# Pedido · Reembolso de despesas

## O pedido, como o cliente escreveu

"O reembolso de despesas de viagem é por e-mail e planilha. A gente perde comprovante, paga duas vezes e não sabe quanto gastou no mês. Queria um sistema simples para a pessoa lançar a despesa, o gestor aprovar ou recusar e o financeiro marcar como paga, com um resumo do mês. Sem login por enquanto: a pessoa informa quem é."

## O que o sistema precisa fazer

**Despesas**
- Uma despesa tem colaborador (nome e e-mail), data da despesa, categoria (`TRANSPORTE`, `HOSPEDAGEM`, `ALIMENTACAO`, `OUTROS`), valor em reais com centavos, descrição e número do comprovante.
- O valor precisa ser maior que zero.
- Limite por despesa: `ALIMENTACAO` até R$ 120,00; `HOSPEDAGEM` até R$ 450,00; `TRANSPORTE` e `OUTROS` até R$ 1.000,00.
- A data da despesa não pode ser futura nem ter mais de 60 dias.
- O mesmo número de comprovante não pode ser lançado duas vezes pelo mesmo colaborador.
- O sistema já começa com 5 despesas de exemplo em situações diferentes.

**Fluxo**
- Toda despesa nasce `PENDENTE`.
- `PENDENTE` pode ir para `APROVADA` ou `RECUSADA`. Recusar exige um motivo.
- `APROVADA` pode ir para `PAGA`.
- Qualquer outra mudança de situação é recusada.
- Só despesa `PENDENTE` pode ser excluída.

**Consulta**
- Despesas com filtro por e-mail do colaborador e por situação.

**Relatório**
- Para um mês (pela data da despesa): total por categoria e total geral, considerando só despesas `APROVADA` e `PAGA`.

**Interface**
- API REST para todas as operações.
- Uma tela web simples para lançar despesa, aprovar, recusar, pagar e ver o resumo do mês.
- Dados em banco local. Sem login.

## Critérios de aceite

| Código | Cenário | Resultado esperado |
|---|---|---|
| CA-01 | Lançar despesa válida | Despesa criada como `PENDENTE` |
| CA-02 | Lançar `ALIMENTACAO` de R$ 120,01 | Recusa por limite |
| CA-03 | Lançar `HOSPEDAGEM` de R$ 450,00 | Despesa criada |
| CA-04 | Lançar despesa com data de 61 dias atrás | Recusa |
| CA-05 | Lançar despesa com data de amanhã | Recusa |
| CA-06 | Lançar o mesmo comprovante duas vezes para o mesmo colaborador | Segunda recusada por duplicidade |
| CA-07 | Recusar despesa sem informar motivo | Recusa |
| CA-08 | Marcar como paga uma despesa `PENDENTE` | Recusa por mudança de situação inválida |
| CA-09 | Aprovar e depois pagar uma despesa | Despesa `PAGA` |
| CA-10 | Resumo de um mês com despesas `RECUSADA` e `PENDENTE` | Elas não entram nos totais |
