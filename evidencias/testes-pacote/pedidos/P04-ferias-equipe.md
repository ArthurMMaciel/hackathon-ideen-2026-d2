# Pedido · Férias da equipe

## O pedido, como o cliente escreveu

"Os pedidos de férias chegam por mensagem e já aconteceu de metade do time sair junto. Queria um sistema para a pessoa pedir férias, o gestor aprovar sem deixar gente demais da mesma equipe fora ao mesmo tempo, e um calendário para ver quem está de férias. Não precisa de login."

## O que o sistema precisa fazer

**Colaboradores**
- Cadastro com nome, e-mail, equipe (`DADOS`, `PRODUTO`, `SUPORTE`) e saldo de dias de férias (30 por padrão).
- O sistema já começa com 9 colaboradores, 3 por equipe.

**Solicitações**
- Uma solicitação tem colaborador, data de início e data de fim (dias corridos, contando o primeiro e o último dia) e situação: `SOLICITADA`, `APROVADA`, `REPROVADA` ou `CANCELADA`.
- Período mínimo de 5 dias e máximo de 30 dias.
- O início precisa ter pelo menos 30 dias de antecedência em relação ao dia da solicitação.
- A quantidade de dias não pode passar do saldo disponível: saldo menos os dias já `SOLICITADA` ou `APROVADA`.
- O colaborador não pode ter duas solicitações `SOLICITADA` ou `APROVADA` com dias em comum.

**Aprovação**
- Só `SOLICITADA` pode ser aprovada ou reprovada.
- No máximo 1 pessoa de cada equipe com férias `APROVADA` em um mesmo dia. Aprovar uma solicitação que quebra essa regra é recusado.
- Ao aprovar, os dias saem do saldo.

**Cancelamento**
- Solicitação `SOLICITADA` ou `APROVADA` pode ser cancelada até o dia anterior ao início. Se estava aprovada, os dias voltam para o saldo.

**Consulta**
- Calendário de um mês: para cada dia, quem está de férias aprovadas, por equipe.
- Saldo de cada colaborador.

**Interface**
- API REST para todas as operações.
- Uma tela web simples para solicitar, aprovar, reprovar e ver o calendário do mês.
- Dados em banco local. Sem login.

## Critérios de aceite

| Código | Cenário | Resultado esperado |
|---|---|---|
| CA-01 | Solicitar 10 dias com 40 dias de antecedência | Solicitação `SOLICITADA` |
| CA-02 | Solicitar 4 dias | Recusa |
| CA-03 | Solicitar com início em 29 dias | Recusa por antecedência |
| CA-04 | Solicitar mais dias que o saldo disponível | Recusa |
| CA-05 | Aprovar solicitação válida | `APROVADA` e saldo reduzido |
| CA-06 | Aprovar segunda pessoa da mesma equipe com dias em comum | Recusa |
| CA-07 | Aprovar pessoa de outra equipe no mesmo período | Aprovada |
| CA-08 | Aprovar pessoa da mesma equipe com férias começando no dia seguinte ao fim das férias de outra | Aprovada |
| CA-09 | Cancelar solicitação aprovada antes do início | `CANCELADA` e saldo devolvido |
| CA-10 | Calendário do mês com solicitações `SOLICITADA` e `REPROVADA` | Só as aprovadas aparecem |
