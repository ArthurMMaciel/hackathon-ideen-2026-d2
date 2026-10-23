# PRD · Chamados de suporte com prazo

## Problema
"O suporte interno atende pelo chat e a gente não sabe o que ficou parado nem se está cumprindo prazo." Falta registrar o chamado, quem assumiu, a solução e quantos estouraram o prazo.

## Usuários
- Equipe de suporte interno e solicitantes: abrir chamado, assumir, resolver, fechar, reabrir, ver a fila e o relatório de prazo.

## Objetivo
Controlar o ciclo de vida dos chamados e medir o cumprimento do prazo de resolução. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Chamado | título, descrição, solicitante (nome, e-mail), categoria, prioridade, situação, data e hora de abertura, prazo, responsável, solução, data e hora de resolução | categoria: ACESSO, HARDWARE, SOFTWARE; prioridade: BAIXA, MEDIA, ALTA, CRITICA; situação: ABERTO, EM_ATENDIMENTO, RESOLVIDO, FECHADO |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Abrir chamado com título, descrição, solicitante (nome e e-mail), categoria e prioridade; nasce `ABERTO` com data e hora de abertura e prazo. |
| RF-02 | Listar chamados e consultar um chamado pelo identificador. |
| RF-03 | Assumir chamado (`ABERTO` → `EM_ATENDIMENTO`) informando o responsável. |
| RF-04 | Resolver chamado (`EM_ATENDIMENTO` → `RESOLVIDO`) informando a solução. |
| RF-05 | Fechar chamado (`RESOLVIDO` → `FECHADO`). |
| RF-06 | Reabrir chamado (`RESOLVIDO` → `EM_ATENDIMENTO`). |
| RF-07 | Consultar a fila de chamados não resolvidos, ordenada pelo prazo, com a indicação `ATRASADO`. |
| RF-08 | Emitir relatório por período de resolução: por prioridade, quantidade de resolvidos e percentual dentro do prazo. |
| RF-09 | Oferecer API REST para todas as operações. |
| RF-10 | Oferecer uma tela web simples para abrir chamado, ver a fila e mudar a situação. |
| RF-11 | Guardar os dados em banco local, sem login. |
| RF-12 | Começar com 6 chamados de exemplo: 2 `ABERTO`, 1 `EM_ATENDIMENTO`, 2 `RESOLVIDO`, 1 `FECHADO`, cobrindo as 4 prioridades e as 3 categorias. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Prazo = abertura + horas corridas: `CRITICA` 4h, `ALTA` 8h, `MEDIA` 24h, `BAIXA` 72h. |
| RN-02 | O prazo é calculado na abertura e nunca muda, inclusive após reabertura. |
| RN-03 | Dentro do prazo quando a data e hora de resolução ≤ prazo (borda inclusiva); 1 minuto depois já é fora. |
| RN-04 | Assumir exige responsável não vazio. |
| RN-05 | Resolver exige solução não vazia e registra a data e hora da resolução. |
| RN-06 | Reabrir só até 7 dias (168h) depois da resolução, inclusive; depois disso é recusado. |
| RN-07 | Só valem as transições `ABERTO`→`EM_ATENDIMENTO`, `EM_ATENDIMENTO`→`RESOLVIDO`, `RESOLVIDO`→`FECHADO`, `RESOLVIDO`→`EM_ATENDIMENTO`; qualquer outra é recusada. |
| RN-08 | Na fila, `ATRASADO` quando o momento atual é posterior ao prazo (no exato prazo ainda não está atrasado). |
| RN-09 | Campos de texto obrigatórios não podem ser vazios; e-mail com formato `algo@dominio.ext`; categoria e prioridade só com os valores fixos. |
| RN-10 | Relatório: data final ≥ data inicial; ambas inclusivas, pelo dia local da data de resolução. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito. |
| PR-02 | A data e hora de abertura é o momento do registro; não é informada pelo usuário. |
| PR-03 | "Não resolvidos" na fila = `ABERTO` e `EM_ATENDIMENTO`; empate de prazo ordenado pela abertura. |
| PR-04 | Relatório conta chamados `RESOLVIDO` ou `FECHADO` cuja data de resolução está no período; lista as 4 prioridades, mesmo com zero. |
| PR-05 | Percentual dentro do prazo de 0 a 100, com 1 casa decimal; vazio quando não há resolvidos na prioridade. |
| PR-06 | Ao reabrir, a solução e a data de resolução anteriores são limpas; o responsável é mantido. |
| PR-07 | Cadastro de chamado cobre abrir, listar e consultar; não há edição nem exclusão (histórico preservado). |
| PR-08 | Não há unicidade de título; cada chamado tem identificador próprio. |
| PR-09 | Os chamados de exemplo têm datas relativas ao momento em que o sistema inicia com banco vazio. |
| PR-10 | Limites de texto: título até 200, descrição e solução até 2000, nomes até 100, e-mail até 200 caracteres. |

## Fora de escopo
- Login, perfis de acesso e notificações.
- Edição e exclusão de chamados, anexos, comentários.
- Calendário de horário comercial (o prazo é em horas corridas).
- Deploy, integração com o chat ou sistema real e dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Abrir chamado `ALTA` | Chamado `ABERTO` com prazo 8 horas depois da abertura | RF-01, RN-01 |
| CA-02 | Assumir chamado sem informar responsável | Recusa | RF-03, RN-04 |
| CA-03 | Resolver chamado `ABERTO` direto | Recusa | RF-04, RN-07 |
| CA-04 | Resolver chamado sem informar solução | Recusa | RF-04, RN-05 |
| CA-05 | Resolver chamado dentro do prazo | Conta como dentro do prazo no relatório | RF-08, RN-03 |
| CA-06 | Resolver chamado `CRITICA` 4 horas e 1 minuto depois da abertura | Conta como fora do prazo | RF-08, RN-01, RN-03 |
| CA-07 | Consultar a fila com um chamado de prazo vencido | Chamado aparece como `ATRASADO` | RF-07, RN-08 |
| CA-08 | Reabrir chamado resolvido há 6 dias | Chamado `EM_ATENDIMENTO` | RF-06, RN-06 |
| CA-09 | Reabrir chamado resolvido há 8 dias | Recusa | RF-06, RN-06 |
| CA-10 | Fechar chamado `ABERTO` | Recusa | RF-05, RN-07 |
