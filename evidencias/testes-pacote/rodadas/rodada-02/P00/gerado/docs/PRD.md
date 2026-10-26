# PRD · Reserva de salas

## Problema
A empresa tem salas em São Paulo, em Araraquara e num coworking e "vive acontecendo de duas pessoas reservarem a mesma sala no mesmo horário", porque hoje é tudo numa planilha compartilhada.

## Usuários
- Colaboradores que reservam salas, procuram sala livre e consultam a agenda do dia, sem login.
- Quem administra as salas e acompanha quanto cada sala é usada.

## Objetivo
Reservar salas sem conflito, achar sala livre rápido e medir a ocupação de cada sala. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Sala | nome, local, capacidade, recursos | local: SAO_PAULO, ARARAQUARA, COWORKING; recursos: TV, VIDEOCONFERENCIA, QUADRO |
| Reserva | sala, responsável (nome e e-mail), título, quantidade de participantes, início, fim, status | status: ATIVA, CANCELADA |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar sala com nome, local, capacidade e recursos. |
| RF-02 | Listar as salas cadastradas e consultar uma sala (a tela precisa delas para reservar e montar a agenda por sala). |
| RF-03 | Começar com 6 salas cadastradas, duas por local. |
| RF-04 | Criar reserva com sala, responsável (nome e e-mail), título, participantes, início e fim; nasce com status ATIVA. |
| RF-05 | Listar as reservas de um dia, por sala, com status (a "agenda do dia por sala" da tela). |
| RF-06 | Cancelar reserva, mantendo-a no histórico com status CANCELADA. |
| RF-07 | Consultar salas livres num intervalo, com filtro opcional por local e por capacidade mínima. |
| RF-08 | Emitir relatório da taxa de ocupação de cada sala num dia. |
| RF-09 | Oferecer API REST para todas as operações. |
| RF-10 | Oferecer tela web simples para reservar e ver a agenda do dia por sala. |
| RF-11 | Guardar os dados em banco local, sem login. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Duas reservas ATIVAS da mesma sala não se sobrepõem. Intervalo semiaberto [início, fim): encostar (10h–11h e 11h–12h) é permitido. |
| RN-02 | Duração mínima de 15 minutos e máxima de 4 horas (240 minutos), ambas inclusive; fim antes ou igual ao início é recusado. |
| RN-03 | Não é possível reservar no passado: início anterior ao momento atual é recusado; início igual ao momento atual é aceito. |
| RN-04 | Participantes entre 1 e a capacidade da sala, inclusive. |
| RN-05 | Só reserva ATIVA e futura (início posterior ao momento atual) pode ser cancelada. |
| RN-06 | Reserva cancelada não é apagada, muda para CANCELADA e deixa de contar para conflito, salas livres e ocupação. |
| RN-07 | Sala livre no intervalo: nenhuma reserva ATIVA dela se sobrepõe ao intervalo; com local, só esse local; com capacidade mínima, capacidade maior ou igual a ela. O intervalo exige fim posterior ao início. |
| RN-08 | Taxa de ocupação de uma sala no dia = minutos de reservas ATIVAS dentro da janela [08:00, 18:00) desse dia ÷ 600 minutos × 100. |
| RN-09 | Sala: capacidade entre 1 e 1000, inclusive; local e recursos só com os valores fixos; recursos sem repetição, lista pode ser vazia. |
| RN-10 | Nome de sala único dentro do mesmo local, sem diferenciar maiúsculas de minúsculas. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito. |
| PR-02 | "Cadastro" de sala cobre criar, listar e consultar; editar e excluir sala ficam fora (não citados). |
| PR-03 | Nome, título e nome do responsável: texto não vazio de até 200 caracteres; e-mail com formato simples (algo@dominio.ext). |
| PR-04 | Reserva em andamento (início já passou, fim ainda não) não é futura: não pode ser cancelada. Cancelar reserva já CANCELADA é recusado. |
| PR-05 | Reservas podem ser feitas em qualquer horário (inclusive fora de 8h–18h e atravessando a meia-noite); a janela 8h–18h vale só para o relatório. |
| PR-06 | "Dia" é o dia de calendário no fuso padrão. A agenda do dia mostra as reservas (ATIVAS e CANCELADAS) que tocam esse dia. |
| PR-07 | No relatório, só a parte da reserva dentro de 08:00–18:00 conta; taxa em percentual com 1 casa decimal (arredondamento meio para cima); também informa os minutos ocupados. |
| PR-08 | O relatório aceita qualquer dia, passado ou futuro, e lista todas as salas, inclusive as de taxa 0. |
| PR-09 | A consulta de salas livres aceita qualquer intervalo com fim posterior ao início, sem os limites de duração e de passado da reserva. |
| PR-10 | Ordenação: salas por local e nome; reservas por início e depois por sala; relatório por local e nome da sala. |
| PR-11 | O pedido não traz contradição; a única interação entre regras é cancelamento × conflito, resolvida pela RN-06 (cancelada libera o horário). |

## Fora de escopo
- Login, perfis e controle de acesso ("não precisa de login por enquanto").
- Editar ou excluir sala; editar reserva (alterar exige cancelar e reservar de novo).
- Notificações, reservas recorrentes, exportação e integração com agenda externa.
- Deploy, integração com sistema real e dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Reservar sala livre dentro das regras | Reserva criada com status `ATIVA` | RF-04 |
| CA-02 | Reservar sala já ocupada em horário que se sobrepõe | Recusa com mensagem de conflito | RF-04, RN-01 |
| CA-03 | Reservar 11h–12h numa sala com reserva 10h–11h | Reserva criada | RF-04, RN-01 |
| CA-04 | Reserva com 10 minutos ou com 4h01 | Recusa por duração | RN-02 |
| CA-05 | Reserva com início no passado | Recusa | RN-03 |
| CA-06 | Participantes acima da capacidade | Recusa | RN-04 |
| CA-07 | Cancelar reserva futura | Status `CANCELADA` e horário liberado | RF-06, RN-05, RN-06 |
| CA-08 | Cancelar reserva que já passou | Recusa | RN-05 |
| CA-09 | Consultar salas livres com filtro de local e capacidade | Só salas livres que atendem aos filtros | RF-07, RN-07 |
| CA-10 | Relatório de ocupação de um dia com reservas canceladas | Canceladas não entram no cálculo | RF-08, RN-06, RN-08 |
