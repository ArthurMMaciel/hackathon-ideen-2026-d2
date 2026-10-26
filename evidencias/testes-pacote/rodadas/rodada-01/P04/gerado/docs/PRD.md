# PRD · Férias da equipe

## Problema
"Os pedidos de férias chegam por mensagem e já aconteceu de metade do time sair junto." Falta um lugar único para pedir, aprovar e enxergar quem está fora.

## Usuários
- Colaborador: pede e cancela férias, consulta saldo.
- Gestor: aprova ou reprova pedidos e consulta o calendário do mês.

## Objetivo
Pedir e aprovar férias sem deixar mais de uma pessoa da mesma equipe fora no mesmo dia. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Colaborador | nome, e-mail, equipe, saldo de dias | DADOS, PRODUTO, SUPORTE |
| Solicitação | colaborador, data de início, data de fim, dias, situação, data do pedido | SOLICITADA, APROVADA, REPROVADA, CANCELADA |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar colaborador com nome, e-mail, equipe e saldo de dias (30 se não informado). |
| RF-02 | Listar e consultar colaboradores, com saldo e saldo disponível de cada um. |
| RF-03 | Carregar ao iniciar 9 colaboradores fictícios, 3 por equipe, com saldo 30. |
| RF-04 | Solicitar férias informando colaborador, data de início e data de fim; nasce `SOLICITADA`. |
| RF-05 | Listar solicitações, com filtro opcional por situação e por colaborador. |
| RF-06 | Aprovar solicitação. |
| RF-07 | Reprovar solicitação. |
| RF-08 | Cancelar solicitação. |
| RF-09 | Consultar o calendário de um mês: para cada dia, quem está de férias aprovadas, por equipe. |
| RF-10 | Oferecer API REST para todas as operações. |
| RF-11 | Oferecer tela web simples para solicitar, aprovar, reprovar e ver o calendário do mês. |
| RF-12 | Guardar os dados em banco local, sem login. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Dias da solicitação = dias corridos de início a fim, contando os dois (fim − início + 1); fim antes do início é recusado. |
| RN-02 | Período mínimo de 5 e máximo de 30 dias, inclusive (4 e 31 recusados). |
| RN-03 | Início com pelo menos 30 dias de antecedência da data do pedido, inclusive (início ≥ hoje + 30). |
| RN-04 | Dias da solicitação ≤ saldo disponível = saldo inicial − dias `SOLICITADA` − dias `APROVADA` (igual a saldo atual − dias `SOLICITADA`). |
| RN-05 | O colaborador não pode ter duas solicitações `SOLICITADA`/`APROVADA` com pelo menos um dia em comum. |
| RN-06 | Só `SOLICITADA` pode ser aprovada ou reprovada. |
| RN-07 | No máximo 1 pessoa por equipe com férias `APROVADA` em um mesmo dia; aprovação que quebre isso é recusada. Terminar num dia e outro começar no dia seguinte não é conflito. |
| RN-08 | Ao aprovar, os dias da solicitação saem do saldo do colaborador. |
| RN-09 | `SOLICITADA` ou `APROVADA` pode ser cancelada até o dia anterior ao início, inclusive (hoje < início). |
| RN-10 | Ao cancelar uma `APROVADA`, os dias voltam ao saldo. |
| RN-11 | Saldo informado no cadastro é inteiro de 0 a 365. |
| RN-12 | E-mail único entre colaboradores e em formato válido; nome não vazio, até 120 caracteres. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito; "hoje" é a data corrente nesse fuso. |
| PR-02 | Férias são dias inteiros: datas sem hora, período fechado (início e fim incluídos). |
| PR-03 | Cadastro cobre criar, listar e consultar; editar e excluir colaborador ficam fora. |
| PR-04 | O saldo exibido é o atual (já descontadas as aprovadas); o disponível desconta também as pendentes. |
| PR-05 | Aprovar e reprovar não exigem data mínima; cancelar segue RN-09. |
| PR-06 | Calendário mostra só dias do mês pedido; quem não tem férias aprovadas não aparece. |
| PR-07 | Listagens ordenadas: colaboradores por equipe e nome; solicitações por início e id. |
| PR-08 | Reprovar e cancelar só mudam a situação; nada é apagado. |
| PR-09 | Não há perfis: qualquer pessoa com acesso à tela age como colaborador ou gestor. |

## Fora de escopo
- Login, perfis e permissões (o pedido dispensa login).
- Editar ou excluir colaboradores; feriados e dias úteis.
- Notificações, exportação, deploy, integração com sistema real e dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Solicitar 10 dias com 40 dias de antecedência | Solicitação `SOLICITADA` | RF-04, RN-01, RN-02, RN-03 |
| CA-02 | Solicitar 4 dias | Recusa | RN-02 |
| CA-03 | Solicitar com início em 29 dias | Recusa por antecedência | RN-03 |
| CA-04 | Solicitar mais dias que o saldo disponível | Recusa | RN-04 |
| CA-05 | Aprovar solicitação válida | `APROVADA` e saldo reduzido | RF-06, RN-06, RN-08 |
| CA-06 | Aprovar segunda pessoa da mesma equipe com dias em comum | Recusa | RN-07 |
| CA-07 | Aprovar pessoa de outra equipe no mesmo período | Aprovada | RN-07 |
| CA-08 | Aprovar pessoa da mesma equipe com férias começando no dia seguinte ao fim das férias de outra | Aprovada | RN-07 |
| CA-09 | Cancelar solicitação aprovada antes do início | `CANCELADA` e saldo devolvido | RF-08, RN-09, RN-10 |
| CA-10 | Calendário do mês com solicitações `SOLICITADA` e `REPROVADA` | Só as aprovadas aparecem | RF-09, RF-07 |
