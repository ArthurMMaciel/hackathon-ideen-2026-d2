# Revisão de qualidade

**Testes antes:** `49 passed, 1 warning`
**Testes depois:** `51 passed, 1 warning`

## Checklist

| Item | Como foi verificado | Resultado |
|---|---|---|
| Cada RF/RN implementado como a SPEC | Tabela de rastreabilidade da SPEC conferida linha a linha contra `app/rotas/*.py` e `app/dominio/ferias.py` | OK |
| Enums e status com os nomes do pedido | `DADOS/PRODUTO/SUPORTE`, `SOLICITADA/APROVADA/REPROVADA/CANCELADA` no DDL (`CHECK`) e nos `Literal` | OK |
| Carga inicial exata | `test_rf_03_carga_inicial_9_colaboradores` (9, 3 por equipe, saldo 30) e `test_rf_03_carga_inicial_idempotente` | OK |
| CA testa status e corpo | `tests/test_criterios_aceite.py`: todos conferem `situacao`, `erro`, `saldo` ou nomes do calendário | OK |
| Limites com no limite, abaixo e acima | RN-02 (4/5/30/31), RN-03 (29/30/31), RN-04 (9/10/11), RN-09 (véspera/dia), RN-11 (−1/0/365/366) | OK |
| Regras de tempo com relógio de teste | Fixture `relogio`; `test_rn_09_bordas_cancelamento` e `test_rn_03_hoje_no_fuso_de_sao_paulo` usam `avancar()` | OK |
| Entradas inválidas → 4xx | `test_entradas_invalidas_retornam_422`, `test_erros_404`, `test_data_inexistente_retorna_422`; teste manual com ids enormes revelou A-01 | Corrigido (A-01) |
| Erros de negócio `{"erro","mensagem"}` em português | `app/erros.py`; mensagens em `app/dominio/ferias.py` | OK |
| `app/dominio/` sem FastAPI e sem sqlite3 | `grep "^from\|^import" app/dominio/*.py`: só stdlib e `app.erros` | OK (ver B-01) |
| SQL só em repositório/banco | `grep -rnE "execute|SELECT|INSERT|UPDATE" app` fora de `repositorio/` e `banco.py`: nada | OK |
| Nenhum `datetime.now()` fora de `relogio.py` | `grep -rn datetime.now app/` | OK |
| Escritas dependentes de leitura em `banco.transacao` | `solicitar`, `aprovar`, `reprovar`, `cancelar`, `criar` colaborador | OK |
| Tela executa ações e mostra erro | Botões Solicitar/Aprovar/Reprovar/Cancelar e calendário; `mostrar(e.message, true)` em todos os `catch` | OK |
| IDs do script existem no HTML | 10 `getElementById` comparados com 10 `id=` | OK |

## Achados

| # | Gravidade | Descrição | Arquivo | Regra | Status |
|---|---|---|---|---|---|
| A-01 | Alto | Id maior que o inteiro de 64 bits do SQLite (ex.: `99999999999999999999`) no caminho, na consulta ou no corpo gerava `OverflowError` e HTTP 500 | `app/rotas/colaboradores.py`, `app/rotas/solicitacoes.py` | Erros da API | CORRIGIDO: `Path/Query/Field(ge=1, le=2147483647)`; teste `test_ids_enormes_nao_causam_erro_500` |
| M-01 | Médio | Data inexistente (`2030-02-30`) sem teste | `tests/test_regras.py` | Validação | CORRIGIDO: `test_data_inexistente_retorna_422` (já retornava 422) |
| B-01 | Baixo | `app/dominio/` importa `app.erros`, que importa `fastapi` (`Request`, `JSONResponse`). Não há import direto, mas o domínio depende indiretamente do framework | `app/erros.py` (do modelo de projeto) | Estrutura | ACEITO: o modelo da fábrica define os erros assim e manda o domínio levantar `regra_violada`/`conflito` |
| B-02 | Baixo | Em `POST /api/solicitacoes`, duração e antecedência são validadas antes de conferir se o colaborador existe; colaborador inexistente com período inválido devolve 422 em vez de 404 | `app/rotas/solicitacoes.py` | — | ACEITO: ambos são recusas corretas; ordem não afeta critério |
| B-03 | Baixo | `mes` com mais de 7 caracteres devolve 422 padrão do framework, não `MES_INVALIDO` | `app/rotas/solicitacoes.py` | RF-09 | ACEITO: continua 422 e sem stack trace |
