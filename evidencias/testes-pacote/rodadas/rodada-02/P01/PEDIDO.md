# Pedido · Empréstimo de equipamentos

## O pedido, como o cliente escreveu

"Temos notebooks, projetores e headsets que o pessoal pega emprestado e ninguém sabe com quem está. Já perdemos equipamento. Queria um sistema simples: cadastro dos equipamentos, registrar empréstimo e devolução, saber o que está disponível e o que está atrasado. Não precisa de login."

## O que o sistema precisa fazer

**Equipamentos**
- Cadastro com patrimônio (código único no formato `EQ-0000`), tipo (`NOTEBOOK`, `PROJETOR`, `HEADSET`) e descrição.
- Situação do equipamento: `DISPONIVEL`, `EMPRESTADO` ou `MANUTENCAO`.
- O sistema já começa com 8 equipamentos: 3 notebooks, 2 projetores e 3 headsets, sendo um dos headsets em manutenção.

**Empréstimos**
- Um empréstimo tem equipamento, pessoa (nome e e-mail), data de retirada (o dia do registro) e data prevista de devolução.
- Só equipamento `DISPONIVEL` pode ser emprestado.
- Prazo máximo: 14 dias para notebook e 3 dias para projetor e headset, contados da retirada.
- A data prevista não pode ser anterior à retirada.
- Uma pessoa (identificada pelo e-mail) pode ter no máximo 2 empréstimos em aberto.
- Status do empréstimo: `ABERTO` ou `DEVOLVIDO`.

**Devolução**
- Registra a data da devolução e encerra o empréstimo.
- Se a devolução indicar defeito, o equipamento vai para `MANUTENCAO`. Senão, volta para `DISPONIVEL`.

**Consultas**
- Equipamentos disponíveis, com filtro opcional por tipo.
- Empréstimos atrasados: em aberto com data prevista anterior a hoje, com a quantidade de dias de atraso.

**Relatório**
- Para um mês: quantidade de empréstimos por tipo de equipamento (pela data de retirada).

**Interface**
- API REST para todas as operações.
- Uma tela web simples para emprestar, devolver e ver os atrasados.
- Dados em banco local. Sem login.

## Critérios de aceite

| Código | Cenário | Resultado esperado |
|---|---|---|
| CA-01 | Emprestar equipamento disponível com prazo dentro do limite | Empréstimo `ABERTO` e equipamento `EMPRESTADO` |
| CA-02 | Emprestar equipamento já emprestado | Recusa |
| CA-03 | Emprestar equipamento em manutenção | Recusa |
| CA-04 | Emprestar notebook com devolução prevista para 15 dias depois | Recusa por prazo |
| CA-05 | Emprestar projetor com devolução prevista para 3 dias depois | Empréstimo criado |
| CA-06 | Pessoa com 2 empréstimos em aberto pede um terceiro | Recusa |
| CA-07 | Devolver sem defeito | Empréstimo `DEVOLVIDO` e equipamento `DISPONIVEL` |
| CA-08 | Devolver com defeito | Equipamento `MANUTENCAO` |
| CA-09 | Empréstimo com devolução prevista para ontem e ainda aberto | Aparece nos atrasados com 1 dia de atraso |
| CA-10 | Devolver empréstimo já devolvido | Recusa |
