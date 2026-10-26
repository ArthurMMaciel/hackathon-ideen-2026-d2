# PRD · Reserva de salas

## Problema
Conflitos de reserva acontecem porque as salas de São Paulo, Araraquara e coworking são controladas numa planilha compartilhada.

## Usuários
- Colaboradores que procuram, reservam e acompanham salas.

## Objetivo
Permitir reservas sem conflito, consulta de disponibilidade e uso diário. Sucesso: dez critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Sala | identificador, nome, local, capacidade, recursos | SAO_PAULO, ARARAQUARA, COWORKING; TV, VIDEOCONFERENCIA, QUADRO |
| Reserva | identificador, sala, responsável nome/e-mail, título, participantes, início, fim, status | ATIVA, CANCELADA |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar e listar salas com nome, local, capacidade e recursos. |
| RF-02 | Iniciar com seis salas fictícias, duas por local. |
| RF-03 | Criar, listar e consultar reservas com sala, responsável, título, participantes, início e fim. |
| RF-04 | Cancelar uma reserva preservando-a no histórico. |
| RF-05 | Consultar salas livres em intervalo com filtros opcionais de local e capacidade mínima. |
| RF-06 | Consultar a taxa de ocupação de cada sala num dia. |
| RF-07 | Disponibilizar API REST para todas as operações. |
| RF-08 | Disponibilizar tela web para reservar e ver agenda do dia por sala. |
| RF-09 | Persistir dados em banco local. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Reserva ATIVA da mesma sala não pode sobrepor outra; intervalos semiabertos permitem encostar. |
| RN-02 | Duração entre 15 e 240 minutos, inclusive; fim posterior ao início. |
| RN-03 | Início da reserva igual ou posterior ao instante atual; passado é recusado. |
| RN-04 | Participantes entre 1 e a capacidade da sala, inclusive. |
| RN-05 | Somente reserva com início estritamente futuro pode ser cancelada; cancelar libera horário e mantém CANCELADA. |
| RN-06 | Ocupação é a soma das interseções de reservas ATIVAS com 08h–18h do dia dividida por 600 minutos, em porcentagem. |
| RN-07 | Capacidade da sala e filtro de capacidade mínima são inteiros positivos; recursos e locais usam os valores fixos. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo; horários sempre com fuso explícito. |
| PR-02 | Cadastro de sala cobre criar e listar; reservas cobrem criar, listar, consultar e cancelar. Não há edição ou exclusão. |
| PR-03 | Identificadores são únicos; nomes de salas podem repetir. Campos de texto são não vazios; e-mail deve ter formato válido. |
| PR-04 | Agenda do dia inclui reservas de qualquer status, ordenadas por início; listagens de salas são por local, nome e identificador. |
| PR-05 | Dia é a data civil no fuso padrão; porcentagem de ocupação tem duas casas decimais e fica entre 0 e 100. |
| PR-06 | Consulta de salas livres exige início anterior ao fim e aceita intervalo passado para consulta histórica. |
| PR-07 | A tela usa os horários locais do navegador e envia horário com fuso explícito. |

## Fora de escopo
- Login, edição/exclusão de salas, edição de reservas, notificações, deploy, integração e dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Reservar sala livre dentro das regras | Reserva criada com status ATIVA | RF-03, RN-01–04 |
| CA-02 | Reservar sala ocupada em horário sobreposto | Recusa com mensagem de conflito | RN-01 |
| CA-03 | Reservar 11h–12h após 10h–11h na mesma sala | Reserva criada | RN-01 |
| CA-04 | Reserva de 10 minutos ou 4h01 | Recusa por duração | RN-02 |
| CA-05 | Reserva com início no passado | Recusa | RN-03 |
| CA-06 | Participantes acima da capacidade | Recusa | RN-04 |
| CA-07 | Cancelar reserva futura | Status CANCELADA e horário liberado | RF-04, RN-05 |
| CA-08 | Cancelar reserva que já passou | Recusa | RN-05 |
| CA-09 | Salas livres com filtro de local e capacidade | Só salas livres que atendem aos filtros | RF-05 |
| CA-10 | Ocupação do dia com reservas canceladas | Canceladas não entram no cálculo | RF-06, RN-06 |
