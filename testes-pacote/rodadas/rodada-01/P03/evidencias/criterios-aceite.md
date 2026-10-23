# Critérios de aceite verificados via HTTP

Executado em 2026-10-23T17:59:31 contra o servidor real (uvicorn, porta 55639).

**Resultado: 11/11 aprovados.**

| Código | Cenário | Esperado | Obtido | Resultado |
|---|---|---|---|---|
| CA-01 | Inscrever em turma com vaga | Inscrição CONFIRMADA | HTTP 201 {"id":1,"turma_id":4,"nome":"Pessoa ca01","email":"ca01@exemplo.test","situacao":"CONFIRMADA","criada_em":"2030-01-07T09:00:00-03:00","posicao_espera":null} | PASSOU |
| CA-02 | Inscrever em turma lotada | Inscrição ESPERA, primeira da fila | HTTP 201 {"id":3,"turma_id":5,"nome":"Pessoa ca02b","email":"ca02b@exemplo.test","situacao":"ESPERA","criada_em":"2030-01-07T09:00:00-03:00","posicao_espera":1} | PASSOU |
| CA-03 | Cancelar confirmada numa turma com fila de espera | A primeira da espera passa a CONFIRMADA | HTTP 200; cancelada #2 CANCELADA; promovida (3, 'CONFIRMADA') (era ESPERA posição 1: #3); próxima da fila #4 ESPERA posição 1 | PASSOU |
| CA-04 | Inscrever o mesmo e-mail duas vezes na mesma turma | Segunda recusada | 1ª HTTP 201; 2ª HTTP 409 {"erro":"INSCRICAO_DUPLICADA","mensagem":"Este e-mail já tem uma inscrição confirmada ou em espera nesta turma."} | PASSOU |
| CA-05 | Inscrever 23 horas antes do início | Recusa | HTTP 422 {"erro":"INSCRICOES_ENCERRADAS","mensagem":"As inscrições fecham 24 horas antes do início da turma."} | PASSOU |
| CA-06 | Cancelar inscrição depois do início da turma | Recusa | HTTP 422 {"erro":"CANCELAMENTO_ENCERRADO","mensagem":"O cancelamento só é permitido até o início da turma."} | PASSOU |
| CA-07 | Marcar presença antes do início da turma | Recusa | HTTP 422 {"erro":"PRESENCA_ANTES_DO_INICIO","mensagem":"A presença só pode ser marcada depois do início da turma."} | PASSOU |
| CA-08 | Marcar presença de uma inscrição em ESPERA | Recusa | HTTP 422 {"erro":"PRESENCA_SITUACAO_INVALIDA","mensagem":"A presença só pode ser marcada em inscrição confirmada; esta está ESPERA."} | PASSOU |
| CA-09 | Consultar turmas futuras depois de lotar uma turma | Turma lotada aparece com 0 vagas restantes | HTTP 200 turma 4: [{'id': 4, 'titulo': 'Verificação CA-01/CA-06/CA-09', 'inicio': '2030-01-10T09:00:00-03:00', 'duracao_minutos': 60, 'modalidade': 'ONLINE', 'vagas': 2, 'vagas_restantes': 0}] | PASSOU |
| CA-10 | Taxa de presença com 3 presentes e 1 ausente | 75% | marcações [200, 200, 200, 200]; HTTP 200 {"turma_id":8,"presentes":3,"ausentes":1,"taxa_presenca":75.0} | PASSOU |
| TELA | Abrir a tela web | HTTP 200 com HTML | HTTP 200 | PASSOU |
