# Revisão de segurança

Sistema: `gerado/` (FastAPI + SQLite, local, sem login). Testes de ataque em `gerado/tests/test_seguranca.py`.

## Checklist

**Injeção de SQL**
- [x] Varredura `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` → nenhuma ocorrência (saída vazia, rc=1). Consultas são constantes literais com `?` em `app/repositorio/chamados.py`.
- [x] Teste: `'; DROP TABLE chamados; --` em `titulo`, `descricao`, `solicitante_nome`, `responsavel`, `solucao` → gravado literal (201/200); em `solicitante_email` e `categoria` → 422; em `data_inicial` do relatório e no id do caminho → 422; listagem continua com os 6 chamados (`test_injecao_sql_*`). PASSOU.

**XSS na tela**
- [x] `grep -rn innerHTML app/estatico/` → só o comentário da linha 72 ("nunca innerHTML"). Dados exibidos com `textContent` e `createElement`.
- [x] Teste: `<script>alert(1)</script>` no título volta literal na API (`test_xss_gravado_literal`). PASSOU.

**Validação de entrada**
- [x] Todos os campos com tipo e limite: textos `max_length` (título 200, descrição/solução 2000, nomes 100, e-mail 200 com regex), enums `Literal`, id `1..2^63-1`, datas `date`. Modelo de criação com `extra="forbid"`.
- [x] Teste: texto acima do limite em cada campo → 422; id negativo → 422 (`test_texto_acima_do_limite_422`, `test_textos_das_transicoes_acima_do_limite_422`, `test_numero_negativo_422`). PASSOU.

**Vazamento de informação**
- [x] Teste: JSON malformado → 422 sem `traceback`, `sqlite`, SQL ou caminho de arquivo (`test_json_malformado_sem_stack_trace`). Erro de negócio só com `erro` e `mensagem`. PASSOU.
- [x] `grep -rn "debug" app/` → nenhuma ocorrência; `FastAPI(...)` sem `debug=True`.

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → nenhuma ocorrência (rc=1).
- [x] Dados iniciais e de teste fictícios: nomes genéricos ("Ana Exemplo", "Bruno Ficticio"...) e e-mails `@example.com`.
- [x] Não há repositório git na pasta de trabalho; criado `gerado/.gitignore` com `dados/`, `.venv/`, `__pycache__/`, `.pytest_cache/`.

**Dependências**
- [x] Todas as versões fixadas em `requirements.txt` (`==`).
- [x] `pip-audit` instalado só no `.venv` (não no `requirements.txt`) e executado: `PY -m pip_audit -r requirements.txt` → "Found 16 known vulnerabilities in 2 packages" (entradas duplicadas por alias). Análise abaixo.

| Pacote | Vulnerabilidade | Aplica a este sistema? | Tratamento |
|---|---|---|---|
| starlette 0.41.3 | CVE-2025-62727 (DoS por cabeçalho `Range` no `FileResponse`) | Sim: a tela era servida com `FileResponse` | CORRIGIDO: `/` passou a usar `HTMLResponse` com o conteúdo do arquivo, que não processa `Range`; teste `test_tela_ignora_cabecalho_range` |
| starlette 0.41.3 | CVE-2025-54121, CVE-2026-54283 (formulários multipart/urlencoded) | Não: nenhuma rota lê formulário | ACEITO, não aplicável |
| starlette 0.41.3 | CVE-2026-48818 (`StaticFiles` no Windows, UNC) | Não: `StaticFiles` não é usado | ACEITO, não aplicável |
| starlette 0.41.3 | CVE-2026-48817 (`HTTPEndpoint` e método arbitrário) | Não: `HTTPEndpoint` não é usado | ACEITO, não aplicável |
| starlette 0.41.3 | CVE-2026-48710, CVE-2026-54282 (reconstrução de `request.url` a partir de Host/caminho) | Não: o sistema não usa `request.url` para decisão nem para redirecionamento | ACEITO, não aplicável |
| pytest 8.3.4 | CVE-2025-71176 (`/tmp/pytest-of-{user}` em UNIX) | Só no ambiente de desenvolvimento, em UNIX multiusuário | ACEITO: dependência de teste; a stack padrão fixa a versão |

Recomendação registrada (não executada para não sair da stack padrão): atualizar `fastapi`/`starlette` para versões com starlette ≥ 1.3.1 numa próxima revisão da stack.

**Exposição**
- [x] Servidor sobe em `127.0.0.1` (padrão do uvicorn; o comando documentado não usa `--host 0.0.0.0`).
- [x] Sem CORS: nenhum `CORSMiddleware`; teste `test_sem_cors_liberado` confere que não há `Access-Control-Allow-Origin`.

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| S1 | Médio | DoS por `Range` no `FileResponse` da tela (CVE-2025-62727, starlette fixado na stack). Impacto limitado: servidor só em 127.0.0.1. | CORRIGIDO (HTMLResponse + teste) |
| S2 | Baixo | Demais vulnerabilidades do starlette 0.41.3 e do pytest 8.3.4 em recursos não usados pelo sistema. | ACEITO (não aplicável; atualização da stack recomendada) |
| S3 | Baixo | Sem `.gitignore` para `dados/` e `.venv/`. | CORRIGIDO (`gerado/.gitignore`) |

## Testes

`PY -m pytest -q` após as correções: `89 passed, 1 warning`.
