# PRD · Chamados de suporte com prazo

## Problema
"O suporte interno atende pelo chat e a gente não sabe o que ficou parado nem se está cumprindo prazo." Hoje não há registro de quem assumiu, do que está atrasado nem de quantos chamados estouraram o prazo.

## Usuários
- Solicitantes internos: abrem chamados.
- Atendentes do suporte: assumem, resolvem, fecham e reabrem chamados, acompanham a fila e o relatório de prazo.

## Objetivo
Registrar o ciclo de vida de cada chamado com prazo de resolução e medir o cumprimento desse prazo. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Chamado | título, descrição, solicitante (nome, e-mail), categoria, prioridade, situação, abertura (data e hora), prazo (data e hora), responsável, solução, resolução (data e hora) | categoria: ACESSO, HARDWARE, SOFTWARE; prioridade: BAIXA, MEDIA, ALTA, CRITICA; situação: ABERTO, EM_ATENDIMENTO, RESOLVIDO, FECHADO |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Abrir chamado com título, descrição, solicitante (nome e e-mail), categoria e prioridade; nasce `ABERTO` com abertura e prazo registrados. |
| RF-02 | Consultar um chamado e listar todos os chamados (a tela precisa deles para fechar e reabrir os resolvidos). |
| RF-03 | Assumir chamado (`ABERTO` → `EM_ATENDIMENTO`) informando o responsável. |
| RF-04 | Resolver chamado (`EM_ATENDIMENTO` → `RESOLVIDO`) informando a solução. |
| RF-05 | Fechar chamado (`RESOLVIDO` → `FECHADO`). |
| RF-06 | Reabrir chamado (`RESOLVIDO` → `EM_ATENDIMENTO`). |
| RF-07 | Consultar a fila: chamados não resolvidos, ordenados pelo prazo, com a indicação `ATRASADO` quando o prazo já passou. |
| RF-08 | Emitir relatório de um período (data inicial e final, pela data de resolução): por prioridade, quantidade de resolvidos e percentual dentro do prazo. |
| RF-09 | Oferecer API REST para todas as operações. |
| RF-10 | Oferecer uma tela web simples para abrir chamado, ver a fila e mudar a situação. |
| RF-11 | Guardar os dados em banco local, sem login. |
| RF-12 | Começar com 6 chamados de exemplo. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Prazo = abertura + horas corridas da prioridade: CRITICA 4h, ALTA 8h, MEDIA 24h, BAIXA 72h. |
| RN-02 | O prazo é calculado na abertura e não muda depois (nem ao reabrir). |
| RN-03 | Dentro do prazo: resolução ≤ prazo (inclusive). Resolução 1 minuto depois do prazo já está fora. |
| RN-04 | Assumir exige o nome do responsável (não vazio). |
| RN-05 | Resolver exige a descrição da solução (não vazia) e registra a data e hora da resolução. |
| RN-06 | Reabrir só até 7 dias (168h) depois da resolução, inclusive; 7 dias e 1 minuto já é recusado. |
| RN-07 | Só valem as transições `ABERTO`→`EM_ATENDIMENTO`, `EM_ATENDIMENTO`→`RESOLVIDO`, `RESOLVIDO`→`FECHADO`, `RESOLVIDO`→`EM_ATENDIMENTO`; qualquer outra é recusada. |
| RN-08 | Atrasado na fila: agora > prazo (no instante exato do prazo ainda não está atrasado). |
| RN-09 | Relatório: data inicial ≤ data final; período fechado, contando o primeiro e o último dia. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito. |
| PR-02 | A abertura é o momento em que o sistema registra o chamado; o usuário não informa a data de abertura. |
| PR-03 | "Não resolvidos" na fila são os chamados `ABERTO` e `EM_ATENDIMENTO`. Ordem: prazo crescente; empate pelo número do chamado. |
| PR-04 | Chamados resolvidos no relatório são os `RESOLVIDO` e `FECHADO` cuja resolução cai no período. O dia da resolução é o dia no fuso de PR-01. |
| PR-05 | Percentual dentro do prazo = no prazo ÷ resolvidos × 100, arredondado a 1 casa decimal (meio para cima); sem resolvidos na prioridade, quantidade 0 e percentual vazio. O relatório traz sempre as 4 prioridades, de CRITICA a BAIXA. |
| PR-06 | Ao reabrir, o chamado volta a `EM_ATENDIMENTO` com o mesmo responsável; solução e resolução anteriores são apagadas e uma nova resolução as registra de novo. A janela de 7 dias conta da resolução mais recente. |
| PR-07 | Cadastro de chamado cobre abrir, consultar e listar. Editar dados e excluir chamado não foram pedidos. |
| PR-08 | Títulos, nomes e responsável: 1 a 200 caracteres sem espaços nas pontas; descrição e solução: até 2000. E-mail no formato nome@dominio.ext. Títulos repetidos são permitidos. |
| PR-09 | A lista geral de chamados é ordenada pelo número do chamado, do mais recente para o mais antigo. |
| PR-10 | Os 6 chamados de exemplo cobrem as quatro situações e as quatro prioridades, com pelo menos um atrasado na fila; datas relativas ao momento em que o sistema inicia. |
| PR-11 | Ao resolver um chamado que não está `EM_ATENDIMENTO`, a recusa é pela transição inválida, mesmo sem solução informada. |

## Fora de escopo
- Login, perfis de acesso e controle de quem pode mudar a situação.
- Editar ou excluir chamados; anexos; comentários; notificações.
- Horário comercial, feriados ou pausa de prazo.
- Deploy, integração com o chat ou outro sistema real, e dados reais.

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
