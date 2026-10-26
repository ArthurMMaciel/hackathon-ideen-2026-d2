# Critérios de aceite verificados via HTTP

Executado em 2026-10-26T07:48:39 contra o servidor real (uvicorn).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| CA-01 | Solicitar 10 dias com 40 dias de antecedência (2030-02-16 a 2030-02-25) | HTTP 201, situacao=SOLICITADA, dias=10 | HTTP 201, situacao=SOLICITADA, dias=10 | PASSOU |
| CA-02 | Solicitar 4 dias (2030-03-01 a 2030-03-04) | HTTP 422, erro=DURACAO_INVALIDA | HTTP 422, erro=DURACAO_INVALIDA | PASSOU |
| CA-03 | Solicitar com início em 29 dias (2030-02-05) | HTTP 422, erro=ANTECEDENCIA_INSUFICIENTE | HTTP 422, erro=ANTECEDENCIA_INSUFICIENTE | PASSOU |
| CA-04 | Solicitar 10 dias com saldo disponível de 8 | HTTP 409, erro=SALDO_INSUFICIENTE | HTTP 409, erro=SALDO_INSUFICIENTE | PASSOU |
| CA-05 | Aprovar solicitação válida de 10 dias | HTTP 200, situacao=APROVADA, saldo 30 → 20 | HTTP 200, situacao=APROVADA, saldo 30 → 20 | PASSOU |
| CA-06 | Aprovar segunda pessoa de DADOS em 2030-02-20 a 2030-03-01 (dias em comum) | HTTP 409, erro=LIMITE_EQUIPE; segue SOLICITADA | HTTP 409, erro=LIMITE_EQUIPE; situação SOLICITADA | PASSOU |
| CA-07 | Aprovar pessoa de PRODUTO em 2030-02-16 a 2030-02-25 | HTTP 200, situacao=APROVADA | HTTP 200, situacao=APROVADA | PASSOU |
| CA-08 | Aprovar pessoa de DADOS em 2030-02-26 (dia seguinte ao fim de outra, 2030-02-25) | HTTP 200, situacao=APROVADA | HTTP 200, situacao=APROVADA | PASSOU |
| CA-09 | Cancelar solicitação aprovada (início 2030-03-10) em 2030-01-07 | HTTP 200, situacao=CANCELADA, saldo 20 → 30 | HTTP 200, situacao=CANCELADA, saldo 20 → 30 | PASSOU |
| CA-10 | Calendário de 2030-04 com APROVADA (DADOS), SOLICITADA (PRODUTO) e REPROVADA (SUPORTE) | HTTP 200, só a aprovada (Verif Dados A) aparece | HTTP 200, 30 dias, nomes no mês=['Verif Dados A'], 2030-04-10 DADOS=['Verif Dados A'] PRODUTO=[] SUPORTE=[] | PASSOU |
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
