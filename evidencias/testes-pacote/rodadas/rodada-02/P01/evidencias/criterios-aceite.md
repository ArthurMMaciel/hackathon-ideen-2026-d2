# Critérios de aceite verificados via HTTP

Executado em 2026-10-26T07:49:30 contra o servidor real (uvicorn).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| CA-01 | Emprestar notebook disponível com prevista em 7 dias | HTTP 201, status=ABERTO; equipamento EMPRESTADO | HTTP 201, status=ABERTO, data_retirada=2030-01-07, data_prevista=2030-01-14; equipamento situacao=EMPRESTADO | PASSOU |
| CA-02 | Emprestar equipamento já emprestado | HTTP 409, erro=EQUIPAMENTO_INDISPONIVEL | HTTP 409, erro=EQUIPAMENTO_INDISPONIVEL, mensagem=O equipamento já está emprestado; só equipamento disponível pode ser emprestado. | PASSOU |
| CA-03 | Emprestar EQ-0008 (HEADSET) em manutenção | HTTP 409, erro=EQUIPAMENTO_INDISPONIVEL | HTTP 409, erro=EQUIPAMENTO_INDISPONIVEL, mensagem=O equipamento está em manutenção; só equipamento disponível pode ser emprestado. | PASSOU |
| CA-04 | Emprestar notebook com prevista em 15 dias | HTTP 422, erro=PRAZO_EXCEDIDO | HTTP 422, erro=PRAZO_EXCEDIDO, mensagem=O prazo máximo para notebook é de 14 dias a partir da retirada.; equipamento situacao=DISPONIVEL | PASSOU |
| CA-05 | Emprestar projetor com prevista em 3 dias | HTTP 201, status=ABERTO | HTTP 201, status=ABERTO, data_retirada=2030-01-07, data_prevista=2030-01-10 | PASSOU |
| CA-06 | Pessoa com 2 empréstimos em aberto pede um terceiro | 2 x HTTP 201, depois HTTP 409 erro=LIMITE_EMPRESTIMOS | anteriores=[201, 201]; HTTP 409, erro=LIMITE_EMPRESTIMOS, mensagem=Esta pessoa já tem 2 empréstimos em aberto; devolva um antes de pegar outro. | PASSOU |
| CA-07 | Devolver sem defeito | HTTP 200, status=DEVOLVIDO; equipamento DISPONIVEL | HTTP 200, status=DEVOLVIDO, data_devolucao=2030-01-07, defeito=False; equipamento situacao=DISPONIVEL | PASSOU |
| CA-08 | Devolver com defeito | HTTP 200; equipamento MANUTENCAO | HTTP 200, status=DEVOLVIDO, defeito=True; equipamento situacao=MANUTENCAO | PASSOU |
| CA-09 | Prevista ontem (2030-01-08), hoje 2030-01-09, ainda aberto | aparece nos atrasados com dias_atraso=1 | HTTP 200; emprestimo 7 prevista=2030-01-08 status=ABERTO dias_atraso=1 | PASSOU |
| CA-10 | Devolver empréstimo já devolvido | HTTP 409, erro=EMPRESTIMO_JA_DEVOLVIDO | HTTP 409, erro=EMPRESTIMO_JA_DEVOLVIDO, mensagem=Este empréstimo já foi devolvido. | PASSOU |
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
