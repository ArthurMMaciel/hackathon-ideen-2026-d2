# Pedido de treino · Reserva de salas

> Use este pedido para construir e calibrar o seu pacote de skills. Rode o pacote nele, de ponta a ponta, e guarde as evidências.
> A banca usará um **pedido oculto** do mesmo tamanho e do mesmo tipo de entrega para desempatar os finalistas.

## O pedido, como o cliente escreveu

"A gente tem salas em São Paulo, em Araraquara e num coworking, e vive acontecendo de duas pessoas reservarem a mesma sala no mesmo horário. Hoje é tudo numa planilha compartilhada. Queria um sistema simples: cadastro das salas, reserva sem conflito, um jeito rápido de achar sala livre e saber quanto cada sala é usada. Não precisa de login por enquanto."

## O que o sistema precisa fazer

**Salas**
- Cadastro com nome, local (`SAO_PAULO`, `ARARAQUARA`, `COWORKING`), capacidade e recursos (`TV`, `VIDEOCONFERENCIA`, `QUADRO`).
- O sistema já começa com 6 salas cadastradas, duas por local.

**Reservas**
- Uma reserva tem sala, responsável (nome e e-mail), título, quantidade de participantes, início e fim.
- Duas reservas da mesma sala não podem se sobrepor. Encostar é permitido: 10h–11h e 11h–12h podem coexistir.
- Duração mínima de 15 minutos e máxima de 4 horas.
- Não é possível reservar no passado.
- Participantes não podem passar da capacidade da sala.

**Cancelamento**
- Só reservas futuras podem ser canceladas.
- A reserva cancelada fica no histórico com status `CANCELADA` e libera o horário.

**Consulta**
- Salas livres num intervalo, com filtro opcional por local e capacidade mínima.

**Relatório**
- Taxa de ocupação de cada sala num dia, considerando o horário das 8h às 18h e só reservas ativas.

**Interface**
- API REST para todas as operações.
- Uma tela web simples para reservar e ver a agenda do dia por sala.
- Dados em banco local. Sem login.

## Critérios de aceite

| Código | Cenário | Resultado esperado |
|---|---|---|
| CA-01 | Reservar sala livre dentro das regras | Reserva criada com status `ATIVA` |
| CA-02 | Reservar sala já ocupada em horário que se sobrepõe | Recusa com mensagem de conflito |
| CA-03 | Reservar 11h–12h numa sala com reserva 10h–11h | Reserva criada |
| CA-04 | Reserva com 10 minutos ou com 4h01 | Recusa por duração |
| CA-05 | Reserva com início no passado | Recusa |
| CA-06 | Participantes acima da capacidade | Recusa |
| CA-07 | Cancelar reserva futura | Status `CANCELADA` e horário liberado |
| CA-08 | Cancelar reserva que já passou | Recusa |
| CA-09 | Consultar salas livres com filtro de local e capacidade | Só salas livres que atendem aos filtros |
| CA-10 | Relatório de ocupação de um dia com reservas canceladas | Canceladas não entram no cálculo |
