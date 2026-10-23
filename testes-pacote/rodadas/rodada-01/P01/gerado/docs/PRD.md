# PRD · Empréstimo de equipamentos

## Problema
"Temos notebooks, projetores e headsets que o pessoal pega emprestado e ninguém sabe com quem está. Já perdemos equipamento."

## Usuários
- Pessoa responsável pelos equipamentos: cadastra, registra empréstimo e devolução, acompanha disponíveis e atrasados.

## Objetivo
Saber a qualquer momento com quem está cada equipamento, o que está disponível e o que está atrasado. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Equipamento | patrimônio, tipo, descrição, situação | tipo: NOTEBOOK, PROJETOR, HEADSET; situação: DISPONIVEL, EMPRESTADO, MANUTENCAO |
| Empréstimo | equipamento, nome, e-mail, data de retirada, data prevista de devolução, data de devolução, defeito, status | status: ABERTO, DEVOLVIDO |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar equipamento com patrimônio, tipo e descrição; novo equipamento nasce DISPONIVEL. |
| RF-02 | Listar e consultar equipamentos com sua situação. |
| RF-03 | Registrar empréstimo de um equipamento para uma pessoa (nome e e-mail) com data prevista de devolução. |
| RF-04 | Registrar devolução, informando se houve defeito; encerra o empréstimo. |
| RF-05 | Consultar equipamentos disponíveis, com filtro opcional por tipo. |
| RF-06 | Consultar empréstimos atrasados com a quantidade de dias de atraso. |
| RF-07 | Gerar relatório de um mês com a quantidade de empréstimos por tipo de equipamento. |
| RF-08 | Listar empréstimos, com filtro opcional por status. |
| RF-09 | Oferecer API REST para todas as operações. |
| RF-10 | Oferecer tela web simples para emprestar, devolver e ver os atrasados. |
| RF-11 | Guardar os dados em banco local, sem login. |
| RF-12 | Começar com 8 equipamentos: 3 NOTEBOOK, 2 PROJETOR e 3 HEADSET, um dos headsets em MANUTENCAO. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Patrimônio no formato EQ-0000 (EQ, hífen, exatamente 4 dígitos) e único entre equipamentos. |
| RN-02 | Só equipamento DISPONIVEL pode ser emprestado. |
| RN-03 | Data de retirada é o dia do registro do empréstimo (data de hoje). |
| RN-04 | Prazo máximo, em dias corridos da retirada até a data prevista, inclusive: NOTEBOOK 14; PROJETOR e HEADSET 3. |
| RN-05 | Data prevista não pode ser anterior à retirada; igual à retirada é aceita (prazo 0). |
| RN-06 | Uma pessoa (e-mail) pode ter no máximo 2 empréstimos ABERTO; o 3º é recusado. |
| RN-07 | Empréstimo registrado nasce ABERTO e o equipamento passa a EMPRESTADO. |
| RN-08 | Devolução grava a data de devolução (hoje) e muda o empréstimo para DEVOLVIDO. |
| RN-09 | Devolução com defeito leva o equipamento a MANUTENCAO; sem defeito, a DISPONIVEL. |
| RN-10 | Só empréstimo ABERTO pode ser devolvido. |
| RN-11 | Atrasado: ABERTO com data prevista anterior a hoje; dias de atraso = hoje menos data prevista (mínimo 1). |
| RN-12 | Relatório conta empréstimos com data de retirada dentro do mês civil informado, de qualquer status, por tipo. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito; "hoje" é a data civil nesse fuso. |
| PR-02 | Datas de empréstimo são datas de calendário, sem hora. |
| PR-03 | Cadastro cobre criar, listar e consultar; editar e excluir equipamento ficam fora (histórico preservado). |
| PR-04 | E-mail identifica a pessoa sem diferenciar maiúsculas de minúsculas e é validado por formato simples (texto@texto.texto). |
| PR-05 | Nome, e-mail e descrição obrigatórios, sem texto vazio, até 200 caracteres. |
| PR-06 | A data de retirada não é informada: o sistema usa o dia do registro. A devolução também usa o dia do registro. |
| PR-07 | Relatório traz os 3 tipos, com zero quando não houver empréstimo no mês. |
| PR-08 | Equipamentos ordenados por patrimônio; empréstimos por data de retirada e depois por ordem de registro; atrasados do maior atraso para o menor. |
| PR-09 | Saída de MANUTENCAO não foi pedida: o equipamento permanece em MANUTENCAO. |

## Fora de escopo
- Login, perfis de acesso e cadastro de pessoas (o pedido diz "não precisa de login").
- Editar ou excluir equipamento e liberar equipamento de manutenção.
- Notificação de atraso, renovação de prazo, reserva antecipada.
- Deploy, integração com sistema real e dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Emprestar equipamento disponível com prazo dentro do limite | Empréstimo ABERTO e equipamento EMPRESTADO | RF-03, RN-02, RN-04, RN-07 |
| CA-02 | Emprestar equipamento já emprestado | Recusa | RN-02 |
| CA-03 | Emprestar equipamento em manutenção | Recusa | RN-02, RF-12 |
| CA-04 | Emprestar notebook com devolução prevista para 15 dias depois | Recusa por prazo | RN-04 |
| CA-05 | Emprestar projetor com devolução prevista para 3 dias depois | Empréstimo criado | RN-04 |
| CA-06 | Pessoa com 2 empréstimos em aberto pede um terceiro | Recusa | RN-06 |
| CA-07 | Devolver sem defeito | Empréstimo DEVOLVIDO e equipamento DISPONIVEL | RF-04, RN-08, RN-09 |
| CA-08 | Devolver com defeito | Equipamento MANUTENCAO | RF-04, RN-09 |
| CA-09 | Empréstimo com devolução prevista para ontem e ainda aberto | Aparece nos atrasados com 1 dia de atraso | RF-06, RN-11 |
| CA-10 | Devolver empréstimo já devolvido | Recusa | RN-10 |
