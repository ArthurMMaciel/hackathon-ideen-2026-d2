# Revisão de segurança

Sistema: `gerado/` (Reembolso de despesas). Testes de ataque em `gerado/tests/test_seguranca.py` (7 testes).

## Checklist

**Injeção de SQL**
- [x] `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/` → nenhuma linha (exit 1). As consultas com colunas fixas são constantes de módulo (`SQL_OBTER`, `SQL_LISTAR`) sem dado do usuário; todos os valores vão por `?`.
- [x] `test_injecao_sql_em_campos_de_texto_grava_literal`: `'; DROP TABLE despesas; --` em nome, descrição e comprovante → 201 com o texto literal; e-mail com aspas → 201/422; listagem continua respondendo.
- [x] `test_injecao_sql_em_parametros_de_consulta`: injeção em `email` → 200 com lista vazia; em `situacao` e `mes` → 422; em `motivo` → gravado literal; tabela intacta (5 despesas da carga).

**XSS na tela**
- [x] `grep -n innerHTML app/estatico/index.html` → só o comentário da linha 87 ("nunca innerHTML"). Dados da API exibidos com `textContent` e `createElement`.
- [x] `test_xss_texto_devolvido_literal`: `<script>alert(1)</script>` em descrição e nome é devolvido literal. Conferido no navegador na revisão de qualidade: `<b>x</b>` aparece como texto (`&lt;b&gt;x&lt;/b&gt;` no DOM).

**Validação de entrada**
- [x] Modelos Pydantic: textos `min_length=1`, `max_length=200` e sem só-espaços; e-mail por expressão regular, até 200; `valor` `Decimal` com `max_digits=12`, `decimal_places=2`, sem NaN/inf; `motivo` até 500; `data_despesa` só `AAAA-MM-DD`; `mes` com padrão e faixa de anos; `{id}` de 1 a 2^63−1; `extra="forbid"` (não aceita `situacao` no corpo de criação).
- [x] `test_texto_acima_do_limite_e_numero_negativo_422`: 201 caracteres, e-mail longo, valor −50, valor 10^12, motivo de 501, filtro de e-mail de 201 e campo extra `situacao` → 422.

**Vazamento de informação**
- [x] `test_json_malformado_sem_vazamento`: JSON truncado → 422 sem "traceback", "sqlite", SQL nem caminho de arquivo.
- [x] Sem `debug=True` (`grep -rn debug app/` vazio; `test_aplicacao_sem_debug_e_sem_cors_aberto` confere `app.debug is False`).

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → nenhuma linha (exit 1).
- [x] Dados iniciais e de teste fictícios: nomes inventados ("Ana Ficticia", "Bruno Exemplo", "Carla Modelo") e e-mails no domínio reservado `empresa.example`.
- [x] Não há repositório git nesta pasta; foi criado `gerado/.gitignore` com `.venv/`, `dados/`, `__pycache__/`, `.pytest_cache/`.

**Dependências**
- [x] Todas as versões fixadas em `requirements.txt` (`==`).
- [x] `pip-audit` instalado só no `.venv` (não no `requirements.txt`) e executado: `PY -m pip_audit -r requirements.txt`. Saída resumida abaixo; análise de aplicabilidade na tabela de achados.

```
pytest    8.3.4   PYSEC-2026-1845 9.0.3
starlette 0.41.3  PYSEC-2026-1941 0.47.2
starlette 0.41.3  PYSEC-2026-1942 0.49.1
starlette 0.41.3  PYSEC-2026-161  1.0.1
starlette 0.41.3  PYSEC-2026-2281 1.1.0
starlette 0.41.3  PYSEC-2026-2280 1.1.0
starlette 0.41.3  PYSEC-2026-249  1.3.1
starlette 0.41.3  PYSEC-2026-248  1.3.0
```

**Exposição**
- [x] Uvicorn sem `--host`: escuta em `127.0.0.1` (confirmado no log de subida: "Uvicorn running on http://127.0.0.1:...").
- [x] Sem `CORSMiddleware`; resposta a requisição com `Origin` externo não traz `access-control-allow-origin` (teste).

## Achados

| ID | Gravidade | Descrição | Status |
|---|---|---|---|
| S-01 | Médio | CVE-2025-62727 (PYSEC-2026-1942): Range malicioso causa processamento quadrático no `FileResponse` do starlette 0.41.3. Afetava a rota `/`, que servia `index.html` com `FileResponse`. Atualizar o starlette exigiria sair do `fastapi==0.115.6` da stack padrão; a rota passou a devolver `HTMLResponse` com o conteúdo lido na inicialização, que não processa Range. Teste `test_tela_ignora_cabecalho_range`. | CORRIGIDO (mitigado no código) |
| S-02 | Baixo | CVE-2025-54121: bloqueio ao processar multipart com arquivos grandes. O sistema não tem rota de formulário/upload. | ACEITO (não se aplica) |
| S-03 | Baixo | CVE-2026-48710 e CVE-2026-54282: `request.url` reconstruído a partir de Host/caminho sem validação. O sistema não usa `request.url` para decisão nenhuma. | ACEITO (não se aplica) |
| S-04 | Baixo | CVE-2026-48818: `StaticFiles` no Windows com caminho UNC. O sistema não usa `StaticFiles`. | ACEITO (não se aplica) |
| S-05 | Baixo | CVE-2026-48817: `HTTPEndpoint` com `getattr` do método. O sistema não usa `HTTPEndpoint`. | ACEITO (não se aplica) |
| S-06 | Baixo | CVE-2026-54283: limites ignorados em `application/x-www-form-urlencoded` em `request.form()`. O sistema não lê formulários. | ACEITO (não se aplica) |
| S-07 | Baixo | CVE-2025-71176 (pytest): diretório `/tmp/pytest-of-{user}` em UNIX. Dependência só de teste, ambiente local Windows. | ACEITO (não se aplica em execução) |
| S-08 | Baixo | Versões presas pela stack padrão estão desatualizadas em relação às correções do starlette (≥ 1.3.1). Atualizar é decisão da stack da fábrica, fora do escopo desta execução. | ACEITO (pendência registrada) |

## Testes

`PY -m pytest -q` → `36 passed, 1 warning`.
