# Revisão de segurança

Sistema: Reserva de salas (`gerado/`). Testes de ataque em `gerado/tests/test_seguranca.py` (19 testes, todos passam).

## Checklist

**Injeção de SQL**
- [x] `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` → nenhuma ocorrência.
- [x] Busca adicional por SQL em f-string: `app/repositorio/reservas.py` linhas 14, 20, 22 e 25 (`OBTER`, `NO_INTERVALO`, `NO_INTERVALO_DA_SALA`, `ATIVAS_NO_INTERVALO`). Justificativa: interpolam só a constante de módulo `_COLUNAS` (lista fixa de colunas), na carga do módulo; todo dado de entrada entra por `?`.
- [x] Testes: `test_injecao_sql_em_campos_de_texto_da_sala`, `test_injecao_sql_em_campos_de_texto_da_reserva` (responsável e título), `test_injecao_sql_no_email`, `test_injecao_sql_em_parametros_de_consulta` (6 casos), `test_injecao_sql_no_caminho`. Resultado: texto gravado literalmente (201) ou 422; listagens de salas, agenda e relatório continuam respondendo 200.

**XSS na tela**
- [x] `grep -rn innerHTML app/estatico/` → só a linha 92, que é o comentário do modelo ("nunca por innerHTML"). Dados da API entram por `textContent` e `desenharTabela`.
- [x] `test_xss_texto_devolvido_literal`: `<script>alert(1)</script>` em nome de sala e título volta literal na API. `test_tela_nao_usa_innerhtml_com_dados`: nenhuma atribuição a `innerHTML`/`outerHTML`, `insertAdjacentHTML` ou `document.write` na tela.

**Validação de entrada**
- [x] Todos os campos com tipo e limite: `Texto` (1..200, sem espaços nas pontas), `Email` (padrão, até 254), `Id` (1..2.147.483.647), `DataHora` (fuso obrigatório, ano 2000..2100), `Data` (AAAA-MM-DD), capacidade e participantes 1..1000, `local` e `recursos` por `Literal`, lista de recursos até 3.
- [x] `test_texto_acima_do_limite_recusado` (201 caracteres → 422) e `test_numero_negativo_recusado` (participantes -3 e capacidade -1 → 422).

**Vazamento de informação**
- [x] `test_json_malformado_sem_vazamento`: JSON truncado → 422, sem `Traceback`, `sqlite3`, SQL ou caminho de arquivo. `test_erro_de_negocio_sem_vazamento`: corpo só com `erro` e `mensagem`.
- [x] Sem `debug=True` (`grep -rn debug app/` → nada; `test_app_sem_debug`).

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → nenhuma ocorrência (código de saída 1).
- [x] Salas iniciais com nomes fictícios (Paulista, Ibirapuera, Laranjeira, Morada do Sol, Coworking Azul, Coworking Verde); testes e verificação usam "Pessoa Ficticia" / `pessoa@exemplo.com`.
- [x] `gerado/.gitignore` contém `.venv/`, `dados/`, `.tmp/` (e `__pycache__/`, `.pytest_cache/`).

**Dependências**
- [x] `requirements.txt` do modelo, sem alteração, com todas as versões fixadas (diretas e transitivas).
- [x] `PY -m pip install pip-audit` e `PYTHONIOENCODING=utf-8 PY -m pip_audit -r requirements.txt -f json -o .tmp/pip-audit.json` → "No known vulnerabilities found"; resumo do JSON: 23 pacotes, 0 vulnerabilidades. `pip check` → "No broken requirements found". `pip-audit` não entrou no `requirements.txt`.

**Exposição**
- [x] Servidor sobe em `127.0.0.1` (padrão do uvicorn; o harness passa `--host 127.0.0.1`). Nenhum `CORSMiddleware` (`grep` → nada); `test_sem_cors_liberado`: sem cabeçalho `Access-Control-Allow-Origin`.

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| 1 | Baixo | f-strings de SQL com a constante `_COLUNAS` em `app/repositorio/reservas.py`; seguras, mas fogem do padrão "SQL só em constantes literais". | ACEITO: só constantes, sem dado de entrada |
| 2 | Baixo | Sem login nem controle de acesso: qualquer pessoa na máquina pode cancelar qualquer reserva. | ACEITO: o pedido diz "não precisa de login"; servidor só em 127.0.0.1 |

Nenhum achado alto ou médio.

## Testes

`PY -m pytest -q` → `89 passed, 1 warning in 11.75s`.
