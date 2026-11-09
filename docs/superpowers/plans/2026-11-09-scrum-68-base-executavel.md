# SCRUM-68 — Base executável do FeatureHub: plano de implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans. Passos com checkbox (`- [ ]`).

**Objetivo:** criar no repositório da equipa uma base executável mínima (frontend React, API Django REST, worker e PostgreSQL) que cumpra os critérios de aceitação da SCRUM-68, sem implementar histórias de produto.

**Arquitetura:** monólito modular conforme a SCRUM-61:
- **Frontend web** (React + Vite + TypeScript) fala JSON com a **API** (Django REST Framework) pela mesma origem: proxy do Vite em desenvolvimento, `/api` atrás do mesmo host em produção.
- **PostgreSQL** guarda os dados.
- O **worker** é um comando de gestão da mesma aplicação Django (`run_worker`), num processo separado. Nesta base só arranca, verifica a BD e escreve um heartbeat. A outbox, as notificações e a IA ficam para as respetivas histórias.

**Stack:** Python 3.12+, Django 5.1, djangorestframework 3.15, psycopg 3, pytest + pytest-django, ruff; Node 20+, React 18, Vite 5, Vitest, Testing Library, ESLint; PostgreSQL 16; docker-compose; GitHub Actions.

**Spec:** `SCRUM-61 - Arquitetura do FeatureHub.docx` (Santiago Fernandes) e os critérios de aceitação da SCRUM-68 no Jira.

## Restrições globais
- Pastas na raiz do repositório: `backend/`, `frontend/`, ao lado de `diagramas-uml/`. Os ficheiros existentes não são alterados.
- O README tem versões, configuração de exemplo **sem segredos** (`.env.example`) e passos reproduzíveis para correr o frontend, o backend e o worker.
- O frontend comunica com o **endpoint de saúde** do backend. Há um **teste de ligação à persistência** em ambiente de desenvolvimento.
- O pipeline corre build, lint e testes de smoke. A evidência do resultado é anexada no Jira.
- Fica registada a **ferramenta de IA** usada no código (Claude Code), com a finalidade e a regra de revisão humana.
- A estrutura respeita a SCRUM-61: há um app Django por módulo (`requests`, `prioritization`, `backlog`, `roadmap`, `requirements`, `collaboration`, `analytics`) e um app `core` (saúde, worker). Os apps de módulo **ficam vazios** (só `apps.py`), sem declarar histórias como implementadas.
- Configuração alinhada com as decisões transversais da SCRUM-61:
  - `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` e `SESSION_COOKIE_HTTPONLY` ligados fora de `DEBUG`.
  - `CsrfViewMiddleware` ativo.
  - `USE_TZ=True`, `TIME_ZONE="UTC"`.
  - Paginação por omissão no DRF (`PageNumberPagination`, `PAGE_SIZE=25`).
- Nenhum segredo no git: `.env` vai para o `.gitignore`, e `DJANGO_SECRET_KEY` só tem um valor de exemplo no `.env.example`.

## Pontos de revisão
1. Se a BD estiver em baixo, `GET /api/health/` responde **503** `{"status":"degraded","db":"down"}` em vez de erro 500. Teste no Task 2.
2. Se a API estiver inacessível, o frontend mostra "API indisponível" em vez de ficar em branco. Teste no Task 3.
3. Se faltar `DATABASE_URL` ou `DJANGO_SECRET_KEY` com `DEBUG` desligado, o arranque falha com uma mensagem que nomeia a variável. Teste no Task 1.
4. Se a BD estiver em baixo no arranque, o worker não termina: regista o erro e volta a tentar no ciclo seguinte. Teste no Task 4.
5. `/api/health/` não expõe detalhes internos (versões, host da BD). O teste do Task 2 verifica que o corpo tem só as chaves `status` e `db`.

---

### Task 1: Projeto Django, configuração e infraestrutura local

**Ficheiros:**
- Criar: `backend/pyproject.toml` (dependências e configuração de ruff e pytest, com `DJANGO_SETTINGS_MODULE=featurehub.settings`)
- Criar: `backend/manage.py`, `backend/featurehub/{__init__,settings,urls,wsgi}.py`
- Criar: `backend/featurehub/env.py` com `require_env(name: str, environ: Mapping[str,str] = os.environ) -> str`, que lança `ImproperlyConfigured(f"{name} is required")`
- Criar: `backend/apps/{core,requests,prioritization,backlog,roadmap,requirements,collaboration,analytics}/{__init__,apps.py}`. O label do app `requests` é `feature_requests`, para não colidir com a biblioteca `requests`.
- Criar: `docker-compose.yml` com os serviços `db` (postgres:16, healthcheck `pg_isready`), `api` (`manage.py runserver 0.0.0.0:8000`), `worker` (`manage.py run_worker`) e `web` (`npm run dev -- --host`)
- Criar: `.env.example` com `DATABASE_URL=postgres://featurehub:featurehub@localhost:5432/featurehub`, `DJANGO_SECRET_KEY=change-me`, `DJANGO_DEBUG=1`, `WORKER_INTERVAL_SECONDS=10`
- Criar: `.gitignore` (`.env`, `__pycache__/`, `.venv/`, `node_modules/`, `dist/`)
- Testes: `backend/tests/test_settings.py`

