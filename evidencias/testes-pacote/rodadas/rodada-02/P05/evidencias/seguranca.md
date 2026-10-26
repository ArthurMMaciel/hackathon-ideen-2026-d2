# Revisão de segurança

Sistema: `gerado/` (Chamados de suporte com prazo). Testes de ataque em `gerado/tests/test_seguranca.py` (19 testes, todos passam).

## Checklist

**Injeção de SQL**
- [x] `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` → nenhuma ocorrência (exit 1). Em `app/repositorio/chamados.py` as constantes `SQL_*` são montadas com `+` só entre literais e a constante `COLUNAS`, no carregamento do módulo, sem dado de entrada; todo valor entra por `?`.
- [x] Testes: `test_injecao_sql_em_campos_de_texto_gravada_literalmente` (titulo, descricao, solicitante_nome), `test_injecao_sql_em_responsavel_e_solucao`, `test_injecao_sql_em_parametros_de_consulta` (data_inicial, data_final → 422), `test_injecao_sql_no_caminho` (422/404). Texto gravado literalmente; listagem e fila continuam respondendo.

**XSS na tela**
- [x] `grep -rn innerHTML app/estatico/` → só o comentário da linha 78 ("nunca por innerHTML"). A tela usa `textContent`, `desenharTabela` e `createElement`.
- [x] `test_xss_texto_devolvido_literal`: `<script>alert(1)</script>` volta literal da API; `test_tela_nao_usa_innerhtml_com_dados` confere o HTML servido.

**Validação de entrada**
- [x] Todos os campos com tipo e limite: `Texto` (200), `TextoLongo` (2000), `Email` (254 + padrão), `Literal` para categoria/prioridade, `Id` (1..2147483647) no caminho, `Data` (AAAA-MM-DD, anos 2000–2100) na consulta; `responsavel` ≤ 200 e `solucao` ≤ 2000 (`StringConstraints`).
- [x] `test_entrada_acima_do_limite_ou_tipo_errado_recusada` e `test_id_negativo_e_gigante_recusados` → 422.

**Vazamento de informação**
- [x] `test_json_malformado_sem_stack_trace`: 422 sem `traceback`, `sqlite`, SQL ou caminho de arquivo. `test_erro_de_negocio_sem_detalhe_interno`: corpo só com `erro` e `mensagem`.
- [x] `grep -rn debug gerado/app` → nada; `FastAPI(...)` sem `debug=True`.

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → nenhuma ocorrência (exit 1).
- [x] Dados iniciais e de teste fictícios: nomes genéricos e e-mails no domínio reservado `empresa.example`.
- [x] `gerado/.gitignore` contém `.venv/`, `dados/`, `.tmp/` (e `__pycache__/`, `.pytest_cache/`).

**Dependências**
- [x] `requirements.txt` do modelo, sem alteração, com todas as versões fixadas (23 pacotes, diretas e transitivas). `pip check` → `No broken requirements found.`
- [x] `PYTHONIOENCODING=utf-8 PY -m pip_audit -r requirements.txt -f json -o .tmp/pip-audit.json` → `No known vulnerabilities found` (23 pacotes, 0 vulnerabilidades). `pip-audit` instalado só no `.venv`, fora do `requirements.txt`.

**Exposição**
- [x] Servidor sobe em `127.0.0.1` (padrão do uvicorn; o harness passa `--host 127.0.0.1`). Nenhum middleware CORS; `test_sem_cors_liberado` confere ausência de `Access-Control-Allow-Origin`.

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| 1 | Baixo | Sem autenticação: qualquer pessoa com acesso à máquina muda a situação de qualquer chamado. Exigência do pedido ("Não precisa de login"); mitigado por escutar só em 127.0.0.1. | ACEITO (pedido) |
| 2 | Baixo | Sem limite de taxa nem de quantidade de chamados. Aplicação local, fora de escopo. | ACEITO |

Nenhum achado alto ou médio.

## Resultado dos testes

`PY -m pytest -q` → `87 passed, 1 warning in 12.83s` (o aviso é o `StarletteDeprecationWarning` do TestClient, do modelo).
