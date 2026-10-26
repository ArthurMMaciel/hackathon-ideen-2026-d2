# PRD · Empréstimo de equipamentos

## Problema
"Temos notebooks, projetores e headsets que o pessoal pega emprestado e ninguém sabe com quem está. Já perdemos equipamento." Hoje não há registro de quem está com cada equipamento nem do que está atrasado.

## Usuários
- Responsável pelos equipamentos: cadastra equipamentos, registra empréstimos e devoluções, acompanha atrasos e o relatório mensal.

## Objetivo
Saber a qualquer momento o que está disponível, com quem está cada equipamento e o que está atrasado. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Equipamento | patrimônio (`EQ-0000`), tipo, descrição, situação | tipo: NOTEBOOK, PROJETOR, HEADSET; situação: DISPONIVEL, EMPRESTADO, MANUTENCAO |
| Empréstimo | equipamento, nome da pessoa, e-mail da pessoa, data de retirada, data prevista de devolução, data de devolução, defeito na devolução, status | status: ABERTO, DEVOLVIDO |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar equipamento com patrimônio, tipo e descrição; nasce na situação DISPONIVEL. |
| RF-02 | Listar todos os equipamentos e consultar um equipamento com sua situação. |
| RF-03 | Iniciar o sistema com 8 equipamentos: 3 NOTEBOOK, 2 PROJETOR e 3 HEADSET, sendo 1 HEADSET em MANUTENCAO. |
| RF-04 | Registrar empréstimo com equipamento, nome e e-mail da pessoa e data prevista de devolução; nasce ABERTO e o equipamento passa a EMPRESTADO. |
| RF-05 | Registrar devolução de um empréstimo, informando se há defeito; o empréstimo passa a DEVOLVIDO. |
| RF-06 | Consultar equipamentos disponíveis, com filtro opcional por tipo. |
| RF-07 | Consultar empréstimos atrasados com a quantidade de dias de atraso. |
| RF-08 | Listar empréstimos, com filtro opcional por status (a tela precisa dos abertos para "devolver"). |
| RF-09 | Gerar relatório de um mês com a quantidade de empréstimos por tipo de equipamento. |
| RF-10 | Oferecer API REST para todas as operações. |
| RF-11 | Oferecer uma tela web simples para emprestar, devolver e ver os atrasados. |
| RF-12 | Guardar os dados em banco local, sem login. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Patrimônio no formato `EQ-` seguido de exatamente 4 dígitos (EQ-0000 a EQ-9999) e único entre equipamentos. |
| RN-02 | Só equipamento DISPONIVEL pode ser emprestado; EMPRESTADO ou MANUTENCAO é recusado. |
| RN-03 | A data de retirada é o dia do registro ("hoje"). |
| RN-04 | Prazo máximo, contado da retirada: NOTEBOOK até 14 dias inclusive; PROJETOR e HEADSET até 3 dias inclusive. Prevista = retirada + 15 dias (notebook) ou + 4 dias (outros) é recusada. |
| RN-05 | A data prevista não pode ser anterior à retirada; igual à retirada (0 dias) é aceita. |
| RN-06 | Uma pessoa, identificada pelo e-mail, pode ter no máximo 2 empréstimos ABERTO; o terceiro é recusado. |
| RN-07 | A devolução registra a data de devolução (hoje) e encerra o empréstimo (DEVOLVIDO); só empréstimo ABERTO pode ser devolvido. |
| RN-08 | Devolução com defeito leva o equipamento a MANUTENCAO; sem defeito, a DISPONIVEL. |
| RN-09 | Atrasado: empréstimo ABERTO com data prevista anterior a hoje. Dias de atraso = hoje − data prevista, em dias inteiros (prevista ontem = 1). |
| RN-10 | Relatório do mês: conta empréstimos (ABERTO e DEVOLVIDO) cuja data de retirada cai entre o dia 1 e o último dia do mês, inclusive, agrupados por tipo; tipos sem empréstimo aparecem com 0. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito; datas de empréstimo são dias de calendário sem horário e "hoje" é a data local. |
| PR-02 | "Cadastro" de equipamento cobre criar, listar e consultar; editar e excluir não foram pedidos. |
| PR-03 | A situação do equipamento muda só por empréstimo e devolução; não há operação para tirar equipamento de MANUTENCAO. |
| PR-04 | E-mail é comparado sem diferença de maiúsculas e minúsculas e guardado em minúsculas; precisa ter formato `nome@dominio.ext`. |
| PR-05 | Nome, descrição e demais textos: obrigatórios, sem espaços nas pontas, até 200 caracteres. |
| PR-06 | Devolução em atraso é aceita normalmente; o atraso não gera multa nem bloqueio. |
| PR-07 | Listagens ordenadas por patrimônio (equipamentos) e por id de criação (empréstimos); atrasados do maior atraso para o menor. |
| PR-08 | Mês do relatório informado como ano e mês; meses sem empréstimo retornam todos os tipos com 0. |
| PR-09 | Os 8 equipamentos iniciais têm patrimônios EQ-0001 a EQ-0008 e descrições fictícias. |
| PR-10 | Empréstimos nunca são apagados; o histórico fica guardado. |

## Fora de escopo
- Login, perfis de acesso e cadastro de pessoas (o pedido diz "não precisa de login").
- Editar ou excluir equipamento e retirar equipamento de manutenção (PR-02, PR-03).
- Notificação de atraso, multa, reserva e renovação de empréstimo.
- Deploy, integração com sistema real e uso de dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Emprestar equipamento disponível com prazo dentro do limite | Empréstimo `ABERTO` e equipamento `EMPRESTADO` | RF-04, RN-02, RN-03, RN-04 |
| CA-02 | Emprestar equipamento já emprestado | Recusa | RN-02 |
| CA-03 | Emprestar equipamento em manutenção | Recusa | RN-02 |
| CA-04 | Emprestar notebook com devolução prevista para 15 dias depois | Recusa por prazo | RN-04 |
| CA-05 | Emprestar projetor com devolução prevista para 3 dias depois | Empréstimo criado | RF-04, RN-04 |
| CA-06 | Pessoa com 2 empréstimos em aberto pede um terceiro | Recusa | RN-06 |
| CA-07 | Devolver sem defeito | Empréstimo `DEVOLVIDO` e equipamento `DISPONIVEL` | RF-05, RN-07, RN-08 |
| CA-08 | Devolver com defeito | Equipamento `MANUTENCAO` | RF-05, RN-08 |
| CA-09 | Empréstimo com devolução prevista para ontem e ainda aberto | Aparece nos atrasados com 1 dia de atraso | RF-07, RN-09 |
| CA-10 | Devolver empréstimo já devolvido | Recusa | RN-07 |
