---
name: revisao
description: Etapa 4 da fábrica. Revisão de qualidade do sistema gerado em gerado/ contra PRD e SPEC, com achados classificados, correção dos achados altos e médios e nova rodada de testes. Grava evidencias/revisao.md. Use depois do gate da construção.
---

# Revisão de qualidade

Objetivo: encontrar o que a construção deixou passar e corrigir antes da verificação. Revise como alguém que não escreveu o código: compare o que existe com o PRD e a SPEC, não com a sua memória do que fez.

## Passo a passo

1. Rode `PY -m pytest -q` e registre o resultado como ponto de partida.
2. Percorra o checklist abaixo item por item, abrindo os arquivos. Cada problema vira um achado com: arquivo e linha, descrição, gravidade e regra ou requisito afetado.
3. Classifique:
   - **Alto:** comportamento diferente do PRD ou da SPEC, critério de aceite não coberto, erro 500 possível com entrada do usuário, perda de dado.
   - **Médio:** regra sem teste de borda, mensagem de erro fora do formato, código de domínio misturado com SQL ou HTTP, tela que não mostra erro.
   - **Baixo:** nome confuso, duplicação pequena, comentário faltando.
4. Corrija todos os altos e médios. Para cada correção que muda comportamento, acrescente ou ajuste um teste.
5. Rode a suíte de novo. Tudo precisa passar.
6. Grave `evidencias/revisao.md` com a tabela de achados (gravidade, descrição, arquivo, status `CORRIGIDO` ou `ACEITO` com motivo) e o resultado dos testes antes e depois.

## Checklist

**Aderência**
- [ ] Cada `RF` e `RN` do PRD está implementado como a SPEC descreve. Abra a tabela de rastreabilidade da SPEC e confira linha por linha.
- [ ] Os nomes de enums e status são exatamente os do pedido.
- [ ] A carga inicial cria exatamente o que o PRD pede.

**Testes**
- [ ] Todo `CA-xx` tem teste que confere status HTTP e o campo relevante do corpo, não só o status.
- [ ] Toda regra com limite tem teste no limite, abaixo e acima.
- [ ] Regras de tempo usam o `relogio` de teste; nenhum teste depende da hora real.

**Erros**
- [ ] Entradas inválidas comuns (campo faltando, tipo errado, id inexistente, data sem fuso) retornam 4xx, nunca 500. Teste pelo menos um caso de cada.
- [ ] Erros de negócio no formato `{"erro", "mensagem"}`, com mensagem em português.

**Estrutura**
- [ ] `app/dominio/` não importa FastAPI nem `sqlite3`.
- [ ] SQL só em `app/repositorio/` (e DDL em `app/banco.py`).
- [ ] Nenhum `datetime.now()` fora de `app/relogio.py`.
- [ ] Escritas que dependem de leitura estão dentro de `banco.transacao`.

**Tela**
- [ ] Executa as ações que a SPEC lista e mostra a mensagem de erro da API.
- [ ] Abre sem erro de JavaScript (confira se os IDs usados no script existem no HTML).

## Gate da revisão

- [ ] `evidencias/revisao.md` existe com a tabela de achados.
- [ ] Nenhum achado alto ou médio com status diferente de `CORRIGIDO`.
- [ ] `PY -m pytest -q` passa depois das correções; resultado registrado no log.
