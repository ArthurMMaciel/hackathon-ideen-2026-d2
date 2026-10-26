# Revisão de segurança

Sistema: `gerado/` (Reserva de salas). Testes de ataque em `gerado/tests/test_seguranca.py` (25 casos, todos passando). Suíte completa depois das correções: `83 passed, 1 warning`.

## Checklist

**Injeção de SQL**
- [x] Varredura `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` (em `gerado/`): **nenhuma linha** (código de saída 1). Todo SQL é string constante com `?`; o filtro opcional por sala usa `(? IS NULL OR sala_id = ?)`.
- [x] Teste: `'; DROP TABLE reservas; --` em `responsavel_nome` e `titulo`, `x'--@exemplo.com` no e-mail e `'; DROP TABLE salas; --` no nome da sala são gravados literalmente (201) e as listagens seguem funcionando (`test_seguranca_injecao_sql_*`). Injeção em parâmetros de consulta e caminho (`local`, `capacidade_minima`, `data`, `sala_id`, `/api/salas/1 OR 1=1`) retorna 422 e as tabelas ficam intactas.

**XSS na tela**
- [x] `grep -rn "innerHTML" app/estatico/`: só o comentário `// Sempre textContent ...; nunca innerHTML.` Nenhum uso real. A tela monta tudo com `createElement` e `textContent` (`test_seguranca_tela_nao_usa_innerhtml`).
- [x] Teste: `<script>alert(1)</script>` em `titulo` e `responsavel_nome` volta literal da API (`test_seguranca_xss_texto_literal`). Conferido também no navegador na revisão de qualidade: título `<b>Teste</b>` exibido como texto, nenhum elemento `<b>` criado.

**Validação de entrada**
- [x] Todo campo tem tipo e limite no Pydantic: textos 1..200 (`Texto`), e-mail 3..254 com padrão, `capacidade` 1..500, `participantes` 1..1000, `recursos` enum sem repetição (máx. 3), `local` enum, ids 1..2^63−1, datas com fuso e ano 2000..2100, `capacidade_minima` 1..500.
- [x] Teste: texto com 201 caracteres, e-mail com 257, `participantes` −1, `sala_id` −1, `capacidade` −5, 50 recursos e `capacidade_minima` −1 retornam 422 (`test_seguranca_limites_*`).

**Vazamento de informação**
- [x] Teste: JSON malformado em `POST /api/reservas` e `POST /api/salas` retorna 422 sem `traceback`, `sqlite`, SQL nem caminho de arquivo no corpo (`test_seguranca_json_malformado_sem_vazamento`).
- [x] A aplicação não roda com `debug=True`: `grep -rniE "debug|CORSMiddleware|allow_origins" app/` sem resultado; `app.debug is False` conferido em teste.

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv`: **nenhuma linha** (código de saída 1).
- [x] Dados iniciais (6 salas com nomes inventados) e de teste (`Ana Teste`, `ana@exemplo.com`, `Pessoa Ficticia`, `pessoa@exemplo.com`) são fictícios; domínio `exemplo.com`.
- [x] `.gitignore` da raiz (não alterado) cobre `.venv/` e `*.db`, mas não cita `gerado/dados/`. Criado `gerado/.gitignore` com `dados/`, `.venv/`, `__pycache__/`, `.pytest_cache/`.

**Dependências**
- [x] Todas as versões diretas fixadas em `requirements.txt` (`==`). Dependências transitivas (starlette, pydantic, anyio) ficam fixadas indiretamente pela faixa do FastAPI, sem lockfile.
- [x] `pip-audit` instalado só no `.venv` (não no `requirements.txt`) e executado: `PY -m pip_audit -r requirements.txt` → "Found 16 known vulnerabilities in 2 packages" (8 IDs distintos; cada um aparece duas vezes na saída). Saída completa em `evidencias/pip-audit.json`. Tratamento abaixo.

| Pacote | ID | Resumo | Aplica ao sistema? | Tratamento |
|---|---|---|---|---|
| starlette 0.41.3 | CVE-2025-62727 (PYSEC-2026-1942) | Cabeçalho `Range` forjado causa CPU quadrática no `FileResponse` | **Sim**: a tela era servida com `FileResponse` | CORRIGIDO: `/` passa a usar `HTMLResponse` com o conteúdo do arquivo; teste `test_seguranca_tela_ignora_cabecalho_range` |
| starlette 0.41.3 | CVE-2025-54121 (PYSEC-2026-1941) | Upload multipart grande bloqueia a thread | Não: nenhum endpoint aceita formulário multipart | ACEITO |
| starlette 0.41.3 | CVE-2026-48710 (PYSEC-2026-161) | `Host` não validado ao reconstruir `request.url` | Não: o código não usa `request.url` | ACEITO |
| starlette 0.41.3 | CVE-2026-54282 (PYSEC-2026-248) | Caminho sem `/` altera `request.url.hostname` | Não: o código não usa `request.url` | ACEITO |
| starlette 0.41.3 | CVE-2026-54283 (PYSEC-2026-249) | Limites de `request.form()` ignorados para urlencoded | Não: nenhum endpoint lê formulário | ACEITO |
| starlette 0.41.3 | CVE-2026-48818 (PYSEC-2026-2281) | `StaticFiles` no Windows com caminho UNC | Não: `StaticFiles` não é usado | ACEITO |
| starlette 0.41.3 | CVE-2026-48817 (PYSEC-2026-2280) | `HTTPEndpoint` sem restrição de método | Não: `HTTPEndpoint` não é usado | ACEITO |
| pytest 8.3.4 | CVE-2025-71176 (PYSEC-2026-1845) | Diretório previsível `/tmp/pytest-of-{user}` em UNIX | Só no ambiente de desenvolvimento, não em execução | ACEITO (baixo) |

A correção completa exigiria starlette >= 1.3.1, o que obriga a trocar a versão do FastAPI fixada pela stack padrão (`fastapi==0.115.6` só aceita starlette < 0.42). A troca não foi feita para não sair da stack padrão; fica registrada como pendência.

**Exposição**
- [x] O servidor sobe em `127.0.0.1` (padrão do uvicorn; o comando documentado não passa `--host`). Sem `CORSMiddleware`; teste com `Origin` externo não recebe `Access-Control-Allow-Origin` (`test_seguranca_sem_debug_e_sem_cors`).

## Achados

| ID | Gravidade | Descrição | Status |
|---|---|---|---|
| S-01 | Médio | Tela servida por `FileResponse`, exposta à CVE-2025-62727 (DoS por cabeçalho `Range`) na starlette 0.41.3 fixada pela stack | CORRIGIDO (`HTMLResponse`, teste de regressão) |
| S-02 | Baixo | Outras 6 vulnerabilidades da starlette 0.41.3 em recursos que o sistema não usa | ACEITO, pendência de atualizar FastAPI/starlette fora da stack padrão |
| S-03 | Baixo | pytest 8.3.4 com CVE-2025-71176 (só UNIX, só desenvolvimento) | ACEITO |
| S-04 | Baixo | `gerado/dados/` não citado no `.gitignore` da raiz (só `*.db`) | CORRIGIDO (`gerado/.gitignore`) |
| S-05 | Baixo | Sem autenticação: qualquer pessoa com acesso à máquina pode cancelar reservas de outros | ACEITO: o pedido diz "Não precisa de login por enquanto" (fora de escopo no PRD); o servidor só escuta em 127.0.0.1 |
