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

## Versões

- Python 3.12+ com [uv](https://docs.astral.sh/uv/)
- Node.js 22.22+ e npm (o jsdom usado nos testes exige Node 22)
- PostgreSQL 16
- Django 5.2, Django REST Framework 3.16, React 19, Vite 6

## Executar

### Opção A — Docker Compose

```bash
docker compose up --build
```

Abre http://localhost:5173. Cria as contas de teste com `docker compose exec api python manage.py seed_demo` e entra, por exemplo, como `mariana` (ver "Contas para testar"). O estado técnico está em http://localhost:5173/status e deve mostrar `API: ok · DB: up`.

### Opção B — Local

```bash
cp .env.example .env            # ajustar se necessário; nunca colocar segredos reais no git
set -a && . ./.env && set +a    # exportar as variáveis para o shell
```

Backend (num terminal; precisa de um PostgreSQL acessível em `DATABASE_URL`):

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

Worker (noutro terminal, com as mesmas variáveis):

```bash
cd backend
uv run python manage.py run_worker
```

Frontend (noutro terminal):

```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run python manage.py check && uv run pytest
cd frontend && npm run lint && npx vitest run && npm run build
```

Os testes do backend incluem uma ligação real ao PostgreSQL (`tests/test_health.py::test_db_connection_roundtrip`). O CI (`.github/workflows/ci.yml`) corre tudo isto em cada push e pull request.

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

Regras principais:

- **Um voto por utilizador e pedido.**
- **Estados:** Submitted → Under review → Approved ou Rejected → Planned → In progress → Released. Só o Product Owner muda o estado, um passo de cada vez.
- **Score = votos × impacto ÷ esforço.** Sem estimativa, o pedido fica no fim da tabela.
- **Histórico:** cada alteração do Product Owner cria uma versão. Os clientes veem só as mudanças de estado e de decisão; o impacto, o esforço e os motivos de prioridade ficam para a equipa. Uma escrita feita sobre uma versão antiga é recusada (HTTP 412) em vez de apagar o trabalho de outra pessoa.
- **Isolamento:** cada utilizador só vê os dados do seu workspace.
- **"AI Suggestion":** é uma ordem calculada pela própria aplicação com a regra do score, com a explicação de cada posição. Não liga a nenhum serviço externo de IA.

### Contas para testar

Depois de `migrate`, cria o workspace, as categorias e as contas das personas (não cria pedidos):

```bash
cd backend
uv run python manage.py seed_demo
```

| Utilizador | Papel |
| --- | --- |
| `mariana`, `pedro` | Customer |
| `rui` | Product Owner |
| `catarina` | Developer |
| `duarte` | Project Manager |

A password de desenvolvimento é `featurehub`. Para usar outra, define `SEED_PASSWORD` antes de correr o comando. Com Docker: `docker compose exec api python manage.py seed_demo`.

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

A página de estado técnico está em http://localhost:5173/status.

## O que ainda não está implementado

Os ecrãs Backlog, User Stories, Traceability, Roadmap, Dashboard e Notifications aparecem no menu mas mostram "Em desenvolvimento". Também não existem ainda: menções e notificações, o processamento em segundo plano no worker (outbox), a geração de user stories, as métricas, o registo de utilizadores pela interface e a ligação a um fornecedor de IA. Os avisos `check --deploy` sobre HSTS e redirecionamento HTTPS dependem da implantação (SCRUM-62).

## Ferramenta de IA

Ver [docs/ferramentas-ia.md](docs/ferramentas-ia.md).
