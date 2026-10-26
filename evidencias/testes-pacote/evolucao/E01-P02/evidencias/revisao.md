# Revisão de qualidade

Revisão de `gerado/` contra `gerado/docs/PRD.md` e `gerado/docs/SPEC.md`.

- **Testes antes da revisão:** `57 passed, 1 warning in 6.96s`
- **Testes depois das correções:** `57 passed, 1 warning in 7.38s`

## Achados

| # | Gravidade | Descrição | Arquivo | Regra / requisito | Status |
|---|---|---|---|---|---|
| 1 | Médio | SQL da carga inicial (`SELECT COUNT(*)` e `INSERT`) estava em `app/banco.py`, fora de `app/repositorio/`; o checklist só admite DDL em `banco.py`. | `app/banco.py` (`carga_inicial`) | Estrutura, RF-08 | CORRIGIDO: `repositorio.despesas.contar` e `inserir` (agora com `motivo_recusa`) usados pela carga |
| 2 | Baixo | `valor_centavos` aceita a string `"12"` (coerção leniente do Pydantic). Não gera erro 500 nem viola regra; dígitos Unicode (`"１２"`) e decimais (`12.5`) são recusados com 422. | `app/rotas/despesas.py` | PR-05 | ACEITO: comportamento padrão do framework, sem impacto nas regras |
| 3 | Baixo | Aviso `StarletteDeprecationWarning` do `TestClient` aparece na saída do pytest; o filtro do `pytest.ini` do modelo cobre só `DeprecationWarning`. | `pytest.ini` (modelo) | — | ACEITO: não afeta o sistema; o modelo pede para não alterar os arquivos base sem necessidade |
| 4 | Baixo | `recusar` lê a despesa fora da transação para devolver 404 antes de conferir o motivo; a leitura é repetida dentro da transação antes de gravar, então não há corrida. | `app/rotas/despesas.py` | PR-12, RN-07 | ACEITO |
| 5 | Baixo | Listagem sem paginação. | `app/repositorio/despesas.py` | RF-06 | ACEITO: volume local pequeno; paginação não pedida |

Nenhum achado alto.

## Checklist

**Aderência**
- [x] Cada RF e RN conferido contra a rastreabilidade da SPEC: RF-01..RF-11 e RN-01..RN-10 implementados como descrito (funções em `app/dominio/despesas.py` com `# RN-xx`).
- [x] Enums e status exatamente os do pedido: `TRANSPORTE`, `HOSPEDAGEM`, `ALIMENTACAO`, `OUTROS`; `PENDENTE`, `APROVADA`, `RECUSADA`, `PAGA` (Literal nas rotas e CHECK no DDL).
- [x] Carga inicial cria 5 despesas, cobrindo as 4 situações, datas relativas a `agora` (`test_rf_08_...`).

**Testes**
- [x] Todo CA confere status e campo do corpo (`situacao`, `erro`, `valor_centavos`, totais).
- [x] Toda regra com limite tem teste no limite, abaixo e acima (RN-01, RN-02 nas 4 categorias, RN-03, RN-04).
- [x] Regras de tempo usam o `relogio` de teste (`test_rn_03_virada_do_dia_libera_data` usa `avancar`); nenhum teste depende da hora real.

**Erros e valores extremos** (sonda `gerado/.tmp/sonda.py` com TestClient, `raise_server_exceptions=False`)

| Sonda | Status |
|---|---|
| id `99999999999999999999` em aprovar, recusar, pagar, excluir | 422 |
| id `0` e id `abc` | 422 |
| data ano `9999`, `0001`, data com hora | 422 |
| nome só com espaços | 422 |
| descrição, comprovante, e-mail com 5000 caracteres | 422 |
| e-mail inválido | 422 |
| valor negativo, valor `10^20`, valor `"１２"`, valor `12.5` | 422 |
| categoria inválida, campo faltando, JSON inválido, corpo lista | 422 |
| motivo com 5000 caracteres, motivo numérico, corpo de recusa texto | 422 |
| filtro e-mail com 5000 caracteres, só espaços; situação inválida | 422 |
| mês `9999-01`, `0001-01`, `２０３０-01`, 5000 caracteres | 422 |
| mês `2100-12` (limite válido) | 200 |
| id inexistente `999999` | 404 `DESPESA_NAO_ENCONTRADA` (teste `test_despesa_inexistente_404`) |

Nenhuma resposta 5xx.

- [x] Erros de negócio no formato `{"erro", "mensagem"}`, mensagens em português; 422 para valor, limite, datas e motivo; 409 para duplicidade, transição e exclusão.

**Estrutura**
- [x] `app/dominio/` importa só `calendar`, `datetime` e `app.dominio.erros` (sem `fastapi` nem `sqlite3`).
- [x] SQL só em `app/repositorio/` e DDL em `app/banco.py` (após correção do achado 1; `grep SELECT|INSERT|UPDATE|DELETE FROM` fora do repositório: nada).
- [x] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py`.
- [x] Escritas dependentes de leitura dentro de `banco.transacao` (lançar, mudar situação, excluir).
- [x] Carga inicial usa o `agora` recebido.

**Tela**
- [x] Ações da SPEC presentes: lançar, filtrar, aprovar, recusar com motivo, pagar, excluir, resumo do mês; erros mostrados com `mostrarMensagem(..., "erro")`.
- [x] Todo `getElementById` aponta para elemento existente (`mensagem`, `form-despesa`, `form-filtro`, `lista-despesas`, `form-resumo`, `resumo`).
- [x] Script extraído passa em `node --check` (Node v22.23.2).
- [x] Endpoints chamados pela tela respondem com os parâmetros que ela envia (`gerado/.tmp/sonda_tela.py`): POST lançar 201 (`valor_centavos` 1234 a partir de R$ 12,34), GET lista 200 com e sem filtros, recusar com motivo vazio 422 `MOTIVO_OBRIGATORIO`, aprovar → APROVADA, pagar → PAGA, DELETE 204, resumo 200.
