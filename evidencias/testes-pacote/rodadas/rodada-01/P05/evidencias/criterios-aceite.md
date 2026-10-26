# Critérios de aceite verificados via HTTP

Executado em 2026-10-23T17:58:08 contra o servidor real (uvicorn, porta 56537).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
| CA-01 | Abrir chamado ALTA | ABERTO, prazo 8h após a abertura | HTTP 201 situacao=ABERTO aberto_em=2030-01-07T09:00:00-03:00 prazo=2030-01-07T17:00:00-03:00 | PASSOU |
| CA-02 | Assumir chamado sem informar responsável | Recusa | HTTP 422 RESPONSAVEL_OBRIGATORIO: Informe o nome do responsável para assumir o chamado.; situação continua ABERTO | PASSOU |
| CA-03 | Resolver chamado ABERTO direto | Recusa | HTTP 422 TRANSICAO_INVALIDA: Não é permitido resolver um chamado ABERTO: essa ação só vale para chamados EM_ATENDIMENTO.; situação continua ABERTO | PASSOU |
| CA-04 | Resolver chamado sem informar solução | Recusa | HTTP 422 SOLUCAO_OBRIGATORIA: Informe a descrição da solução para resolver o chamado.; situação continua EM_ATENDIMENTO | PASSOU |
| CA-05 | Resolver chamado dentro do prazo | Conta como dentro do prazo no relatório | resolver: HTTP 200 dentro_do_prazo=True; relatório MEDIA resolvidos=1 dentro=1 percentual=100.0 | PASSOU |
| CA-06 | Resolver chamado CRITICA 4h01 depois da abertura | Conta como fora do prazo | resolver: HTTP 200 aberto_em=2030-01-07T09:00:00-03:00 resolvido_em=2030-01-07T13:01:00-03:00 dentro_do_prazo=False; relatório CRITICA resolvidos=1 dentro=0 percentual=0.0 | PASSOU |
| CA-07 | Consultar a fila com um chamado de prazo vencido | Chamado aparece como ATRASADO | HTTP 200 chamado 14 prazo=2030-01-07T13:00:00-03:00 indicacao=ATRASADO | PASSOU |
| CA-08 | Reabrir chamado resolvido há 6 dias | Chamado EM_ATENDIMENTO | HTTP 200 situacao=EM_ATENDIMENTO (resolvido em 2030-01-07T13:01:00-03:00, agora 2030-01-13T13:01:00-03:00) | PASSOU |
| CA-09 | Reabrir chamado resolvido há 8 dias | Recusa | HTTP 422 REABERTURA_EXPIRADA: O chamado só pode ser reaberto até 7 dias depois da resolução.; situação continua RESOLVIDO (resolvido em 2030-01-07T09:00:00-03:00, agora 2030-01-15T09:00:00-03:00) | PASSOU |
| CA-10 | Fechar chamado ABERTO | Recusa | HTTP 422 TRANSICAO_INVALIDA: Não é permitido fechar um chamado ABERTO: essa ação só vale para chamados RESOLVIDO.; situação continua ABERTO | PASSOU |
