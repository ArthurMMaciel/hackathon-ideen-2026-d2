# Critérios de aceite verificados via HTTP

Executado em 2026-10-23T17:57:16 contra o servidor real (uvicorn, porta 55815).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
| CA-01 | Solicitar 10 dias com 40 dias de antecedência | 201, SOLICITADA, 10 dias | HTTP 201 situacao=SOLICITADA dias=10 | PASSOU |
| CA-02 | Solicitar 4 dias | Recusa (422 DURACAO_INVALIDA) | HTTP 422 {'erro': 'DURACAO_INVALIDA', 'mensagem': 'As férias devem ter entre 5 e 30 dias; o pedido tem 4.'} | PASSOU |
| CA-03 | Solicitar com início em 29 dias | Recusa por antecedência (422 ANTECEDENCIA_INSUFICIENTE) | HTTP 422 {'erro': 'ANTECEDENCIA_INSUFICIENTE', 'mensagem': 'O início precisa ter pelo menos 30 dias de antecedência (a partir de 2030-02-06).'} | PASSOU |
| CA-04 | Solicitar mais dias que o saldo disponível (10 disponíveis, pede 15) | Recusa (422 SALDO_INSUFICIENTE) | 1º pedido HTTP 201; 2º HTTP 422 {'erro': 'SALDO_INSUFICIENTE', 'mensagem': 'O pedido tem 15 dias, mas o saldo disponível é de 10 dias.'} | PASSOU |
| CA-05 | Aprovar solicitação válida | 200 APROVADA e saldo reduzido (30 -> 20) | HTTP 200 situacao=APROVADA saldo 30 -> 20 | PASSOU |
| CA-06 | Aprovar segunda pessoa da mesma equipe com dias em comum | Recusa (409 LIMITE_EQUIPE), continua SOLICITADA | HTTP 409 {'erro': 'LIMITE_EQUIPE', 'mensagem': 'Já existe outra pessoa da mesma equipe com férias aprovadas em pelo menos um desses dias.'}; situação SOLICITADA | PASSOU |
| CA-07 | Aprovar pessoa de outra equipe no mesmo período | 200 APROVADA | HTTP 200 {'id': 4, 'colaborador_id': 4, 'colaborador_nome': 'Diego Prates', 'equipe': 'PRODUTO', 'inicio': '2030-02-16', 'fim': '2030-02-25', 'dias': 10, 'situacao': 'APROVADA', 'criado_em': '2030-01-07T09:00:00-03:00'} | PASSOU |
| CA-08 | Aprovar mesma equipe com férias começando no dia seguinte ao fim de outra | 200 APROVADA | HTTP 200 {'id': 5, 'colaborador_id': 5, 'colaborador_nome': 'Elisa Moura', 'equipe': 'PRODUTO', 'inicio': '2030-02-26', 'fim': '2030-03-07', 'dias': 10, 'situacao': 'APROVADA', 'criado_em': '2030-01-07T09:00:00-03:00'} | PASSOU |
| CA-09 | Cancelar solicitação aprovada antes do início | 200 CANCELADA e saldo devolvido (20 -> 30) | HTTP 200 situacao=CANCELADA saldo 20 -> 30 | PASSOU |
| CA-10 | Calendário do mês com solicitações SOLICITADA e REPROVADA | Só as aprovadas aparecem (Heitor Vilela) | HTTP 200 nomes no mês=['Heitor Vilela']; 2030-05-10={'DADOS': [], 'PRODUTO': [], 'SUPORTE': ['Heitor Vilela']} | PASSOU |
