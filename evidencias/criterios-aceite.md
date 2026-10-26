# Critérios de aceite verificados via HTTP

Executado em 2026-10-26T07:51:14 contra o servidor real (uvicorn).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| CA-01 | Reservar Paulista 08/01 10h-11h, 4 pessoas | HTTP 201, status=ATIVA | HTTP 201, id=1, status=ATIVA | PASSOU |
| CA-02 | Reservar Paulista 10h30-11h30 (sobrepõe 10h-11h) | HTTP 409, erro=CONFLITO_HORARIO, mensagem de conflito | HTTP 409, erro=CONFLITO_HORARIO, mensagem=Conflito de horário: a sala já tem reserva ativa que se sobrepõe a este intervalo. | PASSOU |
| CA-03 | Reservar Paulista 11h-12h com reserva 10h-11h | HTTP 201, status=ATIVA | HTTP 201, id=2, status=ATIVA | PASSOU |
| CA-04 | Reservas de 10 minutos e de 4h01 | HTTP 422, erro=DURACAO_INVALIDA nas duas | 10 min: HTTP 422, erro=DURACAO_INVALIDA; 4h01: HTTP 422, erro=DURACAO_INVALIDA | PASSOU |
| CA-05 | Reservar 07/01 08h-08h45 com relógio em 07/01 09h | HTTP 422, erro=INICIO_NO_PASSADO | HTTP 422, erro=INICIO_NO_PASSADO | PASSOU |
| CA-06 | Reservar Ibirapuera (capacidade 4) com 5 participantes | HTTP 422, erro=CAPACIDADE_EXCEDIDA | HTTP 422, erro=CAPACIDADE_EXCEDIDA | PASSOU |
| CA-07 | Cancelar reserva futura de Ibirapuera 09h-10h e reservar o mesmo horário | HTTP 200, status=CANCELADA; nova reserva HTTP 201 | cancelar: HTTP 200, status=CANCELADA; nova: HTTP 201, status=ATIVA | PASSOU |
| CA-08 | Cancelar às 12h a reserva de 07/01 10h-11h | HTTP 409, erro=RESERVA_NAO_FUTURA | HTTP 409, erro=RESERVA_NAO_FUTURA | PASSOU |
| CA-09 | Salas livres 08/01 10h30-11h30, local SAO_PAULO, capacidade >= 4 | HTTP 200, só Ibirapuera (Paulista ocupada; outros locais fora) | HTTP 200: ['Ibirapuera'] | PASSOU |
| CA-10 | Ocupação de 08/01 com Laranjeira 08h-10h ativa e 10h-12h cancelada | HTTP 200, Laranjeira 120 min, 20.0% (cancelada fora) | HTTP 200, minutos_ocupados=120.0, taxa_ocupacao=20.0 | PASSOU |
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
