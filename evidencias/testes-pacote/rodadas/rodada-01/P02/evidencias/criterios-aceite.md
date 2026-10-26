# Critérios de aceite verificados via HTTP

Executado em 2026-10-23T17:58:19 contra o servidor real (uvicorn, porta 52390).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
| CA-01 | Lançar despesa válida | 201, situacao PENDENTE | HTTP 201 {"id":6,"colaborador_nome":"Verificacao Ficticia","colaborador_email":"verificacao@empresa.example","data_despesa":"2030-01-05","categoria":"TRANSPORTE","valor" | PASSOU |
| CA-02 | Lançar ALIMENTACAO de R$ 120,01 | 422 LIMITE_EXCEDIDO | HTTP 422 {"erro":"LIMITE_EXCEDIDO","mensagem":"O valor ultrapassa o limite de R$ 120,00 por despesa da categoria ALIMENTACAO."} | PASSOU |
| CA-03 | Lançar HOSPEDAGEM de R$ 450,00 | 201, despesa criada | HTTP 201 {"id":7,"colaborador_nome":"Verificacao Ficticia","colaborador_email":"verificacao@empresa.example","data_despesa":"2030-01-05","categoria":"HOSPEDAGEM","valor" | PASSOU |
| CA-04 | Lançar despesa com data de 61 dias atrás (2029-11-07) | 422 DATA_ANTIGA | HTTP 422 {"erro":"DATA_ANTIGA","mensagem":"A data da despesa não pode ter mais de 60 dias."} | PASSOU |
| CA-05 | Lançar despesa com data de amanhã (2030-01-08) | 422 DATA_FUTURA | HTTP 422 {"erro":"DATA_FUTURA","mensagem":"A data da despesa não pode ser futura."} | PASSOU |
| CA-06 | Lançar o mesmo comprovante duas vezes para o mesmo colaborador | 1ª 201; 2ª 409 COMPROVANTE_DUPLICADO | 1ª HTTP 201; 2ª HTTP 409 {"erro":"COMPROVANTE_DUPLICADO","mensagem":"Este número de comprovante já foi lançado por este colaborador."} | PASSOU |
| CA-07 | Recusar despesa sem informar motivo | 422 MOTIVO_OBRIGATORIO, segue PENDENTE | HTTP 422 {"erro":"MOTIVO_OBRIGATORIO","mensagem":"Informe o motivo para recusar a despesa."}; situação depois: PENDENTE | PASSOU |
| CA-08 | Marcar como paga uma despesa PENDENTE | 409 TRANSICAO_INVALIDA, segue PENDENTE | HTTP 409 {"erro":"TRANSICAO_INVALIDA","mensagem":"Não é possível mudar a situação de PENDENTE para PAGA."}; situação depois: PENDENTE | PASSOU |
| CA-09 | Aprovar e depois pagar uma despesa | 200 APROVADA; 200 PAGA | aprovar HTTP 200 APROVADA; pagar HTTP 200 PAGA | PASSOU |
| CA-10 | Resumo de 2030-03 com PAGA 200,00, APROVADA 80,50, RECUSADA 300,00 e PENDENTE 400,00 | RECUSADA e PENDENTE fora: total 280,50; HOSPEDAGEM e OUTROS 0 | HTTP 200 total_geral=280.5 por_categoria={'TRANSPORTE': 200.0, 'HOSPEDAGEM': 0.0, 'ALIMENTACAO': 80.5, 'OUTROS': 0.0} | PASSOU |
