# FeatureHub

Plataforma de gestão de pedidos de funcionalidades: submissão, priorização (com sugestões de IA), backlog, roadmap, engenharia de requisitos, colaboração e métricas. Projeto de Engenharia de Software 2026/27.

Arquitetura: **monólito modular** com frontend React, API Django REST Framework, PostgreSQL e um worker da mesma aplicação (ver SCRUM-61).

## Estrutura

| Pasta | Conteúdo |
| --- | --- |
| `backend/` | API Django REST (`featurehub/`) e um app por módulo em `apps/` (`core`, `requests`, `prioritization`, `backlog`, `roadmap`, `requirements`, `collaboration`, `analytics`). O worker é o comando `run_worker`. |
| `frontend/` | Aplicação React + TypeScript (Vite). Em desenvolvimento, `/api` é encaminhado para o Django (mesma origem). |
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

Abre http://localhost:5173. A página deve mostrar `API: ok · DB: up`. A API fica em http://localhost:8000/api/health/.

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
cd backend && uv run ruff check . && uv run pytest
cd frontend && npm run lint && npx vitest run && npm run build
```

Os testes do backend incluem uma ligação real ao PostgreSQL (`tests/test_health.py::test_db_connection_roundtrip`). O CI (`.github/workflows/ci.yml`) corre tudo isto em cada push e pull request.

## Endpoint de saúde

`GET /api/health/`

- `200 {"status": "ok", "db": "up"}`
- `503 {"status": "degraded", "db": "down"}` quando a base de dados não responde

## O que esta base ainda não inclui

Esta é a base técnica da SCRUM-68. **Nenhuma história de produto está implementada**: os apps de módulo estão vazios, e não há autenticação de utilizadores, modelos de domínio (SCRUM-65), outbox, notificações nem integração com IA. Os avisos `check --deploy` sobre HSTS e redirecionamento HTTPS dependem da implantação (SCRUM-62).

## Ferramenta de IA

Ver [docs/ferramentas-ia.md](docs/ferramentas-ia.md).
