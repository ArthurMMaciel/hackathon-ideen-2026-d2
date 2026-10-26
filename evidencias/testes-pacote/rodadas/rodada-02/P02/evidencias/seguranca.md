# Revisão de segurança

Sistema: `gerado/` (Reembolso de despesas). Testes de ataque em `gerado/tests/test_seguranca.py` (18 casos, todos passam).

## Checklist

**Injeção de SQL**
- [x] Varredura `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` → nenhuma ocorrência.
  Varredura complementar por f-strings com SQL (`grep -rnE 'f"SELECT|f"INSERT|f"UPDATE|f"DELETE' app/`):
  - `app/repositorio/despesas.py:15` `_BUSCAR = f"SELECT {_COLUNAS} FROM despesas WHERE id = ?"` — composição só de constante de módulo (`_COLUNAS`), avaliada no import; dado de entrada só por `?`.
  - `app/repositorio/despesas.py:18` `_LISTAR = f"SELECT {_COLUNAS} ..."` — idem.
- [x] Teste: `'; DROP TABLE despesas; --` em `colaborador_nome`, `descricao`, `comprovante`, `motivo` e nos filtros `email`, `situacao` e `mes`. Resultado: texto gravado literalmente (201/200) ou 422 nos filtros tipados; listagem continua com as 5 despesas da carga (`test_injecao_sql_*`).

**XSS na tela**
- [x] `grep -rn innerHTML app/estatico/` → só o comentário da linha 89 ("nunca por innerHTML"). Dados entram por `textContent` e `desenharTabela`.
- [x] Teste: `<script>alert(1)</script>` em descrição e nome é devolvido literal pela API (`test_xss_devolvido_literal`); `test_tela_nao_usa_innerhtml_com_dados` garante que a tela não usa `innerHTML` em código.

**Validação de entrada**
- [x] Todos os campos com tipo e limite: `Texto` (1–200, sem espaços nas pontas), `Email` (≤254, padrão), `Data` (AAAA-MM-DD, ano 2000–2100), `Centavos` (0–100.000.000), `Literal` para categoria e situação, `Id` (1–2.147.483.647) no caminho, `Mes` (AAAA-MM, 2000–2100) e `motivo` com `max_length=200`.
- [x] Teste: texto com 201 caracteres e valor negativo → 422 (`test_texto_acima_do_limite_422`, `test_motivo_acima_do_limite_422`, `test_valor_negativo_422`). Sonda de valores extremos da revisão: nenhum 5xx.

**Vazamento de informação**
- [x] Teste: JSON malformado → 422 sem `traceback`, `sqlite`, SQL ou caminho de arquivo (`test_json_malformado_sem_vazamento`); erro de negócio só com `erro` e `mensagem`.
- [x] Aplicação sem `debug=True` (`grep debug app/` vazio; `test_app_sem_debug`).

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → nenhuma ocorrência.
- [x] Dados iniciais e de teste fictícios: nomes genéricos e e-mails no domínio reservado `.example`.
- [x] `gerado/.gitignore` contém `.venv/`, `dados/`, `.tmp/` (e caches).

**Dependências**
- [x] `requirements.txt` do modelo, sem alteração, com todas as versões fixadas (diretas e transitivas). `pip check`: "No broken requirements found."
- [x] `PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pip_audit -r requirements.txt -f json -o .tmp/pip-audit.json` → "No known vulnerabilities found"; JSON: 23 dependências, 0 vulnerabilidades. `pip-audit` instalado só no `.venv`, fora do `requirements.txt`.

**Exposição**
- [x] Servidor sobe em `127.0.0.1` (padrão do uvicorn; o harness passa `--host 127.0.0.1`). Nenhum middleware de CORS (`grep -rn "CORS\|allow_origins" app/` vazio).

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| 1 | Baixo | Sem autenticação: qualquer pessoa com acesso à máquina aprova, paga ou exclui. | ACEITO: o pedido exclui login ("Sem login por enquanto"); fora de escopo no PRD |
| 2 | Baixo | Resposta 422 do FastAPI ecoa o valor recebido no campo `input`. | ACEITO: só reflete a própria entrada do usuário, em JSON, sem stack trace nem SQL |

Nenhum achado alto ou médio.

## Testes

`.venv/Scripts/python -m pytest -q` → `75 passed, 1 warning in 7.18s`
