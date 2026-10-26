# Critérios de aceite verificados via HTTP

Executado em 2026-10-23T17:36:02 contra o servidor real (uvicorn, porta 8765).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
| CA-01 | Reservar sala livre dentro das regras (Paulista 08/01 10h–11h) | 201, status ATIVA | HTTP 201 {'id': 1, 'status': 'ATIVA'} | PASSOU |
| CA-02 | Reservar Paulista 10h30–11h30 sobre reserva 10h–11h | 409 CONFLITO_HORARIO com mensagem de conflito | HTTP 409 {'erro': 'CONFLITO_HORARIO', 'mensagem': 'Conflito de horário: a sala já tem reserva ativa que se sobrepõe a este intervalo.'} | PASSOU |
| CA-03 | Reservar Paulista 11h–12h com reserva 10h–11h existente | 201, status ATIVA | HTTP 201 {'id': 2, 'status': 'ATIVA'} | PASSOU |
| CA-04 | Reserva com 10 minutos e com 4h01 | 422 DURACAO_INVALIDA nas duas | 10 min: HTTP 422 {'erro': 'DURACAO_INVALIDA', 'mensagem': 'A reserva precisa durar no mínimo 15 minutos e no máximo 4 horas.'}; 4h01: HTTP 422 {'erro': 'DURACAO_INVALIDA', 'mensagem': 'A reserva precisa durar no mínimo 15 minutos e no máximo 4 horas.'} | PASSOU |
| CA-05 | Reserva com início 07/01 08h, relógio em 07/01 09h | 422 INICIO_NO_PASSADO | HTTP 422 {'erro': 'INICIO_NO_PASSADO', 'mensagem': 'Não é possível reservar com início no passado.'} | PASSOU |
| CA-06 | 5 participantes na Ibirapuera (capacidade 4) | 422 CAPACIDADE_EXCEDIDA | HTTP 422 {'erro': 'CAPACIDADE_EXCEDIDA', 'mensagem': 'A sala comporta no máximo 4 participantes.'} | PASSOU |
| CA-07 | Cancelar reserva futura (Laranjeira 08/01 14h–15h) e reservar o mesmo horário | 200 CANCELADA; nova reserva 201; histórico mantém CANCELADA | cancelar: HTTP 200 {'id': 3, 'status': 'CANCELADA'}; nova: HTTP 201 {'id': 4, 'status': 'ATIVA'}; histórico: CANCELADA | PASSOU |
| CA-08 | Cancelar a reserva de 08/01 10h–11h com relógio em 09/01 09h | 422 CANCELAMENTO_NAO_PERMITIDO; reserva segue ATIVA | HTTP 422 {'erro': 'CANCELAMENTO_NAO_PERMITIDO', 'mensagem': 'Só reservas futuras podem ser canceladas.'}; status depois: ATIVA | PASSOU |
| CA-09 | Salas livres 08/01 10h–11h, local SAO_PAULO, capacidade mínima 4 e 5 (Paulista ocupada) | cap>=4: [Sala Ibirapuera]; cap>=5: [] | HTTP 200 cap>=4: ['Sala Ibirapuera']; HTTP 200 cap>=5: [] | PASSOU |
| CA-10 | Ocupação de 08/01 da Morada do Sol: 1h ativa (9h–10h) e 2h canceladas (13h–15h) | 60 min, taxa 10.0% (canceladas fora) | HTTP 200 minutos=60 taxa=10.0 | PASSOU |
