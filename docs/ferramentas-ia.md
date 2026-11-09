# Ferramentas de IA de apoio à programação

| Ferramenta | Usada por | Finalidade |
| --- | --- | --- |
| Claude Code (Anthropic) | João Estêvão | Gerar a estrutura da base executável (SCRUM-68): projeto Django e apps por módulo, endpoint de saúde, worker, frontend React, testes, pipeline de CI, docker-compose e este README. |

## Como foi usada

- O trabalho seguiu um plano escrito e aprovado antes de qualquer código (`docs/superpowers/plans/2026-11-09-scrum-68-base-executavel.md`), alinhado com a arquitetura da SCRUM-61.
- Cada comportamento foi primeiro descrito num teste que falhava e só depois implementado.
- A verificação foi feita com comandos reais: testes contra um PostgreSQL 16 local, lint, build e screenshots do frontend ligado à API (`docs/evidencia/`).

## Revisão humana

- Nenhum código gerado entra em `main` sem um pull request revisto e aprovado por outro membro da equipa.
- O autor do PR confirma que correu localmente os testes, e o CI tem de estar verde.
- As decisões em que a IA se afastou do plano estão listadas na descrição do PR, para o revisor as validar.
