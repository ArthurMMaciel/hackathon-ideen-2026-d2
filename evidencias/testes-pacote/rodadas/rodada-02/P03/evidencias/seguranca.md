# Revisão de segurança

## Checklist

**Injeção de SQL**
- [x] `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` → **nenhuma ocorrência**. Composições `"SELECT " + _COLUNAS + "..."` em `app/repositorio/turmas.py` e `app/repositorio/inscricoes.py` são constantes de módulo montadas só com outras constantes (lista de colunas), fora de `execute`; dado de entrada entra só por `?`.
- [x] Testes (`tests/test_seguranca.py`): `'; DROP TABLE turmas; --` em `titulo` e `nome` gravado literalmente (201) e listagens continuam funcionando; e-mail com aspas válido gravado literal; e-mail com injeção inválido → 422; injeção em parâmetros de caminho → 404/422; parâmetro de consulta desconhecido ignorado (200, 3 turmas).

**XSS na tela**
- [x] `grep -rn "innerHTML" app/estatico/` → 1 ocorrência, só o comentário "nunca por innerHTML". Dados entram por `textContent` e `desenharTabela`.
- [x] Teste: `<script>alert(1)</script>` em `titulo` e `nome` devolvido literal pela API (`test_xss_devolvido_literal`).

**Validação de entrada**
- [x] Todo campo de entrada com tipo e limite: `titulo`/`nome` `Texto` (1–200, sem espaços nas pontas), `email` `Email` (até 254, formato), `inicio` `DataHora` (fuso obrigatório, ano 2000–2100), `vagas`/`duracao_minutos` inteiro estrito ±1.000.000 + regra no domínio, `turma_id` inteiro estrito 1–2.147.483.647, `modalidade`/`situacao` `Literal`; ids no caminho `Id`.
- [x] Testes: título com 201 caracteres, nome com 201, vagas −1, duração −1 → 422.

**Vazamento de informação**
- [x] Teste: JSON malformado → 422 sem `traceback`, `sqlite`, SQL ou caminho de arquivo (`test_json_malformado_sem_vazamento`); erro de negócio só com `erro` e `mensagem`.
- [x] `app.debug is False` (`test_app_sem_debug`); nenhum `debug=True` em `app/` (grep).

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → **nenhuma ocorrência**.
- [x] Dados iniciais e de teste fictícios: títulos genéricos, nomes "Pessoa N"/"Pessoa Fictícia", e-mails no domínio reservado `exemplo.test`.
- [x] `gerado/.gitignore` contém `.venv/`, `dados/`, `.tmp/` (e `__pycache__/`, `.pytest_cache/`).

**Dependências**
- [x] `requirements.txt` do modelo, sem alteração, com todas as versões fixadas (diretas e transitivas).
- [x] `pip-audit` instalado só no `.venv` (fora do `requirements.txt`); `PYTHONIOENCODING=utf-8 PY -m pip_audit -r requirements.txt -f json -o .tmp/pip-audit.json` → `No known vulnerabilities found`; resumo do JSON: **23 pacotes, 0 vulnerabilidades**. `pip check` → `No broken requirements found.`

**Exposição**
- [x] Servidor sobe em `127.0.0.1` (padrão do uvicorn; o harness passa `--host 127.0.0.1`). Nenhum middleware de CORS (`grep -rn "CORS\|allow_origins" app/` → nada).

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| — | — | Nenhum achado alto, médio ou baixo nesta etapa. (O único achado de validação, coerção de `true`/`1.5` em inteiros, foi tratado na revisão de qualidade.) | — |

## Testes

`tests/test_seguranca.py`: `15 passed`. Suíte completa: `95 passed, 1 warning in 11.56s`.
