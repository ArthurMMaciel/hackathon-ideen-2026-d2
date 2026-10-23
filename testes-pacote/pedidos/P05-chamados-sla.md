# Pedido · Chamados de suporte com prazo

## O pedido, como o cliente escreveu

"O suporte interno atende pelo chat e a gente não sabe o que ficou parado nem se está cumprindo prazo. Queria abrir chamado, alguém assumir, resolver, e saber quantos estouraram o prazo. Não precisa de login."

## O que o sistema precisa fazer

**Chamados**
- Um chamado tem título, descrição, solicitante (nome e e-mail), categoria (`ACESSO`, `HARDWARE`, `SOFTWARE`), prioridade (`BAIXA`, `MEDIA`, `ALTA`, `CRITICA`), situação e data e hora de abertura.
- Situações: `ABERTO`, `EM_ATENDIMENTO`, `RESOLVIDO`, `FECHADO`.
- O sistema já começa com 6 chamados de exemplo.

**Prazo**
- Prazo de resolução em horas corridas desde a abertura: `CRITICA` 4h, `ALTA` 8h, `MEDIA` 24h, `BAIXA` 72h.
- O prazo é calculado na abertura e não muda.
- Um chamado está dentro do prazo se foi resolvido até o prazo, inclusive.

**Fluxo**
- `ABERTO` → `EM_ATENDIMENTO`: exige o nome do responsável.
- `EM_ATENDIMENTO` → `RESOLVIDO`: exige a descrição da solução e registra a data e hora da resolução.
- `RESOLVIDO` → `FECHADO`.
- `RESOLVIDO` → `EM_ATENDIMENTO` (reabrir): só até 7 dias depois da resolução. O prazo original continua valendo.
- Qualquer outra mudança é recusada.

**Fila**
- Chamados não resolvidos, ordenados pelo prazo, com a indicação `ATRASADO` quando o prazo já passou.

**Relatório**
- Para um período (data inicial e final, pela data de resolução): por prioridade, quantidade de chamados resolvidos e percentual dentro do prazo.

**Interface**
- API REST para todas as operações.
- Uma tela web simples para abrir chamado, ver a fila e mudar a situação.
- Dados em banco local. Sem login.

## Critérios de aceite

| Código | Cenário | Resultado esperado |
|---|---|---|
| CA-01 | Abrir chamado `ALTA` | Chamado `ABERTO` com prazo 8 horas depois da abertura |
| CA-02 | Assumir chamado sem informar responsável | Recusa |
| CA-03 | Resolver chamado `ABERTO` direto | Recusa |
| CA-04 | Resolver chamado sem informar solução | Recusa |
| CA-05 | Resolver chamado dentro do prazo | Conta como dentro do prazo no relatório |
| CA-06 | Resolver chamado `CRITICA` 4 horas e 1 minuto depois da abertura | Conta como fora do prazo |
| CA-07 | Consultar a fila com um chamado de prazo vencido | Chamado aparece como `ATRASADO` |
| CA-08 | Reabrir chamado resolvido há 6 dias | Chamado `EM_ATENDIMENTO` |
| CA-09 | Reabrir chamado resolvido há 8 dias | Recusa |
| CA-10 | Fechar chamado `ABERTO` | Recusa |
