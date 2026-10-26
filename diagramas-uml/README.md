# Diagramas UML — Sistema de Gestão de Funcionalidades

Quatro diagramas de casos de uso UML em **PlantUML**, um por persona, totalizando **22 casos de uso**. Os ficheiros são editáveis e podem ser renderizados com PlantUML.

| Ficheiro | Persona | Casos de uso |
| --- | --- | --- |
| [01-mariana-cliente.puml](01-mariana-cliente.puml) | Mariana Costa (Cliente) | 4 |
| [02-rui-product-owner.puml](02-rui-product-owner.puml) | Rui Almeida (Product Owner) | 6 |
| [03-catarina-programadora.puml](03-catarina-programadora.puml) | Catarina Reis (Programadora) | 6 |
| [04-duarte-gestor-projeto.puml](04-duarte-gestor-projeto.puml) | Duarte Fernandes (Gestor de Projeto) | 6 |

[Quadro FigJam editável](https://www.figma.com/board/wPRLCLv1SkTboJxABkdYJL/Untitled)

## Fonte e modelação

Personas.pdf e Scenarios.pdf da branch main, commit 09bc6c1976e972aa741eb92b6cbbbf1fed75ce79.
RA-03, RA-06, DF-05, DF-06 e critérios de aceitação de CR-03 vêm das necessidades das personas; RA-06 é uma interpretação da centralização do backlog.
As associações ator–caso de uso são simples. Não foram introduzidos include/extend sem suporte. CR-06 generaliza para CR-05.

Pontos a validar: editar pedidos, votação por Mariana, notificações, menções, releases/dependências, sugestões de IA e outras permissões.
Fora do sistema: agendar uma encomenda (exemplo de pedido), desenvolver uma funcionalidade, preparar uma reunião. Product Backlog não é Sprint Backlog.
