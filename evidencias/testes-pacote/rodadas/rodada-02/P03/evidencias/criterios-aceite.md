# Critérios de aceite verificados via HTTP

Executado em 2026-10-26T07:49:30 contra o servidor real (uvicorn).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| CA-01 | Inscrever em turma com vaga (2 vagas, nenhuma ocupada) | HTTP 201, situacao=CONFIRMADA | HTTP 201, situacao=CONFIRMADA | PASSOU |
| CA-02 | Inscrever em turma lotada (1 vaga já confirmada) | HTTP 201, situacao=ESPERA, posicao_espera=1 | HTTP 201, situacao=ESPERA, posicao_espera=1 | PASSOU |
| CA-03 | Cancelar a confirmada com 2 na espera | HTTP 200, cancelada=CANCELADA, primeira da espera (B) passa a CONFIRMADA | HTTP 200, cancelada=CANCELADA, promovida_id=5 (B=5), situacao B na lista=CONFIRMADA | PASSOU |
| CA-04 | Inscrever o mesmo e-mail duas vezes na mesma turma | HTTP 409, erro=INSCRICAO_DUPLICADA | HTTP 409, erro=INSCRICAO_DUPLICADA, mensagem=Este e-mail já tem uma inscrição confirmada ou em espera nesta turma. | PASSOU |
| CA-05 | Inscrever 23 horas antes do início | HTTP 422, erro=INSCRICOES_ENCERRADAS | HTTP 422, erro=INSCRICOES_ENCERRADAS, mensagem=As inscrições fecham 24 horas antes do início da turma. | PASSOU |
| CA-06 | Cancelar inscrição 1 hora depois do início da turma | HTTP 422, erro=CANCELAMENTO_ENCERRADO | HTTP 422, erro=CANCELAMENTO_ENCERRADO, mensagem=Não é possível cancelar depois do início da turma. | PASSOU |
| CA-07 | Marcar presença antes do início da turma | HTTP 422, erro=TURMA_NAO_INICIADA | HTTP 422, erro=TURMA_NAO_INICIADA, mensagem=A presença só pode ser marcada depois do início da turma. | PASSOU |
| CA-08 | Marcar presença de uma inscrição em ESPERA (depois do início) | HTTP 409, erro=SITUACAO_SEM_PRESENCA | HTTP 409, erro=SITUACAO_SEM_PRESENCA, mensagem=Só inscrição CONFIRMADA pode receber presença; esta está ESPERA. | PASSOU |
| CA-09 | Consultar turmas futuras depois de lotar uma turma (2 de 2 vagas) | HTTP 200, turma lotada listada com vagas_restantes=0 | HTTP 200, turma 11 listada=True, vagas_restantes=0 | PASSOU |
| CA-10 | Taxa de presença com 3 presentes e 1 ausente | HTTP 200, taxa_presenca_percentual=75.0 | HTTP 200, presentes=3, ausentes=1, taxa_presenca_percentual=75.0 | PASSOU |
| TELA | Abrir a tela web e carregar as turmas que ela lista | HTTP 200 com HTML; GET /api/turmas 200 com as 3 turmas iniciais | HTTP 200; turmas: HTTP 200, 3 itens | PASSOU |
