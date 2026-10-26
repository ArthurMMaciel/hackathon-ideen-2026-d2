# Revisão de segurança

**Testes depois das correções:** `68 passed, 1 warning` (inclui `tests/test_seguranca.py`, 17 casos).

## Checklist

### Injeção de SQL
- [x] Varredura `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/`.
  - 1ª rodada: 3 ocorrências em `app/repositorio/ferias.py` (`conn.execute(_SELECT_COLABORADOR + " WHERE c.id = ?", ...)`). Eram concatenação de constantes, sem dado do usuário, ou seja, falso positivo. Mesmo assim as consultas viraram constantes de módulo (S-02) para a varredura ficar limpa.
  - 2ª rodada: nenhuma saída (`rc=1`).
- [x] Testes `test_injecao_sql_em_campos_de_texto_grava_literal`, `test_injecao_sql_em_parametros_de_consulta` (3 casos), `test_injecao_sql_no_mes_e_nas_datas`: `'; DROP TABLE colaboradores; --` no nome é gravado literalmente; em e-mail, `situacao`, `colaborador_id`, `mes` e datas dá 422; a listagem continua respondendo com os 9/10 colaboradores.

### XSS na tela
- [x] `grep -rn innerHTML app/estatico/`: única ocorrência é o comentário "nunca innerHTML". Dados entram com `textContent` e `createElement`.
- [x] `test_xss_texto_volta_literal`: `<script>alert(1)</script>` volta literal da API. `test_tela_nao_usa_innerhtml` garante a ausência no HTML.

### Validação de entrada
- [x] Modelos Pydantic: `nome` 1..120 (com strip), `email` até 200 com regex, `equipe` enum, `saldo` 0..365, `colaborador_id` e ids de caminho 1..2147483647, datas só `AAAA-MM-DD`, `situacao` enum, `mes` até 7 caracteres e validado no domínio.
- [x] `test_limites_de_entrada_colaborador` (nome 121, e-mail longo, saldo −5, saldo 10^12, nome só espaços) e `test_numero_negativo_na_solicitacao`: todos 422.

### Vazamento de informação
- [x] `test_json_malformado_sem_stack_trace`: JSON inválido → 422 sem `Traceback`, `sqlite` ou `SELECT`.
- [x] `test_app_sem_debug`: `app.debug is False`; `grep -rniE "debug" app/` sem ocorrência.

### Segredos e dados
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv`: nenhuma saída (`rc=1`).
- [x] Dados iniciais e de teste fictícios, e-mails no domínio reservado `exemplo.test`.
- [x] `gerado/.gitignore` com `.venv/`, `dados/`, `__pycache__/`, `.pytest_cache/`. Não existe repositório git nesta pasta; o `.gitignore` foi criado em `gerado/`.

### Dependências
- [x] Versões fixadas em `requirements.txt` (as da stack padrão). Dependências transitivas (starlette, pydantic, anyio) não são fixadas pela stack.
- [x] `pip-audit` instalado só no `.venv` (depois removido), `pip_audit -r requirements.txt` executado. Saída completa em `evidencias/pip-audit.json`. Resumo:

| Pacote | Id | Correção | Aplica-se? | Tratamento |
|---|---|---|---|---|
| pytest 8.3.4 | CVE-2025-71176 | 9.0.3 | Não: diretório `/tmp/pytest-of-*` em UNIX; dependência só de teste | Aceito |
| starlette 0.41.3 | CVE-2025-54121 | 0.47.2 | Não: o sistema não lê formulários multipart | Aceito |
| starlette 0.41.3 | CVE-2025-62727 | 0.49.1 | **Sim**: `FileResponse` servia a tela e é vulnerável a DoS por cabeçalho `Range` | Mitigado (S-01) |
| starlette 0.41.3 | CVE-2026-48710 | 1.0.1 | Não: `request.url` não é usado | Aceito |
| starlette 0.41.3 | CVE-2026-48818 | 1.1.0 | Não: `StaticFiles` não é usado | Aceito |
| starlette 0.41.3 | CVE-2026-48817 | 1.1.0 | Não: `HTTPEndpoint` não é usado | Aceito |
| starlette 0.41.3 | CVE-2026-54283 | 1.3.1 | Não: `request.form()` não é usado | Aceito |
| starlette 0.41.3 | CVE-2026-54282 | 1.3.0 | Não: `request.url` não é usado | Aceito |

As correções de starlette exigem trocar a versão do FastAPI fixada pela stack padrão (`fastapi==0.115.6` prende `starlette<0.42`). A stack manda usar essas versões; por isso a vulnerabilidade aplicável foi mitigada no código, sem troca de versão.

### Exposição
- [x] uvicorn sobe sem `--host`, logo em `127.0.0.1` (README e harness). Sem `CORSMiddleware`; `test_sem_cors_liberado` confere que não há `Access-Control-Allow-Origin`.

## Achados

| # | Gravidade | Descrição | Arquivo | Status |
|---|---|---|---|---|
| S-01 | Médio | Tela servida por `FileResponse` do starlette 0.41.3, sujeito a CVE-2025-62727 (DoS por `Range`). Servidor só em 127.0.0.1, por isso médio | `app/main.py` | CORRIGIDO: `HTMLResponse` com o conteúdo do arquivo; teste `test_tela_ignora_cabecalho_range` |
| S-02 | Baixo | Varredura de SQL acusava concatenação de constantes (falso positivo) | `app/repositorio/ferias.py` | CORRIGIDO: consultas como constantes de módulo |
| S-03 | Baixo | Versões transitivas com CVEs não aplicáveis ao uso (tabela acima) | `requirements.txt` | ACEITO: presas pela versão do FastAPI exigida na stack padrão |
