# Revisão de qualidade

Revisão de `gerado/` contra `gerado/docs/PRD.md` e `gerado/docs/SPEC.md`.

## Testes

| Momento | Resultado (`PY -m pytest -q`) |
|---|---|
| Antes da revisão | `53 passed, 1 warning` |
| Depois das correções | `72 passed, 1 warning` |

O aviso é `DeprecationWarning` do `starlette.testclient` sobre `anyio.abc.BlockingPortal` (versões fixadas da stack padrão), sem efeito no comportamento.

## Checklist

**Aderência**
- [x] Cada RF e RN conferido contra a tabela de rastreabilidade da SPEC (RF-01..RF-12, RN-01..RN-10): implementados em `app/rotas/chamados.py`, `app/dominio/chamados.py`, `app/dominio/relatorio.py`, `app/banco.py`.
- [x] Enums exatamente como no pedido: `ACESSO/HARDWARE/SOFTWARE`, `BAIXA/MEDIA/ALTA/CRITICA`, `ABERTO/EM_ATENDIMENTO/RESOLVIDO/FECHADO`, indicação `ATRASADO`.
- [x] Carga inicial: 6 chamados (2 ABERTO, 1 EM_ATENDIMENTO, 2 RESOLVIDO, 1 FECHADO), como RF-12 e a SPEC; conferido por `test_rf_12_carga_inicial`.

**Testes**
- [x] Todo `test_ca_*` confere status e campo do corpo (`situacao`, `erro`, `prazo`, `dentro_do_prazo`, `indicacao`, números do relatório).
- [x] Limites com teste no limite, abaixo e acima: RN-03 (239/240/241 min), RN-06 (6d23h59/7d/7d+1min), RN-08 (239/240/241 min), RN-09 (199/200/201 caracteres), RN-10 (00:00 do dia inicial, 23:59 do final, 00:00 do seguinte, 23:59 do anterior), RN-01 (4 prioridades).
- [x] Regras de tempo usam a fixture `relogio`; nenhum teste depende da hora real (a carga inicial usa a hora real, mas os testes filtram pelos ids que criam).

**Erros**
- [x] Campo faltando, tipo errado, id inexistente → 4xx (`tests/test_entradas.py`, `test_rf_02_consultar_e_404`). Data sem fuso: não se aplica, a API não recebe data e hora (só datas `YYYY-MM-DD` no relatório, testadas com valores inválidos).
- [x] Erros de negócio no formato `{"erro", "mensagem"}` em português.

**Estrutura**
- [x] `app/dominio/` não importa FastAPI nem `sqlite3` diretamente (importa `app.erros`, que usa FastAPI para o handler; ver achado Q5).
- [x] SQL só em `app/repositorio/chamados.py` e DDL em `app/banco.py`.
- [x] Nenhum `datetime.now()` fora de `app/relogio.py` dentro de `app/`.
- [x] Escritas que dependem de leitura (todas as transições e a abertura) dentro de `banco.transacao`.

**Tela**
- [x] Abre chamado, mostra fila com `ATRASADO`, assumir/resolver/fechar/reabrir, relatório; erros da API exibidos em `#mensagem`.
- [x] Todos os IDs usados por `getElementById` existem no HTML (fila, form-abrir, form-relatorio, mensagem, relatorio, status, todos); script passa em `node --check`.

## Achados

| # | Gravidade | Descrição | Arquivo | Regra | Status |
|---|---|---|---|---|---|
| Q1 | Alto | `GET/POST /api/chamados/{id}` com id acima do INTEGER do SQLite (ex.: `99999999999999999999999`) gerava `OverflowError` → 500. | `app/rotas/chamados.py` | Erros da API | CORRIGIDO: `IdChamado = Annotated[int, Path(ge=1, le=2**63-1)]` em todas as rotas com id; teste `test_id_fora_da_faixa_nao_gera_500`. |
| Q2 | Alto | Relatório com `data_final=9999-12-31` gerava `OverflowError` ao somar 1 dia → 500. | `app/dominio/relatorio.py:14` | RN-10 | CORRIGIDO: recusa com 422 `PERIODO_INVALIDO`; teste `test_relatorio_datas_invalidas_nao_gera_500`. |
| Q3 | Médio | Faltavam testes de entrada inválida comum (campo faltando, tipo errado, campo desconhecido, data inválida no relatório). | `tests/` | Checklist de erros | CORRIGIDO: `tests/test_entradas.py` (19 casos). |
| Q4 | Baixo | Constantes `CATEGORIAS`, `SITUACOES`, `NAO_RESOLVIDAS` não usadas no domínio. | `app/dominio/chamados.py` | — | CORRIGIDO: removidas. |
| Q5 | Baixo | O domínio importa `app.erros`, que importa `fastapi` para o handler; o import é indireto. | `app/dominio/chamados.py:5` | Estrutura | ACEITO: é o padrão do modelo de projeto (`regra_violada` vem de `app/erros.py`, conforme a skill de construção). |
| Q6 | Baixo | Erros de validação do framework (422) aparecem na tela como o JSON de `detail`, em inglês. | `app/estatico/index.html` | Idioma | ACEITO: a tela mostra o erro (exigência da SPEC); os erros de regra de negócio estão em português; a função `api()` é a do modelo. |
