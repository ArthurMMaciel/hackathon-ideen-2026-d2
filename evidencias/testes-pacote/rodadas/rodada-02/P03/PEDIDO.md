# Pedido · Inscrição em treinamentos

## O pedido, como o cliente escreveu

"Fazemos treinamentos internos e as inscrições são por formulário. Sempre lota, alguém desiste e a vaga fica parada. Queria cadastrar as turmas, as pessoas se inscreverem, ter lista de espera automática e saber quem compareceu. Não precisa de login."

## O que o sistema precisa fazer

**Turmas**
- Cadastro com título, data e hora de início, duração em minutos, modalidade (`PRESENCIAL`, `ONLINE`) e quantidade de vagas (de 1 a 50).
- O sistema já começa com 3 turmas futuras.

**Inscrições**
- Uma inscrição tem turma, pessoa (nome e e-mail) e situação: `CONFIRMADA`, `ESPERA`, `CANCELADA`, `PRESENTE` ou `AUSENTE`.
- Se a turma tem vaga, a inscrição nasce `CONFIRMADA`. Se está lotada, nasce `ESPERA`, por ordem de chegada.
- O mesmo e-mail não pode ter duas inscrições ativas (`CONFIRMADA` ou `ESPERA`) na mesma turma.
- Inscrições fecham 24 horas antes do início da turma.

**Cancelamento**
- Pode cancelar até o início da turma.
- Quando uma inscrição `CONFIRMADA` é cancelada, a primeira da `ESPERA` passa a `CONFIRMADA`.

**Presença**
- Só depois do início da turma, e só para inscrições `CONFIRMADA`: marcar `PRESENTE` ou `AUSENTE`.

**Consulta**
- Turmas futuras com a quantidade de vagas restantes.

**Relatório**
- Taxa de presença de uma turma: presentes ÷ (presentes + ausentes), em percentual.

**Interface**
- API REST para todas as operações.
- Uma tela web simples para ver as turmas, se inscrever e ver os inscritos de uma turma.
- Dados em banco local. Sem login.

## Critérios de aceite

| Código | Cenário | Resultado esperado |
|---|---|---|
| CA-01 | Inscrever em turma com vaga | Inscrição `CONFIRMADA` |
| CA-02 | Inscrever em turma lotada | Inscrição `ESPERA`, primeira da fila |
| CA-03 | Cancelar inscrição confirmada numa turma com fila de espera | A primeira da espera passa a `CONFIRMADA` |
| CA-04 | Inscrever o mesmo e-mail duas vezes na mesma turma | Segunda recusada |
| CA-05 | Inscrever 23 horas antes do início | Recusa |
| CA-06 | Cancelar inscrição depois do início da turma | Recusa |
| CA-07 | Marcar presença antes do início da turma | Recusa |
| CA-08 | Marcar presença de uma inscrição em `ESPERA` | Recusa |
| CA-09 | Consultar turmas futuras depois de lotar uma turma | Turma lotada aparece com 0 vagas restantes |
| CA-10 | Taxa de presença com 3 presentes e 1 ausente | 75% |