**Interfaces produzidas:** `featurehub.env.require_env`, settings com `DATABASES["default"]` lido de `DATABASE_URL` (com `dj-database-url`) e `INSTALLED_APPS` com os 8 apps.

- [ ] **Passo 1: testes que falham primeiro**
  - `test_require_env_missing_names_variable`: `pytest.raises(ImproperlyConfigured, match="DATABASE_URL")` ao chamar `require_env("DATABASE_URL", {})`.
  - `test_require_env_returns_value`: `require_env("X", {"X": "1"}) == "1"`.
  - `test_module_apps_installed`: os 7 labels de módulo e `core` estão em `apps.get_app_configs()`.
- [ ] **Passo 2:** `cd backend && uv run pytest tests/test_settings.py` → FAIL.
- [ ] **Passo 3:** implementar os settings e `env.py`.
- [ ] **Passo 4:** correr os testes → PASS. Correr `uv run ruff check . && uv run python manage.py check --deploy --fail-level ERROR` com as variáveis de produção → sem erros.
- [ ] **Passo 5:** commit `chore(backend): django project skeleton with module apps (SCRUM-68)`.

### Task 2: Endpoint de saúde e teste de persistência

**Ficheiros:**
- Criar: `backend/apps/core/health.py` com `check_db() -> bool` (`connection.ensure_connection()` + `SELECT 1`; devolve False em `OperationalError`/`DatabaseError`)
- Criar: `backend/apps/core/views.py` com `HealthView(APIView)` (`GET`, `permission_classes=[AllowAny]`), que devolve 200 `{"status":"ok","db":"up"}` ou 503 `{"status":"degraded","db":"down"}`
- Modificar: `backend/featurehub/urls.py`: `path("api/health/", HealthView.as_view())`
- Testes: `backend/tests/test_health.py`

**Interfaces produzidas:** `GET /api/health/` com o contrato acima, consumido pelos Tasks 3 e 5 e pelos diagramas da SCRUM-67.

- [ ] **Passo 1: testes que falham primeiro**
  - `test_health_ok` (`@pytest.mark.django_db`): `client.get("/api/health/")` → 200 e `json() == {"status":"ok","db":"up"}`.
  - `test_health_db_down`: com `monkeypatch` de `apps.core.views.check_db` para `lambda: False` → 503 e `json() == {"status":"degraded","db":"down"}`.
  - `test_db_connection_roundtrip` (`@pytest.mark.django_db`): `check_db() is True` contra a BD real (Postgres local ou do CI). É o teste de persistência pedido.
- [ ] **Passo 2:** correr → FAIL.
- [ ] **Passo 3:** implementar.
- [ ] **Passo 4:** correr → PASS.
- [ ] **Passo 5:** commit `feat(core): health endpoint with db check (SCRUM-68)`.

### Task 3: Frontend mínimo ligado à API

**Ficheiros:**
- Criar: `frontend/` com Vite react-ts. `vite.config.ts` tem o proxy `/api` → `http://localhost:8000` (o alvo pode ser alterado com `VITE_API_PROXY` para o docker-compose) e a configuração de teste do Vitest (`environment: "jsdom"`).
- Criar: `frontend/src/api/health.ts` com `type Health = { status: "ok" | "degraded"; db: "up" | "down" }` e `fetchHealth(signal?: AbortSignal): Promise<Health>`. Aceita 200 e 503 (ambos têm corpo válido) e lança exceção nos outros casos ou em erro de rede.
- Criar: `frontend/src/App.tsx` com o título "FeatureHub" e o texto de estado: `API: ok · DB: up`, `API: degraded · DB: down` ou `API indisponível`. Mostra "A verificar…" enquanto carrega.
- Testes: `frontend/src/App.test.tsx`

- [ ] **Passo 1: testes que falham primeiro**
  - `shows ok status`: `fetch` mock com 200 `{"status":"ok","db":"up"}` → `findByText("API: ok · DB: up")`.
  - `shows degraded on 503`: mock 503 `{"status":"degraded","db":"down"}` → `findByText("API: degraded · DB: down")`.
  - `shows unavailable when fetch rejects`: mock rejeitado → `findByText("API indisponível")`.
- [ ] **Passo 2:** `cd frontend && npm test` → FAIL.
- [ ] **Passo 3:** implementar.
- [ ] **Passo 4:** correr → PASS; `npm run lint && npm run build` → OK.
- [ ] **Passo 5:** commit `feat(frontend): health status page wired to api (SCRUM-68)`.

### Task 4: Worker mínimo

