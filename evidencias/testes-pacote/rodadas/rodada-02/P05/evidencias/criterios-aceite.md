# Critérios de aceite verificados via HTTP

Executado em 2026-10-26T07:49:52 contra o servidor real (uvicorn).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| CA-01 | Abrir chamado ALTA | HTTP 201, situacao=ABERTO, prazo 8h após a abertura | HTTP 201, situacao=ABERTO, aberto_em=2030-01-07T09:00:00-03:00, prazo_em=2030-01-07T17:00:00-03:00, horas=8 | PASSOU |
| CA-02 | Assumir chamado sem informar responsável | Recusa: HTTP 422 RESPONSAVEL_OBRIGATORIO, continua ABERTO | HTTP 422, erro=RESPONSAVEL_OBRIGATORIO, mensagem=Informe o nome do responsável para assumir o chamado., situacao=ABERTO | PASSOU |
| CA-03 | Resolver chamado ABERTO direto | Recusa: HTTP 409 TRANSICAO_INVALIDA, continua ABERTO | HTTP 409, erro=TRANSICAO_INVALIDA, mensagem=Não é possível resolver um chamado na situação ABERTO; a ação só vale para chamados EM_ATENDIMENTO., situacao=ABERTO | PASSOU |
| CA-04 | Resolver chamado sem informar solução | Recusa: HTTP 422 SOLUCAO_OBRIGATORIA, continua EM_ATENDIMENTO | HTTP 422, erro=SOLUCAO_OBRIGATORIA, mensagem=Informe a descrição da solução para resolver o chamado., situacao=EM_ATENDIMENTO | PASSOU |
| CA-05 | Resolver chamado MEDIA 2h após a abertura (dentro do prazo) e consultar relatório | Conta como dentro do prazo: MEDIA resolvidos=1, dentro_do_prazo=1, percentual=100.0 | HTTP 200, situacao=RESOLVIDO, resolvido_em=2030-01-07T11:00:00-03:00 \| HTTP 200, MEDIA: resolvidos=1, dentro_do_prazo=1, percentual=100.0 | PASSOU |
| CA-06 | Resolver chamado CRITICA 4h01 após a abertura e consultar relatório | Conta como fora do prazo: CRITICA resolvidos=1, dentro_do_prazo=0 | HTTP 200, situacao=RESOLVIDO, resolvido_em=2030-01-07T13:01:00-03:00 \| HTTP 200, CRITICA: resolvidos=1, dentro_do_prazo=0, percentual=0.0 | PASSOU |
| CA-07 | Consultar a fila com chamado CRITICA de prazo vencido (aberto 4h01 antes) | Chamado aparece como ATRASADO | HTTP 200, id=14, prazo_em=2030-01-07T13:00:00-03:00, indicacao=ATRASADO | PASSOU |
| CA-08 | Reabrir chamado resolvido há 6 dias | HTTP 200, situacao=EM_ATENDIMENTO | HTTP 200, situacao=EM_ATENDIMENTO, prazo_em=2030-01-07T17:00:00-03:00 | PASSOU |
| CA-09 | Reabrir chamado resolvido há 8 dias | Recusa: HTTP 409 PRAZO_REABERTURA_ENCERRADO, continua RESOLVIDO | HTTP 409, erro=PRAZO_REABERTURA_ENCERRADO, mensagem=O chamado só pode ser reaberto até 7 dias depois da resolução., situacao=RESOLVIDO | PASSOU |
| CA-10 | Fechar chamado ABERTO | Recusa: HTTP 409 TRANSICAO_INVALIDA, continua ABERTO | HTTP 409, erro=TRANSICAO_INVALIDA, mensagem=Não é possível fechar um chamado na situação ABERTO; a ação só vale para chamados RESOLVIDO., situacao=ABERTO | PASSOU |
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
