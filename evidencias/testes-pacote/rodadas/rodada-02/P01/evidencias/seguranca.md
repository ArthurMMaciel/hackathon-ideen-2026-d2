# Revisão de segurança

**Suíte depois da revisão:** `80 passed, 1 warning in 7.48s` (inclui `tests/test_seguranca.py`: `18 passed`).

## Achados

| # | Gravidade | Descrição | Status |
|---|---|---|---|
| 1 | Baixo | `pip-audit -r requirements.txt` cria um ambiente virtual temporário na pasta temporária do sistema (fora da pasta de trabalho) para resolver as dependências. Não afeta o sistema gerado. | ACEITO (comportamento da ferramenta exigida pela skill) |

Nenhum achado alto ou médio.

## Checklist

**Injeção de SQL**
- [x] `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" gerado/app/` → nenhuma ocorrência.
- [x] Composições de texto SQL fora de `execute` (busca extra por `f"SELECT` e `_SELECT +`): 8 ocorrências em `app/repositorio/equipamentos.py` (linhas 8, 10, 11, 13) e `app/repositorio/emprestimos.py` (linhas 12–15). Todas juntam só constantes de módulo (`_COLUNAS`, `_SELECT`) com texto fixo, em tempo de importação; nenhum dado de entrada. Dados de entrada entram só por `?`.
- [x] Testes: `test_injecao_sql_em_textos_gravada_literalmente` (descrição e nome gravados literalmente, 201), `test_injecao_sql_em_campos_com_formato_recusada` (patrimônio e e-mail → 422), `test_injecao_sql_em_parametros_de_consulta` (tipo, status, mês → 422), `test_injecao_sql_no_caminho` (→ 4xx). Em todos, as listagens continuam respondendo depois.

**XSS na tela**
- [x] `grep -rn innerHTML gerado/app/estatico/` → só o comentário da linha 85 ("nunca por innerHTML"). Dados entram por `textContent`, `createTextNode` e `desenharTabela`.
- [x] Testes: `test_xss_devolvido_como_texto_literal` (`<script>alert(1)</script>` volta literal em nome e descrição), `test_tela_nao_usa_innerhtml_com_dados`.

**Validação de entrada**
- [x] Todo campo tem tipo e limite: `patrimonio` (padrão `^EQ-[0-9]{4}$`, máx. 7), `tipo`/`status` (`Literal`), `descricao`/`nome` (`Texto`, 1–200), `email` (`Email`, máx. 254), `equipamento_id`/`id` (`Id`, 1–2.147.483.647), `data_prevista` (`Data`, anos 2000–2100), `defeito` (`StrictBool`), `mes` (`AAAA-MM`, anos 2000–2100). Campos extras recusados (`extra="forbid"`).
- [x] Testes: `test_texto_acima_do_limite_e_numero_negativo_recusados` (nome 201 caracteres, e-mail longo, id −1, 0 e 2.147.483.648 → 422), `test_descricao_acima_do_limite_recusada`.

**Vazamento de informação**
- [x] `test_json_malformado_sem_stack_trace`: JSON truncado → 422 sem `traceback`, `sqlite`, SQL ou caminho de arquivo.
- [x] `test_erro_de_negocio_sem_detalhe_interno`: erro de negócio só com `erro` e `mensagem`.
- [x] `test_app_sem_debug_e_sem_cors_aberto`: `app.debug is False`; `grep -rniE "debug|cors" gerado/app/` → nada.

**Segredos e dados**
- [x] `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv` → nenhuma ocorrência.
- [x] Dados iniciais e de teste fictícios: equipamentos genéricos, pessoas "Ana Teste"/"Pessoa Fictícia", e-mails `@exemplo.com`.
- [x] `gerado/.gitignore` contém `.venv/`, `dados/`, `.tmp/` (além de `__pycache__/` e `.pytest_cache/`).

**Dependências**
- [x] `requirements.txt` do modelo, sem alteração, com todas as versões fixadas (diretas e transitivas).
- [x] `PYTHONIOENCODING=utf-8 PY -m pip_audit -r requirements.txt -f json -o .tmp/pip-audit.json` → `No known vulnerabilities found`; resumo do JSON: 23 pacotes, 0 vulnerabilidades. `pip-audit` não entrou no `requirements.txt`.

**Exposição**
- [x] O servidor sobe em `127.0.0.1` (padrão do uvicorn; o harness passa `--host 127.0.0.1`). Sem `CORSMiddleware`.
