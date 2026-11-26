# FeatureHub

Plataforma de gestão de pedidos de funcionalidades: submissão, priorização (com sugestões de IA), backlog, roadmap, engenharia de requisitos, colaboração e métricas. Projeto de Engenharia de Software 2026/27.

Arquitetura: **monólito modular** com frontend React, API Django REST Framework, PostgreSQL e um worker da mesma aplicação (ver SCRUM-61).

## Estrutura

| Pasta | Conteúdo |
| --- | --- |
| `backend/` | API Django REST (`featurehub/`) e um app por módulo em `apps/`: `core` (saúde, sessão, worker), `collaboration` (workspaces, papéis, comentários), `requests` (pedidos e versões) e `prioritization` (votos e avaliação) têm código; `backlog`, `roadmap`, `requirements` e `analytics` ainda estão vazios. |
| `frontend/` | Aplicação React + TypeScript (Vite): `src/pages` (ecrãs), `src/layout` (menu e topo), `src/api` (chamadas à API). Em desenvolvimento, `/api` é encaminhado para o Django (mesma origem). |
| `diagramas-uml/` | Diagramas de casos de uso (PlantUML). |
| `docs/` | Planos, evidência e registo da ferramenta de IA. |

## Instalação e execução

A aplicação corre como três processos (API, frontend e, opcionalmente, o worker) ligados a um PostgreSQL. Os passos abaixo têm os comandos para **macOS** e para **Windows**. No Windows usa o **PowerShell**; os comandos não funcionam na Linha de comandos (cmd).

Cola os comandos um de cada vez. No fim, http://localhost:5173 mostra o ecrã de login.

### 1. Instalar as ferramentas

