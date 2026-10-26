# Critérios de aceite verificados via HTTP

Executado em 2026-10-23T17:59:28 contra o servidor real (uvicorn, porta 55633).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
| CA-01 | Emprestar equipamento disponível com prazo dentro do limite | Empréstimo ABERTO e equipamento EMPRESTADO | HTTP 201 id=1, patrimonio=EQ-0001, data_retirada=2030-01-07, data_prevista=2030-01-10, data_devolucao=None, status=ABERTO, situacao_equipamento=EMPRESTADO \| equipamento EMPRESTADO | PASSOU |
| CA-02 | Emprestar equipamento já emprestado | Recusa | HTTP 409 {"erro":"EQUIPAMENTO_INDISPONIVEL","mensagem":"O equipamento está EMPRESTADO e só equipamento DISPONIVEL pode ser emprestado."} | PASSOU |
| CA-03 | Emprestar equipamento em manutenção | Recusa | HTTP 409 {"erro":"EQUIPAMENTO_INDISPONIVEL","mensagem":"O equipamento está MANUTENCAO e só equipamento DISPONIVEL pode ser emprestado."} | PASSOU |
| CA-04 | Emprestar notebook com devolução prevista para 15 dias depois | Recusa por prazo | HTTP 422 {"erro":"PRAZO_EXCEDIDO","mensagem":"O prazo máximo para NOTEBOOK é de 14 dias a partir da retirada."} \| equipamento DISPONIVEL | PASSOU |
| CA-05 | Emprestar projetor com devolução prevista para 3 dias depois | Empréstimo criado | HTTP 201 id=2, patrimonio=EQ-0004, data_retirada=2030-01-07, data_prevista=2030-01-10, data_devolucao=None, status=ABERTO, situacao_equipamento=EMPRESTADO | PASSOU |
| CA-06 | Pessoa com 2 empréstimos em aberto pede um terceiro | Recusa | 1º HTTP 201, 2º HTTP 201, 3º HTTP 422 {"erro":"LIMITE_EMPRESTIMOS","mensagem":"Esta pessoa já tem 2 empréstimos em aberto; o máximo é 2."} | PASSOU |
| CA-07 | Devolver sem defeito | Empréstimo DEVOLVIDO e equipamento DISPONIVEL | HTTP 200 id=1, patrimonio=EQ-0001, data_retirada=2030-01-07, data_prevista=2030-01-10, data_devolucao=2030-01-07, status=DEVOLVIDO, situacao_equipamento=DISPONIVEL \| equipamento DISPONIVEL | PASSOU |
| CA-08 | Devolver com defeito | Equipamento MANUTENCAO | HTTP 200 id=4, patrimonio=EQ-0006, data_retirada=2030-01-07, data_prevista=2030-01-10, data_devolucao=2030-01-07, status=DEVOLVIDO, situacao_equipamento=MANUTENCAO \| equipamento MANUTENCAO | PASSOU |
| CA-09 | Empréstimo com devolução prevista para ontem e ainda aberto | Aparece nos atrasados com 1 dia de atraso | HTTP 200; empréstimo 5 com dias_atraso 1 (no dia anterior: ausente) | PASSOU |
| CA-10 | Devolver empréstimo já devolvido | Recusa | HTTP 409 {"erro":"EMPRESTIMO_JA_DEVOLVIDO","mensagem":"Este empréstimo já foi devolvido."} | PASSOU |
