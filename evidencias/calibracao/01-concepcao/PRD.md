# PRD · Reserva de salas

## Problema
A empresa tem salas em São Paulo, em Araraquara e num coworking, e "vive acontecendo de duas pessoas reservarem a mesma sala no mesmo horário", porque hoje é tudo numa planilha compartilhada.

## Usuários
- Colaboradores que reservam salas, procuram sala livre e consultam a agenda e o uso das salas, sem login.

## Objetivo
Reservar salas sem conflito, achar sala livre rápido e medir o uso de cada sala. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Sala | nome, local, capacidade, recursos | local: SAO_PAULO, ARARAQUARA, COWORKING; recursos: TV, VIDEOCONFERENCIA, QUADRO |
| Reserva | sala, responsável (nome, e-mail), título, participantes, início, fim, status | status: ATIVA, CANCELADA |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar sala com nome, local, capacidade e recursos. |
| RF-02 | Listar salas e consultar uma sala. |
| RF-03 | Começar com 6 salas cadastradas, duas por local (SAO_PAULO, ARARAQUARA, COWORKING). |
| RF-04 | Criar reserva com sala, responsável (nome e e-mail), título, participantes, início e fim; nasce com status ATIVA. |
| RF-05 | Cancelar reserva, mudando o status para CANCELADA, mantendo-a no histórico e liberando o horário. |
| RF-06 | Consultar salas livres num intervalo, com filtro opcional por local e por capacidade mínima. |
| RF-07 | Emitir relatório da taxa de ocupação de cada sala num dia. |
| RF-08 | Ver a agenda do dia por sala (reservas do dia agrupadas por sala). |
| RF-09 | Oferecer API REST para todas as operações (RF-01 a RF-08). |
| RF-10 | Oferecer tela web simples para reservar e ver a agenda do dia por sala. |
| RF-11 | Guardar os dados em banco local, sem login. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Local é um de SAO_PAULO, ARARAQUARA, COWORKING; recursos são zero ou mais de TV, VIDEOCONFERENCIA, QUADRO, sem repetição. |
| RN-02 | Capacidade é inteiro maior ou igual a 1. |
| RN-03 | Reservas ATIVAS da mesma sala não se sobrepõem: há conflito quando A.início < B.fim e B.início < A.fim. Encostar (fim de uma = início da outra) é permitido. |
| RN-04 | Duração mínima de 15 minutos e máxima de 4 horas, ambas inclusive (14 min e 4h01 são recusadas); fim sempre depois do início. |
| RN-05 | Início antes do instante atual é recusado. |
| RN-06 | Participantes entre 1 e a capacidade da sala, inclusive. |
| RN-07 | Só reserva ATIVA com início depois do instante atual pode ser cancelada. |
| RN-08 | Reserva CANCELADA não conta para conflito, sala livre, agenda nem ocupação. |
| RN-09 | Sala livre no intervalo: nenhuma reserva ATIVA sobreposta (RN-03); filtro de local por igualdade e de capacidade por capacidade >= mínimo. |
| RN-10 | Ocupação = minutos de reservas ATIVAS dentro de [08:00, 18:00) do dia ÷ 600 × 100; a parte fora da janela não conta. |
| RN-11 | Nome da sala, título e nome do responsável não podem ser vazios; e-mail precisa ter formato válido. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo para "agora", "dia" e a janela 8h–18h; datas e horas sempre informadas com fuso explícito; sem fuso é recusado. |
| PR-02 | "Cadastro" de sala cobre criar, listar e consultar; editar e excluir sala ficam fora. |
| PR-03 | Nome de sala é único (comparação exata); repetido é recusado como conflito. |
| PR-04 | Início igual ao instante atual é aceito; "passado" é início < agora. |
| PR-05 | "Reserva futura" é a que ainda não começou; reserva em andamento ou já CANCELADA não pode ser cancelada. |
| PR-06 | Taxa de ocupação em percentual com uma casa decimal; o relatório lista todas as salas, inclusive com 0%. |
| PR-07 | Listagens ordenadas: salas por local e nome; reservas por início. |
| PR-08 | Reserva não é editada; para mudar, cancela-se e cria-se outra. |
| PR-09 | Reservas podem ser feitas em qualquer horário; a janela 8h–18h vale só para o relatório. Precisão de minuto. |
| PR-10 | O mesmo responsável pode ter reservas simultâneas em salas diferentes. |
| PR-11 | As 6 salas iniciais têm nomes, capacidades e recursos fictícios; a carga só ocorre com base vazia. |
| PR-12 | Consulta de salas livres exige intervalo com fim depois do início; não aplica os limites de duração da RN-04. |

## Fora de escopo
- Login, perfis de acesso e controle de permissão (o pedido diz "não precisa de login por enquanto").
- Edição e exclusão de salas; edição de reserva; reservas recorrentes; notificações; exportação.
- Migração da planilha atual, integração com sistema real, deploy e uso de dados reais.

## Critérios de aceite
| Código | Cenário | Verifica |
|---|---|---|
| CA-01 | Reservar sala livre dentro das regras → reserva criada com status ATIVA | RF-04, RN-03, RN-04, RN-05, RN-06 |
| CA-02 | Reservar sala já ocupada em horário que se sobrepõe → recusa com mensagem de conflito | RF-04, RN-03 |
| CA-03 | Reservar 11h–12h numa sala com reserva 10h–11h → reserva criada | RF-04, RN-03 |
| CA-04 | Reserva com 10 minutos ou com 4h01 → recusa por duração | RN-04 |
| CA-05 | Reserva com início no passado → recusa | RN-05, PR-04 |
| CA-06 | Participantes acima da capacidade → recusa | RN-06 |
| CA-07 | Cancelar reserva futura → status CANCELADA e horário liberado | RF-05, RN-07, RN-08 |
| CA-08 | Cancelar reserva que já passou → recusa | RN-07, PR-05 |
| CA-09 | Consultar salas livres com filtro de local e capacidade → só salas livres que atendem aos filtros | RF-06, RN-09 |
| CA-10 | Relatório de ocupação de um dia com reservas canceladas → canceladas não entram no cálculo | RF-07, RN-08, RN-10 |
