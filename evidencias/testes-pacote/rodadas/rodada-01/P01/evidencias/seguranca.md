# Revisão de segurança

Sistema: `gerado/` (FastAPI + SQLite local, sem login). Testes de ataque em `gerado/tests/test_seguranca.py` (9 testes).

## Checklist

**Injeção de SQL**
- [x] Varredura `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/`.
  - 1ª execução: 2 ocorrências (`app/repositorio/emprestimos.py:25`, `app/repositorio/equipamentos.py:13`), f-strings que juntavam só fragmentos constantes de SQL (`_SELECT`, `COLUNAS`), sem dado de entrada. Não havia injeção, mas o padrão contraria a regra da stack. Achado S1.
  - Depois da correção: nenhuma ocorrência (`grep` com código de saída 1).
- [x] Teste `test_injecao_sql_em_campos_de_texto_fica_literal`: `'; DROP TABLE equipamentos; --` em `descricao` e `nome` é gravado literalmente (201); em `email` e `patrimonio` é recusado pelo formato (422); listagens continuam funcionando.
- [x] Teste `test_injecao_sql_em_parametros_de_consulta`: o mesmo texto em `tipo`, `situacao`, `status`, `mes` e no id do caminho → 422; tabela intacta.

**XSS na tela**
- [x] `grep -rn innerHTML app/estatico/`: só o comentário "nunca innerHTML". A tela usa `textContent`, `createElement` e `replaceChildren`.
- [x] Teste `test_xss_texto_devolvido_literal`: `<script>alert(1)</script>` no nome volta literal da API. Teste `test_tela_nao_usa_innerhtml_com_dados` garante que a página servida não usa `innerHTML`, `outerHTML` nem `document.write`.

**Validação de entrada**
- [x] Todos os campos com tipo e limite no Pydantic: textos com `min_length=1`, `max_length=200` (patrimônio 20) e `strip_whitespace`; e-mail com padrão e `max_length=200`; `equipamento_id` e ids de caminho entre 1 e 2^63−1; `tipo`, `situacao`, `status` como `Literal`; `data_prevista` só texto `AAAA-MM-DD`; `mes` com padrão `[0-9]{4}-[0-9]{2}`.
- [x] Testes `test_texto_acima_do_limite_retorna_422` (201 caracteres, e-mail longo, patrimônio longo) e `test_numero_negativo_retorna_422` (ids −1, 0, −5 em corpo e caminho).

**Vazamento de informação**
- [x] Teste `test_json_malformado_sem_stack_trace`: JSON inválido nos 3 POSTs → 422, sem `Traceback`, sem `sqlite`, sem caminho de arquivo. O caso de 500 por id gigante (com `OverflowError` do driver) foi corrigido na revisão de qualidade (achado 1 de `revisao.md`).
- [x] A aplicação não usa `debug=True` (`grep -rni debug app/`: nada; teste `test_sem_debug_e_sem_cors_aberto` confere `app.debug is False`).

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv`: nenhuma ocorrência.
- [x] Dados iniciais e de teste fictícios: equipamentos genéricos; pessoas "Ana Exemplo", "Bruno Exemplo" etc. com e-mails no domínio reservado `exemplo.test`.
- [x] `gerado/.gitignore` lista `.venv/`, `dados/`, `__pycache__/` e `.pytest_cache/`. Observação: a pasta de trabalho não é um repositório git; o `.gitignore` foi criado em `gerado/`, que é a raiz do sistema entregue.

**Dependências**
- [x] Versões fixadas em `requirements.txt` (fastapi 0.115.6, uvicorn 0.32.1, pytest 8.3.4, httpx 0.28.1, tzdata 2025.2).
- [x] `PY -m pip install pip-audit` (no `.venv`, fora do `requirements.txt`) e `PY -m pip_audit -r requirements.txt`. Saída resumida:

  ```
  pytest    8.3.4   PYSEC-2026-1845 (CVE-2025-71176)  fix 9.0.3
  starlette 0.41.3  PYSEC-2026-1941 (CVE-2025-54121)  fix 0.47.2
  starlette 0.41.3  PYSEC-2026-1942 (CVE-2025-62727)  fix 0.49.1
  starlette 0.41.3  PYSEC-2026-161  (CVE-2026-48710)  fix 1.0.1
  starlette 0.41.3  PYSEC-2026-2281 (CVE-2026-48818)  fix 1.1.0
  starlette 0.41.3  PYSEC-2026-2280 (CVE-2026-48817)  fix 1.1.0
  starlette 0.41.3  PYSEC-2026-249  (CVE-2026-54283)  fix 1.3.1
  starlette 0.41.3  PYSEC-2026-248  (CVE-2026-54282)  fix 1.3.0
  ```

  `starlette 0.41.3` vem como dependência transitiva de `fastapi==0.115.6`, versão fixada pela stack padrão da fábrica. Análise de aplicabilidade abaixo (achados S2 a S4).

**Exposição**
- [x] O servidor sobe em `127.0.0.1` (padrão do uvicorn; o README e o harness não passam `--host`).
- [x] Sem `CORSMiddleware` (`grep -rniE "CORSMiddleware|allow_origins" app/`: nada); teste confirma ausência de `access-control-allow-origin`.

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| S1 | Baixo | SQL com f-string de fragmentos constantes em 2 funções do repositório; sem dado externo, mas contraria a regra "nunca f-string" e polui a varredura. | CORRIGIDO: consultas viraram constantes de módulo (`_POR_ID`, `_LISTAR`, `_VENCIDOS`); varredura limpa |
| S2 | Médio | CVE-2025-62727: `FileResponse` do starlette 0.41.3 tem processamento quadrático do cabeçalho `Range` (DoS). A tela em `/` era servida com `FileResponse`. | CORRIGIDO: `/` passa a usar `HTMLResponse` com o conteúdo do arquivo, sem tratamento de `Range`; teste `test_tela_ignora_cabecalho_range` |
| S3 | Baixo | Demais CVEs do starlette 0.41.3 (formulário multipart/urlencoded, `StaticFiles` com UNC no Windows, `HTTPEndpoint` sem `methods`, reconstrução de `request.url` pelo Host/caminho) dependem de recursos que a aplicação não usa: não há `request.form()`, `StaticFiles`, `HTTPEndpoint` nem uso de `request.url`. | ACEITO: não aplicável ao código; atualizar FastAPI/starlette exige mudar a versão fixada pela stack padrão |
| S4 | Baixo | CVE-2025-71176 do pytest 8.3.4: diretório `/tmp/pytest-of-{user}` em UNIX; ferramenta só de desenvolvimento, execução local em Windows. | ACEITO: não afeta o sistema em execução |

## Testes

- `PY -m pytest -q tests/test_seguranca.py` → `9 passed, 1 warning`
- `PY -m pytest -q` → `55 passed, 1 warning`