**Ficheiros:**
- Criar: `backend/apps/core/worker.py` com `run_once(now: Callable[[], datetime] = timezone.now) -> bool`, que chama `check_db()`, regista `worker heartbeat db=up|down at=<ISO UTC>` no logger `featurehub.worker` e devolve o resultado.
- Criar: `backend/apps/core/management/commands/run_worker.py` com as opções `--once` e `--interval` (por omissão `WORKER_INTERVAL_SECONDS`, 10). O ciclo `while True: run_once(); sleep(interval)` apanha e regista exceções sem terminar.
- Testes: `backend/tests/test_worker.py`

- [ ] **Passo 1: testes que falham primeiro**
  - `test_run_once_db_up` (`django_db`): `run_once()` devolve True e o `caplog` contém `"worker heartbeat db=up"`.
  - `test_run_once_db_down_does_not_raise`: com monkeypatch de `check_db` para False → devolve False e regista `"db=down"`.
  - `test_command_once` (`django_db`): `call_command("run_worker", "--once")` termina sem exceção.
- [ ] **Passo 2:** correr → FAIL.
- [ ] **Passo 3:** implementar.
- [ ] **Passo 4:** correr → PASS.
- [ ] **Passo 5:** commit `feat(core): minimal worker process with heartbeat (SCRUM-68)`.

### Task 5: CI, README, registo de IA e evidência

**Ficheiros:**
- Criar: `.github/workflows/ci.yml` com dois jobs, em push e PR:
  - `backend`: service `postgres:16`, `DATABASE_URL` apontado para ele, `astral-sh/setup-uv`, `uv sync`, `ruff check`, `pytest`, `manage.py check`.
  - `frontend`: `setup-node@v4` (20), `npm ci`, `npm run lint`, `npm test -- --run`, `npm run build`.
- Modificar: o `README.md` da raiz ainda não existe, por isso é criado. Tem a descrição curta do FeatureHub, um link para a SCRUM-61, a estrutura de pastas, as versões (Python 3.12+, Node 20+, Postgres 16) e dois caminhos de execução:
  - (a) `docker compose up`
  - (b) local: `cp .env.example .env`, `uv sync`, `manage.py migrate`, `runserver`, `run_worker`, `npm install && npm run dev`

  Inclui também como correr os testes e uma secção "O que esta base NÃO inclui" (histórias de produto, autenticação de utilizadores, outbox, IA).
- Criar: `docs/ferramentas-ia.md` com a ferramenta (Claude Code), a finalidade (scaffolding, testes, configuração de CI, documentação) e a revisão humana (cada PR revisto e aprovado por outro membro antes do merge; o autor confirma que os testes passam localmente).
- Criar: `docs/evidencia/` com o screenshot `health-ok.png`, e, se possível, `health-degraded.png` com a BD parada.

- [ ] **Passo 1:** verificação ponta a ponta local, com o Postgres 16 nativo (`initdb`/`pg_ctl` em `/tmp`, porque o daemon Docker não está disponível nesta sessão). Correr `migrate`, `runserver`, `run_worker --once` e `npm run dev`. Tirar o screenshot de `http://localhost:5173` com o Playwright e confirmar que mostra `API: ok · DB: up`. Parar o Postgres e confirmar `API: degraded · DB: down`.
- [ ] **Passo 2:** `docker compose config` valida o ficheiro. Não é possível correr `up` aqui, e isso fica dito no README e no Jira.
- [ ] **Passo 3:** commit `ci: backend and frontend pipelines; docs: readme and ai tool log (SCRUM-68)`.
- [ ] **Passo 4 (push):** depende de acesso de escrita. Esta sessão **não consegue fazer push** para `tiagobolota011/engenhariadesoftware` (a app GitHub do Claude não tem acesso). As alternativas são:
  - o Tiago instalar a app do Claude no repositório; ou
  - eu entregar o branch como `git bundle`/patch e tu fazeres o push.

  Depois do push, abrir um PR e esperar que o CI fique verde.

### Task 6: Registo no Jira (só com confirmação tua)
- [ ] Comentário na **SCRUM-68** com:
  - o link do PR e do run verde do CI;
  - os screenshots;
  - um link para `docs/ferramentas-ia.md`;
  - a nota "base alinhada com SCRUM-61 (Django REST + React + PostgreSQL + worker)".
- [ ] Comentário na **SCRUM-16** com o link do repositório e do README.
- [ ] Não mudar o estado para Done, porque falta a revisão e a aprovação do PO.

## Verificação final
- `cd backend && uv run ruff check . && uv run pytest` passa, com 9 testes, incluindo o de persistência contra Postgres real.
- `cd frontend && npm run lint && npm test -- --run && npm run build` passa, com 3 testes.
- No browser: `API: ok · DB: up`, e com a BD parada `API: degraded · DB: down`.
- `run_worker --once` regista um heartbeat.
- O CI fica verde no PR, depois do push.
