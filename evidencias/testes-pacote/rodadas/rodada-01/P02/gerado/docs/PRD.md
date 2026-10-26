# PRD · Reembolso de despesas

## Problema
"O reembolso de despesas de viagem é por e-mail e planilha. A gente perde comprovante, paga duas vezes e não sabe quanto gastou no mês."

## Usuários
- Colaborador: lança a despesa informando quem é (sem login).
- Gestor: aprova ou recusa despesas.
- Financeiro: marca despesas aprovadas como pagas e consulta o resumo do mês.

## Objetivo
Controlar o ciclo lançamento → aprovação → pagamento das despesas de viagem, sem duplicidade e com resumo mensal. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Despesa | colaborador (nome, e-mail), data da despesa, categoria, valor em reais com centavos, descrição, número do comprovante, situação, motivo da recusa, criada em | categoria: TRANSPORTE, HOSPEDAGEM, ALIMENTACAO, OUTROS; situação: PENDENTE, APROVADA, RECUSADA, PAGA |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Lançar despesa com colaborador (nome e e-mail), data, categoria, valor, descrição e número do comprovante. |
| RF-02 | Aprovar despesa. |
| RF-03 | Recusar despesa informando o motivo. |
| RF-04 | Marcar despesa como paga. |
| RF-05 | Excluir despesa. |
| RF-06 | Consultar despesas com filtro por e-mail do colaborador e por situação; consultar uma despesa pelo identificador. |
| RF-07 | Emitir resumo de um mês: total por categoria e total geral. |
| RF-08 | Oferecer API REST para todas as operações. |
| RF-09 | Oferecer tela web simples para lançar, aprovar, recusar, pagar e ver o resumo do mês. |
| RF-10 | Guardar os dados em banco local, sem login; a pessoa informa quem é. |
| RF-11 | Começar com 5 despesas de exemplo: 2 PENDENTE, 1 APROVADA, 1 RECUSADA, 1 PAGA. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Valor maior que zero (R$ 0,00 é recusado), com no máximo 2 casas decimais. |
| RN-02 | Limite por despesa, inclusive: ALIMENTACAO até R$ 120,00; HOSPEDAGEM até R$ 450,00; TRANSPORTE e OUTROS até R$ 1.000,00. |
| RN-03 | Data da despesa não pode ser futura: hoje é aceito, amanhã é recusado. |
| RN-04 | Data da despesa não pode ter mais de 60 dias: hoje − 60 dias é aceito, hoje − 61 dias é recusado. |
| RN-05 | O mesmo número de comprovante não pode ser lançado duas vezes pelo mesmo colaborador (mesmo e-mail), em qualquer situação. |
| RN-06 | Toda despesa nasce PENDENTE. |
| RN-07 | Transições permitidas: PENDENTE → APROVADA, PENDENTE → RECUSADA, APROVADA → PAGA. Qualquer outra é recusada. |
| RN-08 | Recusar exige motivo não vazio (até 500 caracteres). |
| RN-09 | Só despesa PENDENTE pode ser excluída. |
| RN-10 | O resumo do mês considera a data da despesa e só as situações APROVADA e PAGA. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito; "hoje" é a data corrente nesse fuso. |
| PR-02 | Data da despesa é só data (dia), sem hora. |
| PR-03 | Colaborador é identificado pelo e-mail, comparado sem diferenciar maiúsculas; e-mail precisa ter formato válido. |
| PR-04 | Nome, descrição e número do comprovante são obrigatórios, não vazios, até 200 caracteres. |
| PR-05 | Não há edição de despesa; correção é feita excluindo (se PENDENTE) e lançando de novo. |
| PR-06 | A exclusão pedida remove a despesa PENDENTE de fato, pois o pedido a prevê explicitamente; demais situações mantêm histórico. |
| PR-07 | Totais em reais com 2 casas decimais, sem arredondamento (soma exata de centavos); categorias sem despesa aparecem com zero. |
| PR-08 | Mês informado como ano e mês; o mês vai do dia 1 ao último dia, inclusive. |
| PR-09 | Listagem ordenada pela data da despesa, da mais recente para a mais antiga, e depois pelo identificador. |
| PR-10 | Quem aprova, recusa ou paga não é identificado (sem login); registra-se a data e hora da última mudança. |
| PR-11 | As despesas de exemplo têm datas relativas ao dia em que o sistema inicia, dentro dos últimos 60 dias. |

## Fora de escopo
- Login, perfis de acesso e controle de quem aprova ou paga.
- Anexo do arquivo do comprovante (só o número).
- Edição de despesa, notificações e exportação.
- Deploy, integração com sistemas reais (folha, ERP, banco) e dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Lançar despesa válida | Despesa criada como PENDENTE | RF-01, RN-06 |
| CA-02 | Lançar ALIMENTACAO de R$ 120,01 | Recusa por limite | RN-02 |
| CA-03 | Lançar HOSPEDAGEM de R$ 450,00 | Despesa criada | RF-01, RN-02 |
| CA-04 | Lançar despesa com data de 61 dias atrás | Recusa | RN-04 |
| CA-05 | Lançar despesa com data de amanhã | Recusa | RN-03 |
| CA-06 | Lançar o mesmo comprovante duas vezes para o mesmo colaborador | Segunda recusada por duplicidade | RN-05 |
| CA-07 | Recusar despesa sem informar motivo | Recusa | RF-03, RN-08 |
| CA-08 | Marcar como paga uma despesa PENDENTE | Recusa por mudança de situação inválida | RF-04, RN-07 |
| CA-09 | Aprovar e depois pagar uma despesa | Despesa PAGA | RF-02, RF-04, RN-07 |
| CA-10 | Resumo de um mês com despesas RECUSADA e PENDENTE | Elas não entram nos totais | RF-07, RN-10 |
