# Critérios de aceite verificados via HTTP

Executado em 2026-10-26T08:05:49 contra o servidor real (uvicorn).

**Resultado: 15/15 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| CA-01 | Lançar despesa válida | HTTP 201, situacao=PENDENTE | HTTP 201, id=6, situacao=PENDENTE, valor_centavos=5000 | PASSOU |
| CA-02 | Lançar ALIMENTACAO de R$ 120,01 | HTTP 422, erro=VALOR_ACIMA_DO_LIMITE | HTTP 422, erro=VALOR_ACIMA_DO_LIMITE, mensagem=O valor passa do limite de R$ 120,00 por despesa da categoria ALIMENTACAO. | PASSOU |
| CA-03 | Lançar HOSPEDAGEM de R$ 450,00 | HTTP 201, situacao=PENDENTE, valor_centavos=45000 | HTTP 201, situacao=PENDENTE, categoria=HOSPEDAGEM, valor_centavos=45000 | PASSOU |
| CA-04 | Lançar despesa com data de 61 dias atrás (2029-11-07) | HTTP 422, erro=DATA_MUITO_ANTIGA | HTTP 422, erro=DATA_MUITO_ANTIGA, mensagem=A data da despesa não pode ter mais de 60 dias. | PASSOU |
| CA-05 | Lançar despesa com data de amanhã (2030-01-08) | HTTP 422, erro=DATA_FUTURA | HTTP 422, erro=DATA_FUTURA, mensagem=A data da despesa não pode ser futura. | PASSOU |
| CA-06 | Lançar o mesmo comprovante duas vezes para o mesmo colaborador | 1ª HTTP 201; 2ª HTTP 409, erro=COMPROVANTE_DUPLICADO | 1ª HTTP 201, situacao=PENDENTE; 2ª HTTP 409, erro=COMPROVANTE_DUPLICADO, mensagem=Este número de comprovante já foi lançado por este colaborador. | PASSOU |
| CA-07 | Recusar despesa sem informar motivo | HTTP 422, erro=MOTIVO_OBRIGATORIO; segue PENDENTE | HTTP 422, erro=MOTIVO_OBRIGATORIO, mensagem=Informe o motivo da recusa.; situação após: PENDENTE | PASSOU |
| CA-08 | Marcar como paga uma despesa PENDENTE | HTTP 409, erro=TRANSICAO_INVALIDA | HTTP 409, erro=TRANSICAO_INVALIDA, mensagem=Não é possível mudar a despesa de PENDENTE para PAGA. | PASSOU |
| CA-09 | Aprovar e depois pagar uma despesa | aprovar HTTP 200 APROVADA; pagar HTTP 200 PAGA | aprovar HTTP 200, situacao=APROVADA; pagar HTTP 200, situacao=PAGA | PASSOU |
| CA-10 | Resumo de 2029-11 com uma despesa APROVADA (30000), PAGA (7000), RECUSADA (11000) e PENDENTE (50000) | HTTP 200; HOSPEDAGEM +30000, TRANSPORTE +7000, ALIMENTACAO +0, OUTROS +0, total +37000 | HTTP 200, totais_centavos={'TRANSPORTE': 7000, 'HOSPEDAGEM': 30000, 'ALIMENTACAO': 0, 'OUTROS': 0}, total_geral_centavos=37000, acréscimo={'TRANSPORTE': 7000, 'HOSPEDAGEM': 30000, 'ALIMENTACAO': 0, 'OUTROS': 0}, acréscimo total=37000 | PASSOU |
| CA-11 | Editar valor, descrição e categoria de uma despesa PENDENTE | HTTP 200; HOSPEDAGEM, 40000, 'Hotel corrigido', segue PENDENTE; data e comprovante iguais | HTTP 200, categoria=HOSPEDAGEM, valor_centavos=40000, descricao=Hotel corrigido, situacao=PENDENTE, comprovante=CA11 | PASSOU |
| CA-12 | Editar despesa PENDENTE para ALIMENTACAO de R$ 120,01 | HTTP 422, erro=VALOR_ACIMA_DO_LIMITE; despesa inalterada | HTTP 422, erro=VALOR_ACIMA_DO_LIMITE, mensagem=O valor passa do limite de R$ 120,00 por despesa da categoria ALIMENTACAO.; depois: TRANSPORTE 5000 | PASSOU |
| CA-13 | Editar uma despesa APROVADA | HTTP 409, erro=EDICAO_NAO_PERMITIDA; despesa inalterada | HTTP 409, erro=EDICAO_NAO_PERMITIDA, mensagem=Só despesa PENDENTE pode ser editada; esta está APROVADA. | PASSOU |
| CA-14 | Resumo de 2029-11 com 2 APROVADA HOSPEDAGEM, 1 PAGA TRANSPORTE, 1 RECUSADA ALIMENTACAO, 1 PENDENTE OUTROS | HTTP 200; quantidades HOSPEDAGEM +2, TRANSPORTE +1, ALIMENTACAO +0, OUTROS +0; quantidade_total +3 | HTTP 200, quantidades={'TRANSPORTE': 1, 'HOSPEDAGEM': 2, 'ALIMENTACAO': 0, 'OUTROS': 0}, quantidade_total=3, acréscimo={'TRANSPORTE': 1, 'HOSPEDAGEM': 2, 'ALIMENTACAO': 0, 'OUTROS': 0}, acréscimo total=3 | PASSOU |
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
