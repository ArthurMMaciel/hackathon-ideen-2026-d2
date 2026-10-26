# Revisão de segurança

Sistema: `gerado/` (Férias da equipe). Testes de ataque em `gerado/tests/test_seguranca.py` (13 testes, todos passam).
Suíte completa depois da revisão: `71 passed, 1 warning`.

## Checklist

**Injeção de SQL**
- [x] Varredura `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` → **nenhuma ocorrência** (saída vazia, código de saída 1).
- [x] Varredura complementar por f-strings com SQL: 4 ocorrências em `app/repositorio/ferias.py` (linhas 14, 15, 27, 31). Todas compõem só constantes de módulo (`_COLABORADOR_COLUNAS`, `_SOLICITACAO_COLUNAS`) no carregamento do módulo; nenhum dado de entrada. Dados entram só por `?`.
- [x] Teste `test_injecao_sql_em_campos_de_texto_gravada_literalmente`: `'; DROP TABLE colaboradores; --` no nome é gravado literalmente (201) e a listagem continua com o registro; e-mail com aspas aceito ou recusado sem quebrar o banco.
- [x] Testes `test_injecao_sql_em_parametros_de_consulta` (mes com injeção → 422; 9 colaboradores intactos) e `test_injecao_sql_em_campos_de_solicitacao` (→ 422; listagem funciona).

**XSS na tela**
- [x] `grep -rn innerHTML app/estatico/` → só a linha 69, um comentário ("nunca por innerHTML"). Dados entram por `textContent`, `desenharTabela` e `option.textContent`.
- [x] Teste `test_xss_devolvido_literal_pela_api`: `<script>alert(1)</script>` gravado e devolvido literal. `test_tela_nao_usa_innerhtml_com_dados` confere o HTML servido.

**Validação de entrada**
- [x] Todos os campos têm tipo e limite: `nome` `Texto` (1–200, sem espaços nas pontas), `email` `Email` (até 254, padrão), `equipe` `Literal`, `saldo` 0–365, `colaborador_id` e ids de caminho `Id` (1–2.147.483.647), datas `Data` (AAAA-MM-DD, ano 2000–2100), `mes` `Mes` (AAAA-MM, ano 2000–2100).
- [x] Testes `test_texto_acima_do_limite_e_numero_negativo_recusados` (nome 201 caracteres, e-mail longo, saldo −1 → 422) e `test_id_negativo_recusado` (→ 422).

**Vazamento de informação**
- [x] Teste `test_json_malformado_sem_stack_trace`: JSON truncado → 422 sem `traceback`, `sqlite`, SQL ou caminho de arquivo. `test_erro_de_negocio_sem_detalhe_interno`: 404 só com `erro` e `mensagem`.
- [x] Sem `debug=True` (grep por `debug` em `app/`: vazio); `test_app_sem_debug_e_sem_cors_aberto` confere `app.debug is False`.

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → **nada** (código de saída 1).
- [x] Dados iniciais fictícios (nomes inventados, e-mails em `exemplo.com`); testes usam `pessoaN@exemplo.com` e nomes genéricos.
- [x] `gerado/.gitignore` contém `.venv/`, `dados/`, `.tmp/` (e `__pycache__/`, `.pytest_cache/`).

**Dependências**
- [x] `requirements.txt` do modelo, sem alteração: 23 pacotes com versão fixada (diretas e transitivas). `pip check`: `No broken requirements found.`
- [x] `PYTHONIOENCODING=utf-8 PY -m pip_audit -r requirements.txt -f json -o .tmp/pip-audit.json` → `No known vulnerabilities found`; resumo do JSON: 23 pacotes, 0 vulnerabilidades. `pip-audit` não entrou no `requirements.txt`.

**Exposição**
- [x] Servidor sobe em `127.0.0.1` (padrão do uvicorn; o harness passa `--host 127.0.0.1`).
- [x] Sem `CORSMiddleware` (grep `CORS` em `app/`: vazio); teste confirma ausência de `Access-Control-Allow-Origin` com `Origin` estranho.

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| 1 | Baixo | Sem autenticação: qualquer pessoa com acesso à tela aprova, reprova ou cancela. É o que o pedido define ("Não precisa de login"), registrado em PR-07 e no fora de escopo. | ACEITO: exigência do pedido; servidor só em 127.0.0.1 |
| 2 | Informativo | f-strings de SQL em `app/repositorio/ferias.py` compõem só constantes de módulo. | ACEITO: sem dado de entrada |

Nenhum achado alto ou médio.
