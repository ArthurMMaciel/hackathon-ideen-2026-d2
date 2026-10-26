# Revisão de segurança

Sistema: `gerado/` (Inscrição em treinamentos). Testes de ataque em `gerado/tests/test_seguranca.py` (9 testes).

## Checklist

**Injeção de SQL**
- [x] `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` → nenhuma linha. Consultas com subconsulta fixa estão em constantes de texto (`repositorio/turmas.py`), sem dado do usuário.
- [x] `test_injecao_sql_nos_campos_de_texto_e_gravada_literalmente`: `'; DROP TABLE turmas; --` em título e nome → 201, gravado literalmente; listagens continuam funcionando. `test_injecao_sql_em_parametros_de_caminho`: `1 OR 1=1`, `1;DROP TABLE turmas`, `1'--` nos caminhos → 422; tabelas intactas.

**XSS na tela**
- [x] `grep -rn innerHTML app/estatico/` → só o comentário "nunca innerHTML" (linha 55). Dados exibidos com `textContent` e `createElement`. `test_tela_nao_usa_innerhtml_com_dados`.
- [x] `test_xss_e_devolvido_como_texto_literal`: `<script>alert(1)</script>` em título e nome → API devolve o texto literal.

**Validação de entrada**
- [x] Todos os campos com tipo e limite: título e nome 1–200 (espaços das pontas removidos), e-mail 3–254 com padrão, vagas 1–50, duração 1–1440, modalidade e situação de presença como `Literal`, início com fuso e ano 2000–2999, ids de caminho 1..2^63−1.
- [x] `test_texto_acima_do_limite_e_numero_negativo_recusados`: título 201, nome 10.000, e-mail 307 caracteres, vagas −5, duração −1 → 422.

**Vazamento de informação**
- [x] `test_json_malformado_nao_vaza_detalhes`: JSON inválido → 422 sem traceback, SQL ou caminho de arquivo. `test_erro_de_negocio_nao_vaza_sql`: duplicidade → 409 com só `erro` e `mensagem`.
- [x] Sem `debug=True`: `grep -rniE "debug" gerado/app` → nada.

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → nada.
- [x] Dados iniciais (3 turmas com títulos genéricos) e de teste (`pessoaN@exemplo.test`, `*.test`) são fictícios.
- [x] `gerado/.gitignore` contém `.venv/`, `dados/`, `__pycache__/`, `.pytest_cache/`. (Não há repositório git nesta pasta; o `.gitignore` foi criado em `gerado/`.)

**Dependências**
- [x] Versões diretas fixadas em `requirements.txt` (fastapi, uvicorn, pytest, httpx, tzdata). Transitivas (starlette, pydantic, anyio) seguem as faixas declaradas pelo fastapi 0.115.6.
- [x] `pip-audit` instalado só no `.venv` (não no `requirements.txt`) e executado: `Found 16 known vulnerabilities in 2 packages` (linhas duplicadas por alias). Análise abaixo.

**Exposição**
- [x] O servidor sobe em `127.0.0.1` (padrão do uvicorn; nenhum `--host` nos comandos documentados). Nenhum `CORSMiddleware`; `test_sem_cors_liberado` confirma ausência de `Access-Control-Allow-Origin`.

## Saída do pip-audit (resumida, sem duplicatas)

| Pacote | Versão | Vulnerabilidade | Corrigida em | Afeta este sistema? |
|---|---|---|---|---|
| starlette | 0.41.3 | CVE-2025-62727 (DoS por cabeçalho Range no `FileResponse`) | 0.49.1 | **Sim**: a tela era servida com `FileResponse`. Mitigado (achado S1). |
| starlette | 0.41.3 | CVE-2025-54121 (multipart com arquivos grandes bloqueia o loop) | 0.47.2 | Não: nenhuma rota aceita formulário/multipart; `python-multipart` nem está instalado. |
| starlette | 0.41.3 | CVE-2026-48710, CVE-2026-54282 (Host/path não validados ao reconstruir `request.url`) | 1.0.1 / 1.3.0 | Baixo: o sistema não usa `request.url` para decisão nenhuma e escuta só em 127.0.0.1. |
| starlette | 0.41.3 | CVE-2026-48818 (`StaticFiles` no Windows com caminho UNC) | 1.1.0 | Não: `StaticFiles` não é usado. |
| starlette | 0.41.3 | CVE-2026-48817 (`HTTPEndpoint` com método arbitrário) | 1.1.0 | Não: `HTTPEndpoint` não é usado. |
| starlette | 0.41.3 | CVE-2026-54283 (limites ignorados em `x-www-form-urlencoded`) | 1.3.1 | Não: nenhuma rota lê `request.form()`. |
| pytest | 8.3.4 | CVE-2025-71176 (`/tmp/pytest-of-{user}` em UNIX) | 9.0.3 | Não em produção: dependência só de teste; ambiente Windows. |

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| S1 | Alto | `GET /` usava `FileResponse`, exposto ao DoS por Range (CVE-2025-62727) na versão de starlette fixada pela stack. | CORRIGIDO: a tela é lida uma vez e servida com `HTMLResponse` (`app/main.py`); `test_tela_ignora_cabecalho_range`. |
| S2 | Baixo | starlette 0.41.3 tem outras CVEs em recursos não usados (multipart, StaticFiles, HTTPEndpoint, form urlencoded, reconstrução de URL). | ACEITO: a atualização exigiria trocar a versão do fastapi fixada pela stack padrão; nenhum caminho vulnerável é usado. Recomendação registrada para quem mantiver o sistema. |
| S3 | Baixo | pytest 8.3.4 (CVE-2025-71176, UNIX). | ACEITO: dependência de teste, não roda com a aplicação. |
| S4 | Baixo | Dependências transitivas não fixadas no `requirements.txt`. | ACEITO: a stack padrão define exatamente esse `requirements.txt`; fastapi limita a faixa do starlette. |

## Resultado

Nenhum achado alto ou médio aberto. `PY -m pytest -q` → `59 passed, 1 warning`.