| Ferramenta | Versão | Para que serve |
| --- | --- | --- |
| Git | recente | Obter o código |
| [uv](https://docs.astral.sh/uv/) | 0.5 ou superior | Gere o Python e as dependências do backend. Não é preciso instalar o Python à parte |
| Node.js | **22.22 ou superior** | Frontend. Com o Node 20 os testes do frontend falham |
| PostgreSQL | 16 | Base de dados |

**macOS** (com o [Homebrew](https://brew.sh)):

```bash
brew install git uv node postgresql@16
```

```bash
brew services start postgresql@16
```

**Windows** (PowerShell):

```powershell
winget install Git.Git
```

```powershell
winget install astral-sh.uv
```

```powershell
winget install OpenJS.NodeJS.LTS
```

```powershell
winget install PostgreSQL.PostgreSQL.16
```

O instalador do PostgreSQL pede uma password para o utilizador `postgres`: aponta-a, porque é precisa no passo 3. Mantém a porta 5432. Depois de instalar tudo, fecha e volta a abrir o PowerShell.

Para confirmar, nos dois sistemas:

```bash
git --version
```

```bash
uv --version
```

```bash
node -v
```

O `node -v` tem de mostrar `v22.22` ou superior.

### 2. Obter o código

```bash
git clone https://github.com/tiagobolota011/Engenhariadesoftware.git
```

```bash
cd Engenhariadesoftware
```

Quem já tem o repositório atualiza com `git pull` na branch `main`. No Windows, evita pastas com espaços ou acentos no caminho (por exemplo, usa `C:\dev`).

### 3. Criar a base de dados (só uma vez)

A aplicação usa o utilizador `featurehub`, com a password `featurehub`, e uma base de dados com o mesmo nome. São credenciais só para desenvolvimento.

**macOS:**

```bash
"$(brew --prefix postgresql@16)/bin/psql" postgres -c "CREATE ROLE featurehub LOGIN PASSWORD 'featurehub' CREATEDB;"
```

```bash
"$(brew --prefix postgresql@16)/bin/psql" postgres -c "CREATE DATABASE featurehub OWNER featurehub;"
```

**Windows** (pede a password do utilizador `postgres`, definida no instalador):

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -c "CREATE ROLE featurehub LOGIN PASSWORD 'featurehub' CREATEDB;"
```

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -c "CREATE DATABASE featurehub OWNER featurehub;"
```

Cada comando responde `CREATE ROLE` e `CREATE DATABASE`. Se disser que já existe, segue em frente.

### 4. Criar o ficheiro de configuração (só uma vez)

Na pasta `Engenhariadesoftware`:

**macOS:**

```bash
cp .env.example .env
```

**Windows:**

```powershell
Copy-Item .env.example .env
```

O `.env` fica só no teu computador e não vai para o Git. Nunca ponhas lá segredos reais.

### 5. Carregar a configuração no terminal

A API e o worker leem a configuração de variáveis de ambiente. **Cada terminal novo** que vá correr a API, o worker ou os testes do backend precisa deste comando, corrido na pasta `Engenhariadesoftware`:

**macOS:**

```bash
set -a && . ./.env && set +a
```

**Windows:**

```powershell
Get-Content .env | Where-Object { $_ -match '^[A-Z_]+=' } | ForEach-Object { $k, $v = $_ -split '=', 2; Set-Item "env:$k" $v }
```

### 6. Arrancar a API (terminal 1)

Com a configuração do passo 5 carregada, os comandos são iguais nos dois sistemas:

```bash
cd backend
```

```bash
uv sync
```

```bash
uv run python manage.py migrate
```

```bash
uv run python manage.py seed_demo
```

```bash
uv run python manage.py runserver
```

Na primeira vez, o `uv sync` descarrega o Python e as dependências (1 a 2 minutos). O `migrate` cria as tabelas e o `seed_demo` cria as contas de teste; os dois podem ser repetidos sem problema, e convém correr o `migrate` depois de cada `git pull`. A API fica em http://localhost:8000.

### 7. Arrancar o frontend (terminal 2)

Este terminal não precisa do passo 5. Os comandos são iguais nos dois sistemas:

```bash
cd frontend
```

```bash
npm install
```

```bash
npm run dev
```

Quando aparecer `Local: http://localhost:5173/`, abre esse endereço no browser.

### 8. Entrar

Usa uma das contas criadas pelo `seed_demo`. A password de todas é `featurehub`.

| Utilizador | Papel | O que consegue fazer |
| --- | --- | --- |
| `mariana`, `pedro` | Customer | Submeter pedidos, votar, comentar, ver My Requests |
| `rui` | Product Owner | Tudo o anterior, mais avaliar, mudar o estado, marcar a decisão e priorizar |
| `catarina` | Developer | Ver pedidos e a avaliação, votar e comentar |
| `duarte` | Project Manager | Ver pedidos e a avaliação, votar e comentar |

Para testar com duas contas ao mesmo tempo no mesmo computador, usa uma janela normal e uma janela privada do browser. O estado técnico da API e da base de dados está em http://localhost:5173/status e deve mostrar `API: ok · DB: up`.

### 9. Worker (opcional, terminal 3)

O fluxo atual não depende do worker. Para o ver a correr, carrega a configuração (passo 5) e:

```bash
cd backend
```

```bash
uv run python manage.py run_worker
```

A cada 10 segundos escreve `worker heartbeat db=up`.

### Parar e voltar a arrancar

Para parar um processo, carrega em `Ctrl+C` no terminal dele. Nas vezes seguintes bastam os passos 5 a 7, sem o `uv sync`, o `seed_demo` e o `npm install`, a não ser que o `git pull` tenha trazido dependências novas.

### Alternativa: Docker Desktop

Com o [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado, um comando substitui os passos 1 e 3 a 7, em macOS e em Windows:

```bash
docker compose up --build
```

Noutro terminal, cria as contas de teste:

```bash
docker compose exec api python manage.py seed_demo
```

Este caminho ainda não foi testado num computador com Docker. Se o `--build` falhar, usa a instalação local. A porta 5432 tem de estar livre: se também tens o PostgreSQL instalado, para-o primeiro.

### Problemas comuns

| Erro ou sintoma | Causa | Solução |
| --- | --- | --- |
| `ImproperlyConfigured: DATABASE_URL is required` | A configuração não foi carregada neste terminal | Corre o comando do passo 5 neste terminal |
| `password authentication failed for user "featurehub"` | O utilizador da base de dados não existe ou tem outra password | Repete o passo 3 |
| `connection refused` ao arrancar a API | O PostgreSQL está parado | macOS: `brew services start postgresql@16`. Windows, como administrador: `Start-Service postgresql-x64-16` |
| O login responde "Invalid username or password." | As contas ainda não foram criadas | `uv run python manage.py seed_demo` (passo 6) |
| A página mostra erros ao carregar dados depois de um `git pull` | Faltam migrações novas | `uv run python manage.py migrate` |
| `npx vitest run` falha logo ao arrancar | O Node é anterior ao 22.22 | `node -v`; instala a versão LTS mais recente |
| Windows: `running scripts is disabled on this system` | O PowerShell bloqueia scripts | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Windows: `uv`, `node` ou `git` não é reconhecido | O PATH ainda não foi atualizado | Fecha e volta a abrir o PowerShell |
| Windows: `psql.exe` não encontrado | Outra versão ou pasta de instalação | Vê a pasta em `C:\Program Files\PostgreSQL\` e ajusta o número |
| macOS: `zsh: command not found: #` | O comando foi colado com um comentário | Cola só o comando, sem o texto a seguir a `#` |
| `Port 5173 is in use` ou `8000 already in use` | Ficou outro processo aberto | Fecha os terminais antigos |

## Testes

Backend, num terminal com a configuração do passo 5 carregada e o PostgreSQL ligado:

```bash
cd backend
```

```bash
uv run ruff check .
```

```bash
uv run ruff format --check .
```

```bash
uv run python manage.py check
```

```bash
uv run pytest
```

Frontend:

```bash
cd frontend
```

```bash
npm run lint
```

```bash
npx vitest run
```

```bash
npm run build
```

Os testes do backend incluem uma ligação real ao PostgreSQL. O CI (`.github/workflows/ci.yml`) corre estes mesmos comandos em cada push para a `main` e em cada pull request.

## O que já funciona (Sprint 4)

O fluxo principal dos pedidos, com base de dados, API e testes:

| Ecrã | Wireframe | Quem usa |
| --- | --- | --- |
| Login | — | todos |
| Feature Requests: lista, pesquisa, filtros e voto | WF-01 | todos |
| Submit a feature request, com pedidos semelhantes | WF-02 | todos |
| Request detail: estados, discussão, decisão, avaliação e histórico de versões | WF-03 | todos; a avaliação só o Product Owner altera, e os clientes não a veem |
| My Requests e Public Roadmap | WF-04 | todos |
| Prioritization: score, ordem manual com motivo e sugestão calculada | WF-05 | só o Product Owner |
| Notifications e contador no sino do topo; menções `@username` na discussão (Sprint 5, SCRUM-87) | — | todos |

Regras principais:

- **Um voto por utilizador e pedido.**
- **Estados:** Submitted → Under review → Approved ou Rejected → Planned → In progress → Released. Só o Product Owner muda o estado, um passo de cada vez.
- **Score = votos × impacto ÷ esforço.** Sem estimativa, o pedido fica no fim da tabela.
- **Histórico:** cada alteração do Product Owner cria uma versão. Os clientes veem só as mudanças de estado e de decisão; o impacto, o esforço e os motivos de prioridade ficam para a equipa. Uma escrita feita sobre uma versão antiga é recusada (HTTP 412) em vez de apagar o trabalho de outra pessoa.
- **Isolamento:** cada utilizador só vê os dados do seu workspace.
- **Menções e notificações (Sprint 5):** escrever `@username` num comentário notifica esse membro do workspace, com ligação direta ao pedido; nomes desconhecidos, de outro workspace ou do próprio autor são ignorados. O autor de um pedido é notificado quando o Product Owner muda o estado ou regista uma decisão. Ninguém é notificado das suas próprias ações. Evidência em `docs/evidencia/sprint5`.
- **"AI Suggestion":** é uma ordem calculada pela própria aplicação com a regra do score, com a explicação de cada posição. Não liga a nenhum serviço externo de IA.

### API

Todas as rotas ficam em `/api/`. Tirando a de saúde, a do token CSRF e o login, exigem sessão iniciada.

| Rota | O que faz |
| --- | --- |
| `GET /api/health/` | Estado da API e da base de dados: 200 `{"status": "ok", "db": "up"}` ou 503 `{"status": "degraded", "db": "down"}` |
| `GET /api/auth/csrf/`, `POST /api/auth/login/`, `POST /api/auth/logout/`, `GET /api/auth/me/` | Sessão por cookie, com CSRF |
| `GET /api/categories/` | Categorias do workspace |
| `GET /api/requests/` | Lista paginada; filtros `search`, `status`, `category`, `date` (`7d`, `30d`, `90d`) e `mine=1` |
| `POST /api/requests/` | Submete um pedido |
| `GET /api/requests/similar/?q=&tags=` | Pedidos parecidos com um título |
| `GET /api/requests/{id}/` | Detalhe, com discussão e histórico |
| `POST` / `DELETE /api/requests/{id}/vote/` | Vota ou retira o voto |
| `POST /api/requests/{id}/comments/` | Comenta |
| `POST` / `DELETE /api/requests/{id}/comments/{cid}/decision/` | O Product Owner marca ou retira a decisão; há uma por pedido, e marcar outro comentário move-a |
| `PATCH /api/requests/{id}/assessment/` | O Product Owner define impacto, esforço e estado; leva a `version` que viu |
| `GET /api/prioritization/`, `POST /api/prioritization/reorder/` | Tabela de priorização e ordem manual: coloca um pedido antes de outro (`before`), com motivo (Product Owner) |
| `GET /api/prioritization/suggestion/`, `POST /api/prioritization/suggestion/accept/` | Sugestão calculada (Product Owner) |
| `GET /api/roadmap/public/` | Roadmap público: só título e categoria |
| `GET /api/members/` | Membros do workspace (para sugerir menções) |
| `GET /api/notifications/` | As 50 notificações mais recentes e o número de não lidas; `unread=1` mostra só as não lidas |
| `GET /api/notifications/unread/` | Número de notificações por ler |
| `POST /api/notifications/{id}/read/`, `POST /api/notifications/read-all/` | Marca uma ou todas como lidas |

A página de estado técnico está em http://localhost:5173/status.

## O que ainda não está implementado

Os ecrãs Backlog, User Stories, Traceability, Roadmap e Dashboard aparecem no menu mas mostram "Em desenvolvimento" (tarefas do Sprint 5: SCRUM-89, SCRUM-91, SCRUM-93 e SCRUM-95). Também não existem ainda: notificações por email (as notificações são só na aplicação), o processamento em segundo plano no worker (outbox), a geração de user stories, as métricas, o registo de utilizadores pela interface e a ligação a um fornecedor de IA. Os avisos `check --deploy` sobre HSTS e redirecionamento HTTPS dependem da implantação (SCRUM-62).

## Ferramenta de IA

Ver [docs/ferramentas-ia.md](docs/ferramentas-ia.md).
