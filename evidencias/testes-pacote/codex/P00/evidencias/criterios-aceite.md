# Critérios de aceite verificados via HTTP

Executado em 2026-10-26T08:36:04 contra o servidor real (uvicorn).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| CA-01 | Reserva livre | 201 ATIVA | HTTP 201, status=ATIVA | PASSOU |
| CA-02 | Sobreposição | 409 CONFLITO_HORARIO | HTTP 409, erro=CONFLITO_HORARIO, mensagem=Há conflito de horário nesta sala. | PASSOU |
| CA-03 | Intervalos encostam | 201 ATIVA | HTTP 201, status=ATIVA | PASSOU |
| CA-04 | Duração 10min ou 4h01 | ambos 422 DURACAO_INVALIDA | HTTP 422, erro=DURACAO_INVALIDA; HTTP 422, erro=DURACAO_INVALIDA | PASSOU |
| CA-05 | Início no passado | 422 INICIO_PASSADO | HTTP 422, erro=INICIO_PASSADO | PASSOU |
| CA-06 | Capacidade excedida | 422 CAPACIDADE_EXCEDIDA | HTTP 422, erro=CAPACIDADE_EXCEDIDA | PASSOU |
| CA-07 | Cancelar e liberar | 200 CANCELADA; 201 ATIVA | HTTP 200, status=CANCELADA; HTTP 201, status=ATIVA | PASSOU |
| CA-08 | Cancelar reserva passada | 422 CANCELAMENTO_FORA_DO_PRAZO | HTTP 422, erro=CANCELAMENTO_FORA_DO_PRAZO | PASSOU |
| CA-09 | Filtro de salas livres | 200 lista vazia | HTTP 200, salas=[] | PASSOU |
| CA-10 | Ocupação sem canceladas | 200; sala 1 = 5% | HTTP 200, percentual=5.0 | PASSOU |
| TELA | Tela web | 200, formulário e agenda | HTTP 200 | PASSOU |
