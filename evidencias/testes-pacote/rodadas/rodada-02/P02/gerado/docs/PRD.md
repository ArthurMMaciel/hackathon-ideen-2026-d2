# PRD · Reembolso de despesas

## Problema
O reembolso de despesas de viagem é feito "por e-mail e planilha": a empresa perde comprovante, paga duas vezes e não sabe quanto gastou no mês.

## Usuários
- Colaborador: lança a despesa informando quem é (nome e e-mail), sem login.
- Gestor: aprova ou recusa despesas pendentes.
- Financeiro: marca despesas aprovadas como pagas e consulta o resumo do mês.

## Objetivo
Um sistema simples que leva a despesa do lançamento ao pagamento e mostra o total do mês. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Despesa | colaborador (nome, e-mail), data da despesa, categoria, valor em reais com centavos, descrição, número do comprovante, situação, motivo da recusa | categoria: TRANSPORTE, HOSPEDAGEM, ALIMENTACAO, OUTROS; situação: PENDENTE, APROVADA, RECUSADA, PAGA |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Lançar despesa com nome e e-mail do colaborador, data, categoria, valor, descrição e número do comprovante. |
| RF-02 | Aprovar despesa. |
| RF-03 | Recusar despesa informando um motivo. |
| RF-04 | Marcar despesa como paga. |
| RF-05 | Excluir despesa. |
| RF-06 | Consultar despesas com filtro opcional por e-mail do colaborador e por situação. |
| RF-07 | Emitir resumo de um mês: total por categoria e total geral. |
| RF-08 | Começar com 5 despesas de exemplo fictícias, cobrindo as 4 situações (PENDENTE, APROVADA, RECUSADA, PAGA). |
| RF-09 | Oferecer "API REST para todas as operações". |
| RF-10 | Oferecer "uma tela web simples para lançar despesa, aprovar, recusar, pagar e ver o resumo do mês", com a lista de despesas que essas ações exigem (RF-06). |
| RF-11 | Guardar os dados "em banco local", "sem login": a pessoa informa quem é. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Valor maior que zero: mínimo R$ 0,01; R$ 0,00 é recusado. |
| RN-02 | Limite por despesa, inclusive: ALIMENTACAO até R$ 120,00; HOSPEDAGEM até R$ 450,00; TRANSPORTE e OUTROS até R$ 1.000,00. Um centavo acima é recusado. |
| RN-03 | Data da despesa não pode ser futura: até hoje, inclusive; amanhã é recusado. |
| RN-04 | Data da despesa com no máximo 60 dias: hoje menos 60 dias é aceito; hoje menos 61 dias é recusado. |
| RN-05 | O mesmo número de comprovante não pode ser lançado duas vezes pelo mesmo colaborador. |
| RN-06 | Toda despesa nasce PENDENTE. |
| RN-07 | Mudanças de situação permitidas: PENDENTE→APROVADA, PENDENTE→RECUSADA, APROVADA→PAGA. Qualquer outra é recusada. |
| RN-08 | Recusar exige motivo não vazio. |
| RN-09 | Só despesa PENDENTE pode ser excluída. |
| RN-10 | O resumo do mês considera só despesas APROVADA e PAGA cuja data da despesa cai no mês. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito. |
| PR-02 | Data da despesa é data de calendário sem horário; "hoje" é a data atual no fuso de PR-01. |
| PR-03 | O colaborador é identificado pelo e-mail, comparado sem diferenciar maiúsculas de minúsculas; o nome é só informativo. |
| PR-04 | Duplicidade (RN-05) vale contra qualquer despesa existente do colaborador, inclusive RECUSADA; despesa excluída libera o comprovante. Comprovante comparado sem espaços nas pontas. |
| PR-05 | Valores com precisão de centavo, sem arredondamento; o resumo soma valores exatos. |
| PR-06 | Não há edição de despesa (não pedida); "excluir" remove o registro, como o pedido manda, prevalecendo sobre a regra de manter histórico. |
| PR-07 | Listagem ordenada pela data da despesa, mais recente primeiro; empate pelo lançamento mais recente. |
| PR-08 | "Mês" é o mês civil (do dia 1 ao último dia, inclusive) da data da despesa; o resumo mostra as 4 categorias, com zero quando não houver valor. |
| PR-09 | As regras de data (RN-03, RN-04) valem só no lançamento; aprovar ou pagar uma despesa antiga continua permitido. |
| PR-10 | Nome, descrição, comprovante e motivo são textos não vazios de até 200 caracteres; e-mail em formato válido. |
| PR-11 | Quem aprova, recusa ou paga não é identificado (sem login e o pedido não exige registrar). |
| PR-12 | Ao recusar sem motivo uma despesa que nem poderia ser recusada, prevalece a recusa por falta de motivo (RN-08 é conferida antes de RN-07). |

## Fora de escopo
- Login, perfis de acesso e autenticação (o pedido diz "sem login por enquanto").
- Anexo do arquivo do comprovante; só o número é guardado.
- Edição de despesa, notificações e exportação.
- Deploy, integração com sistema real (folha, ERP, banco) e dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Lançar despesa válida | Despesa criada como `PENDENTE` | RF-01, RN-06 |
| CA-02 | Lançar `ALIMENTACAO` de R$ 120,01 | Recusa por limite | RF-01, RN-02 |
| CA-03 | Lançar `HOSPEDAGEM` de R$ 450,00 | Despesa criada | RF-01, RN-02 |
| CA-04 | Lançar despesa com data de 61 dias atrás | Recusa | RF-01, RN-04 |
| CA-05 | Lançar despesa com data de amanhã | Recusa | RF-01, RN-03 |
| CA-06 | Lançar o mesmo comprovante duas vezes para o mesmo colaborador | Segunda recusada por duplicidade | RF-01, RN-05 |
| CA-07 | Recusar despesa sem informar motivo | Recusa | RF-03, RN-08 |
| CA-08 | Marcar como paga uma despesa `PENDENTE` | Recusa por mudança de situação inválida | RF-04, RN-07 |
| CA-09 | Aprovar e depois pagar uma despesa | Despesa `PAGA` | RF-02, RF-04, RN-07 |
| CA-10 | Resumo de um mês com despesas `RECUSADA` e `PENDENTE` | Elas não entram nos totais | RF-07, RN-10 |
