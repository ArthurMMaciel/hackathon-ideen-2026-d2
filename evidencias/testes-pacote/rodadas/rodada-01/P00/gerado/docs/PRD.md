# PRD · Reserva de salas

## Problema
"Vive acontecendo de duas pessoas reservarem a mesma sala no mesmo horário", porque hoje as reservas das salas de São Paulo, Araraquara e do coworking ficam numa planilha compartilhada.

## Usuários
- Colaboradores que reservam salas, procuram sala livre e consultam a agenda do dia.
- Quem administra as salas e acompanha quanto cada sala é usada.

## Objetivo
Reservar salas sem conflito, achar sala livre rápido e medir a ocupação de cada sala. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Sala | nome, local, capacidade, recursos | local: SAO_PAULO, ARARAQUARA, COWORKING; recursos: TV, VIDEOCONFERENCIA, QUADRO |
| Reserva | sala, responsável (nome, e-mail), título, participantes, início, fim, status | status: ATIVA, CANCELADA |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar sala com nome, local, capacidade e recursos. |
| RF-02 | Listar as salas cadastradas e consultar uma sala. |
| RF-03 | Começar com 6 salas cadastradas, duas por local. |
| RF-04 | Criar reserva com sala, responsável (nome e e-mail), título, participantes, início e fim; nasce com status ATIVA. |
| RF-05 | Cancelar reserva, que fica no histórico com status CANCELADA e libera o horário. |
| RF-06 | Consultar salas livres num intervalo, com filtro opcional por local e capacidade mínima. |
| RF-07 | Emitir relatório de taxa de ocupação de cada sala num dia. |
| RF-08 | Listar as reservas de um dia por sala (agenda do dia), incluindo canceladas com seu status. |
| RF-09 | Oferecer API REST para todas as operações. |
| RF-10 | Oferecer tela web simples para reservar e ver a agenda do dia por sala. |
| RF-11 | Guardar os dados em banco local, sem login. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Duas reservas ATIVAS da mesma sala não podem se sobrepor; intervalos [início, fim) e encostar é permitido (10h–11h e 11h–12h coexistem). |
| RN-02 | Duração mínima de 15 minutos e máxima de 4 horas, ambas inclusive (15 min e 4h00 aceitas; 14 min e 4h01 recusadas). |
| RN-03 | Início no passado é recusado: exige início >= agora. |
| RN-04 | Participantes entre 1 e a capacidade da sala, inclusive. |
| RN-05 | Só reserva ATIVA com início > agora pode ser cancelada; reserva já iniciada, passada ou já cancelada é recusada. |
| RN-06 | Reserva CANCELADA não conta para conflito, sala livre nem ocupação. |
| RN-07 | Sala livre no intervalo = nenhuma reserva ATIVA sobreposta; atende local igual ao filtro e capacidade >= capacidade mínima. |
| RN-08 | Ocupação do dia = minutos de reservas ATIVAS dentro de 08:00–18:00 (600 min) / 600 × 100. |
| RN-09 | Fim precisa ser posterior ao início. |
| RN-10 | Sala: nome obrigatório e único (sem diferenciar maiúsculas); capacidade de 1 a 500; recursos sem repetição, podendo ser vazio. |
| RN-11 | Reserva: nome, título e e-mail obrigatórios; e-mail no formato texto@dominio.ext. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito. |
| PR-02 | "Cadastro" de sala cobre criar, listar e consultar; editar e excluir sala ficam fora de escopo. |
| PR-03 | Reserva que começa exatamente agora é aceita (não está no passado). |
| PR-04 | "Dia" do relatório e da agenda é o dia civil no fuso de PR-01; reserva que passa da janela 08:00–18:00 conta só a parte dentro dela. |
| PR-05 | Taxa de ocupação em percentual, arredondada a 1 casa decimal, junto com os minutos ocupados. |
| PR-06 | Salas listadas por local e nome; reservas por início; relatório por local e nome da sala. |
| PR-07 | Como salas não são excluídas nem inativadas, nenhuma reserva muda de status por causa da sala. |
| PR-08 | Reservas podem ser feitas em qualquer horário e dia; a janela 08:00–18:00 vale só para o relatório. |
| PR-09 | Os textos livres têm no máximo 200 caracteres (e-mail até 254). |
| PR-10 | Datas aceitas só entre os anos 2000 e 2100, inclusive. |

## Fora de escopo
- Login, perfis de acesso e autenticação ("não precisa de login por enquanto").
- Editar ou excluir sala; editar reserva (para mudar, cancela-se e cria-se outra).
- Notificações, exportação, reserva recorrente.
- Deploy, integração com sistema real e uso de dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Reservar sala livre dentro das regras | Reserva criada com status `ATIVA` | RF-04 |
| CA-02 | Reservar sala já ocupada em horário que se sobrepõe | Recusa com mensagem de conflito | RN-01 |
| CA-03 | Reservar 11h–12h numa sala com reserva 10h–11h | Reserva criada | RN-01 |
| CA-04 | Reserva com 10 minutos ou com 4h01 | Recusa por duração | RN-02 |
| CA-05 | Reserva com início no passado | Recusa | RN-03 |
| CA-06 | Participantes acima da capacidade | Recusa | RN-04 |
| CA-07 | Cancelar reserva futura | Status `CANCELADA` e horário liberado | RF-05, RN-05, RN-06 |
| CA-08 | Cancelar reserva que já passou | Recusa | RN-05 |
| CA-09 | Consultar salas livres com filtro de local e capacidade | Só salas livres que atendem aos filtros | RF-06, RN-07 |
| CA-10 | Relatório de ocupação de um dia com reservas canceladas | Canceladas não entram no cálculo | RF-07, RN-06, RN-08 |
