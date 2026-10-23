---
name: especificacao
description: Etapa 2 da fábrica. Transforma o PRD (gerado/docs/PRD.md) numa especificação técnica (gerado/docs/SPEC.md) com modelo de dados, contrato de cada endpoint, códigos de erro, tela e plano de testes que liga cada CA-xx e RN-xx a um teste nomeado. Use depois do gate da concepção e antes de escrever qualquer código.
---

# Especificação · contrato do que será construído

Objetivo: decidir como o PRD vira sistema, com detalhe suficiente para a construção não precisar inventar nada. Cada decisão aponta para um código do PRD.

Leia antes: `../fabrica/referencias/regras-transversais.md`, `../fabrica/referencias/stack-padrao.md` e o arquivo `gerado/docs/PRD.md`.

## Entrada e saída

- **Entrada:** `gerado/docs/PRD.md`.
- **Saída:** `gerado/docs/SPEC.md`, no formato de [modelo-spec.md](modelo-spec.md).

## Passo a passo

1. **Modelo de dados.** Uma tabela SQL por entidade do PRD: colunas, tipos SQLite, `NOT NULL`, `UNIQUE`, `CHECK` e chaves estrangeiras. Datas em `TEXT` UTC. Listas pequenas de valores fixos (ex.: recursos) podem ir numa coluna `TEXT` com JSON ou numa tabela de ligação; escolha a mais simples para as consultas que o PRD pede. Escreva o DDL completo; ele vai direto para `banco.ESQUEMA`.
2. **Carga inicial.** Se o PRD pede dados iniciais, liste-os aqui, linha a linha, com valores fictícios.
3. **Contrato da API.** Todos os caminhos começam com `/api`. Recursos no plural. Para cada endpoint:
   - método e caminho;
   - entrada: corpo JSON ou parâmetros de consulta, com tipo, obrigatoriedade e limites;
   - saída de sucesso: status e exemplo de corpo JSON;
   - erros: status, código `ERRO` em maiúsculas e a regra (`RN-xx`) que o dispara.

   Todo `RF` que fala de operação precisa de pelo menos um endpoint. Ações que mudam estado sem criar recurso usam `POST /api/<recursos>/{id}/<acao>` (ex.: `/cancelar`).
4. **Formatos.** Datas e horas em ISO 8601 com offset. Horário sem fuso é recusado com `422`. Valores calculados com unidade e arredondamento definidos pela `PR` correspondente.
5. **Regras de negócio no código.** Para cada `RN-xx`: a função de `app/dominio/` que a implementa e o código de erro que ela levanta. As funções de domínio recebem `agora` como parâmetro quando a regra depende do tempo.
6. **Tela.** O que a tela mostra, quais ações oferece e quais endpoints chama. Uma página só. Mensagens de erro da API aparecem para o usuário.
7. **Plano de testes.** Uma tabela com uma linha por teste:
   - um teste por `CA-xx`, nomeado `test_ca_XX_<resumo>`;
   - testes de borda para cada `RN-xx` com limite numérico, nomeados `test_rn_XX_<resumo>` (o valor no limite, um abaixo, um acima);
   - para cada linha: dados de entrada, horário do relógio de teste e resultado esperado (status e campo conferido).

   Cenários que dependem de o tempo passar usam `relogio.avancar()` (testes) ou reinício do servidor com outro `APP_AGORA` (verificação).
8. **Confira o gate.**

## O que não fazer

- Não acrescente endpoint, campo ou tela que nenhum `RF` pede.
- Não deixe "a definir". Se faltar informação, decida, registre a decisão no log e siga.
- Não escreva código de aplicação nesta etapa. O DDL entra como texto na especificação.

## Gate da especificação

- [ ] `gerado/docs/SPEC.md` existe com as seções de [modelo-spec.md](modelo-spec.md).
- [ ] Todo `RF-xx` do PRD aparece na tabela de rastreabilidade com endpoint, tela ou carga inicial.
- [ ] Todo `RN-xx` aparece com a função de domínio e o código de erro.
- [ ] Todo endpoint tem método, caminho, entrada, saída de sucesso e erros.
- [ ] Todo `CA-xx` tem pelo menos um teste nomeado `test_ca_XX_...` no plano de testes.
- [ ] Toda `RN-xx` com limite numérico tem teste de borda no plano.
- [ ] O DDL está completo e usa apenas tipos SQLite.
