# PRD · Férias da equipe

## Problema
"Os pedidos de férias chegam por mensagem e já aconteceu de metade do time sair junto." Falta um lugar único para pedir, aprovar sem esvaziar uma equipe e ver quem está de férias.

## Usuários
- Colaborador: pede e cancela as próprias férias e consulta o saldo.
- Gestor: aprova ou reprova pedidos e consulta o calendário do mês.

## Objetivo
Registrar pedidos de férias e aprová-los sem que mais de uma pessoa da mesma equipe fique fora no mesmo dia. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Colaborador | nome, e-mail, equipe, saldo de dias | DADOS, PRODUTO, SUPORTE |
| Solicitação | colaborador, data de início, data de fim, quantidade de dias, situação | SOLICITADA, APROVADA, REPROVADA, CANCELADA |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar colaborador com nome, e-mail, equipe e saldo de dias de férias (30 por padrão). |
| RF-02 | Listar e consultar colaboradores com saldo e saldo disponível ("Saldo de cada colaborador"). |
| RF-03 | Carregar 9 colaboradores ao iniciar com banco vazio, 3 por equipe, saldo 30. |
| RF-04 | Solicitar férias informando colaborador, data de início e data de fim; nasce `SOLICITADA`. |
| RF-05 | Listar e consultar solicitações (necessário para a tela aprovar, reprovar e cancelar). |
| RF-06 | Aprovar solicitação. |
| RF-07 | Reprovar solicitação. |
| RF-08 | Cancelar solicitação. |
| RF-09 | Consultar o calendário de um mês: para cada dia, quem está com férias aprovadas, por equipe. |
| RF-10 | Oferecer API REST para todas as operações. |
| RF-11 | Oferecer tela web simples para solicitar, aprovar, reprovar e ver o calendário do mês. |
| RF-12 | Guardar os dados em banco local, sem login. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Quantidade de dias = dias corridos de início a fim, contando os dois (fim − início + 1); fim antes do início é recusado. |
| RN-02 | Período mínimo 5 e máximo 30 dias, inclusive: 4 e 31 são recusados. |
| RN-03 | Início ≥ hoje + 30 dias: 30 dias de antecedência é aceito, 29 é recusado. |
| RN-04 | Dias pedidos ≤ saldo disponível; saldo disponível = saldo − dias das solicitações `SOLICITADA` (os dias `APROVADA` já saíram do saldo, ver PR-04). |
| RN-05 | O colaborador não pode ter duas solicitações `SOLICITADA` ou `APROVADA` com pelo menos um dia em comum. |
| RN-06 | Só `SOLICITADA` pode ser aprovada ou reprovada. |
| RN-07 | No máximo 1 pessoa por equipe com `APROVADA` em um mesmo dia; aprovação que quebra isso é recusada. |
| RN-08 | Ao aprovar, a quantidade de dias sai do saldo do colaborador. |
| RN-09 | Só `SOLICITADA` ou `APROVADA` pode ser cancelada, e só até o dia anterior ao início (hoje ≤ início − 1). |
| RN-10 | Ao cancelar uma `APROVADA`, os dias voltam para o saldo. |
| RN-11 | Saldo inicial entre 0 e 365 dias, inteiro; e-mail válido e único; equipe só entre os valores fixos. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito; "hoje" é a data atual nesse fuso. |
| PR-02 | Datas de férias são dias de calendário sem horário; o período conta o primeiro e o último dia; dias seguidos (fim + 1 = início) não têm dia em comum. |
| PR-03 | "Cadastro" cobre criar, listar e consultar colaboradores; editar e excluir ficam fora. |
| PR-04 | O pedido diz "saldo menos os dias SOLICITADA ou APROVADA" e também "ao aprovar, os dias saem do saldo"; para não descontar duas vezes, o saldo guardado já exclui os aprovados e o disponível desconta só os pendentes. |
| PR-05 | Pedidos `SOLICITADA` de pessoas da mesma equipe podem se sobrepor; o limite por equipe só é conferido na aprovação. |
| PR-06 | Reprovar não pede motivo e não mexe no saldo; reprovada e cancelada são finais. |
| PR-07 | Ninguém é identificado (sem login): qualquer pessoa da tela pode aprovar, reprovar ou cancelar. |
| PR-08 | Mês do calendário vai de dia 1 ao último dia do mês; cada dia lista as equipes DADOS, PRODUTO e SUPORTE. |
| PR-09 | Listagens: colaboradores por equipe e nome; solicitações por início e depois por código, mais antigas primeiro. |
| PR-10 | Quantidade de dias e saldo em dias inteiros, sem arredondamento. |
| PR-11 | E-mail único sem diferenciar maiúsculas; nomes podem repetir. |

## Fora de escopo
- Login, perfis de acesso e identificação de quem aprova ("Não precisa de login").
- Editar ou excluir colaborador; editar solicitação (cancela-se e pede-se outra).
- Notificações, feriados, dias úteis, recarga anual de saldo.
- Deploy, integração com sistema real e dados reais.

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
| CA-08 | Aprovar pessoa da mesma equipe com férias começando no dia seguinte ao fim das férias de outra | Aprovada | RN-07, PR-02 |
| CA-09 | Cancelar solicitação aprovada antes do início | `CANCELADA` e saldo devolvido | RF-08, RN-09, RN-10 |
| CA-10 | Calendário do mês com solicitações `SOLICITADA` e `REPROVADA` | Só as aprovadas aparecem | RF-09, RF-07 |
