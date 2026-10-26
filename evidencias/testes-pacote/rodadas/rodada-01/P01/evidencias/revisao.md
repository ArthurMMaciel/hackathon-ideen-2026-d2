# Revisão de qualidade

Revisão de `gerado/` contra `gerado/docs/PRD.md` e `gerado/docs/SPEC.md`.

## Testes

| Momento | Comando | Resultado |
|---|---|---|
| Antes | `PY -m pytest -q` | `43 passed, 1 warning` |
| Depois das correções | `PY -m pytest -q` | `46 passed, 1 warning` |

O aviso é `DeprecationWarning` do `starlette.testclient` (alias `anyio.abc.BlockingPortal`), da biblioteca, sem relação com o código.

## Checklist

**Aderência**
- [x] Cada RF e RN implementado como a SPEC descreve: tabela de rastreabilidade conferida linha a linha (RF-01 a RF-12 → 8 endpoints, tela e carga inicial; RN-01 a RN-12 → funções em `app/dominio/` com comentário `# RN-xx`).
- [x] Enums e status exatamente os do pedido: `NOTEBOOK`, `PROJETOR`, `HEADSET`; `DISPONIVEL`, `EMPRESTADO`, `MANUTENCAO`; `ABERTO`, `DEVOLVIDO` (Literal no Pydantic e `CHECK` no DDL).
- [x] Carga inicial: 8 equipamentos, 3/2/3, só EQ-0008 (HEADSET) em MANUTENCAO; `test_rf_12_carga_inicial` e `test_rf_12_carga_inicial_idempotente`.

**Testes**
- [x] Todo CA confere status HTTP e o campo relevante (`status`, `situacao_equipamento`, `erro`, `dias_atraso`).
- [x] Limites com teste no limite, abaixo e acima: RN-04 (notebook 13/14/15, projetor 2/3/4, headset 3/4), RN-05 (−1/0), RN-06 (2º/3º, devolução libera), RN-11 (0/1/3 dias).
- [x] Regras de tempo usam o `relogio` de teste; `test_rn_03_retirada_usa_data_local` cobre a virada de dia UTC × America/Sao_Paulo.

**Erros**
- [x] Campo faltando, tipo errado, id inexistente → 4xx (`test_erro_validacao_entrada`, `test_rf_01_validacao_entrada`, `test_erro_*_inexistente_*`). "Data sem fuso" não se aplica: as datas do domínio são de calendário (PR-02); data com hora é recusada (`test_erro_data_prevista_so_aceita_aaaa_mm_dd`).
- [x] Erros de negócio no formato `{"erro", "mensagem"}`, em português.
- Sondagem manual com entradas hostis (ids enormes, timestamp numérico como data, dígitos Unicode no mês, JSON inválido) revelou os achados 1 a 3.

**Estrutura**
- [x] `app/dominio/` não importa FastAPI nem `sqlite3` diretamente (importa `app.erros`, que importa FastAPI; ver achado 5).
- [x] SQL só em `app/repositorio/` e DDL em `app/banco.py` (`grep -rn execute app` fora deles: nada).
- [x] Nenhum `datetime.now()` fora de `app/relogio.py`.
- [x] Escritas que dependem de leitura dentro de `banco.transacao`: cadastro de equipamento, registro de empréstimo, devolução.

**Tela**
- [x] Executa as ações da SPEC (emprestar com filtro por tipo, devolver com/sem defeito, ver em aberto e atrasados) e mostra a `mensagem` da API em `#mensagem`.
- [x] IDs usados no script existem no HTML (conferido por script: nenhum ID faltando); sintaxe do script validada com `node --check`; `innerHTML` só aparece no comentário. Os endpoints que a tela chama foram exercitados via HTTP num servidor manual (recusa por prazo, empréstimo, lista de abertos, devolução com defeito). A tentativa de dirigir a tela no navegador embutido foi abandonada porque o painel é compartilhado com outras execuções em paralelo e trocou de aba.

## Achados

| # | Gravidade | Descrição | Arquivo | Status |
|---|---|---|---|---|
| 1 | Alto | Id acima de 2^63−1 (caminho ou `equipamento_id`) gerava `OverflowError` no `sqlite3` → HTTP 500 em `GET /api/equipamentos/{id}`, `POST /api/emprestimos/{id}/devolver` e `POST /api/emprestimos`. | `app/rotas/equipamentos.py`, `app/rotas/emprestimos.py` | CORRIGIDO: `Path(ge=1, le=2**63-1)` e `Field(le=...)`; teste `test_erro_id_acima_do_limite_do_banco_nao_gera_500` |
| 2 | Médio | `data_prevista` aceitava número (timestamp Unix) e data com hora `T00:00:00`, contrariando o formato `YYYY-MM-DD` da SPEC. | `app/rotas/emprestimos.py` | CORRIGIDO: `BeforeValidator` exige texto `AAAA-MM-DD`; teste `test_erro_data_prevista_so_aceita_aaaa_mm_dd` |
| 3 | Médio | `mes` do relatório aceitava dígitos Unicode (largura total), porque `\d` casa com qualquer dígito; resposta 200 com o mês ecoado em outro alfabeto. | `app/rotas/relatorios.py` | CORRIGIDO: padrão `[0-9]`; teste `test_rf_07_mes_so_aceita_digitos_ascii` |
| 4 | Baixo | Ano 9999 recusado no relatório (limite técnico para calcular o mês seguinte). | `app/dominio/emprestimos.py` | ACEITO: irrelevante para o uso; recusa com 422 `MES_INVALIDO`, sem 500 |
| 5 | Baixo | `app/dominio/` importa `app.erros`, que importa FastAPI (dependência transitiva). É o desenho do modelo de projeto (`regra_violada` mora em `erros.py`). | `app/dominio/*.py` | ACEITO: prescrito pela skill de construção |
| 6 | Baixo | Erros de validação do framework (422) vêm com `detail` em inglês; a tela mostra o JSON do `detail`. | `app/estatico/index.html` | ACEITO: regra transversal permite "422 padrão do framework"; a tela já impede a maioria via `required`/`type` |
| 7 | Baixo | Com nenhum equipamento disponível, o envio manda `equipamento_id: 0` e recebe 422 do framework. | `app/estatico/index.html` | ACEITO: recusa correta, mensagem pouco amigável |
