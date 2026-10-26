# Revisão de qualidade

Revisão de `gerado/` contra `docs/PRD.md` e `docs/SPEC.md`.

- **Testes antes:** `48 passed, 1 warning`
- **Testes depois:** `50 passed, 1 warning`

## Checklist

**Aderência**
- [x] Cada RF e RN conferido contra a rastreabilidade da SPEC (8 endpoints, carga inicial, tela). RN-01..RN-13 implementadas onde a SPEC indica (`app/dominio/*`, modelos Pydantic).
- [x] Enums exatamente como no pedido: `PRESENCIAL`, `ONLINE`, `CONFIRMADA`, `ESPERA`, `CANCELADA`, `PRESENTE`, `AUSENTE` (CHECK no banco e `Literal` nos modelos).
- [x] Carga inicial cria 3 turmas futuras (`banco.TURMAS_INICIAIS`), idempotente (`contar() > 0` → não insere); `test_carga_inicial_tres_turmas_futuras`.

**Testes**
- [x] Todo `test_ca_XX` confere status e campo do corpo (`situacao`, `posicao_espera`, `erro`, `vagas_restantes`, `taxa_presenca`).
- [x] Regras com limite têm teste no limite, abaixo e acima (RN-01, RN-02, RN-03, RN-08, RN-09, RN-11).
- [x] Regras de tempo usam o `relogio` de teste; nenhum teste usa a hora real.

**Erros**
- [x] Campo faltando, tipo errado, id inexistente, data sem fuso → 4xx. Antes da revisão, id enorme e ano 9999 davam 500 (achados 1 e 2). Agora `test_entradas_invalidas_retornam_4xx` cobre os casos.
- [x] Erros de negócio em `{"erro", "mensagem"}`, mensagem em português (`app/erros.py`).

**Estrutura**
- [x] `app/dominio/` não importa FastAPI nem `sqlite3` diretamente (ver achado 5 sobre import transitivo via `app.erros`).
- [x] SQL só em `app/repositorio/` e DDL em `app/banco.py`.
- [x] `grep -rn "datetime.now" app/` → só `app/relogio.py`.
- [x] Escritas que dependem de leitura (inscrever, cancelar com promoção, presença) dentro de `banco.transacao`. Cadastro de turma também.

**Tela**
- [x] Lista turmas futuras, inscreve, mostra inscritos; mostra `mensagem` da API em erro (`catch` → `.erro`).
- [x] Todos os IDs usados pelo script existem no HTML (conferido com grep: `turmas`, `turma`, `nome`, `email`, `form-inscricao`, `resultado-inscricao`, `inscritos`, `titulo-inscritos`, `resultado-inscritos`, `status`); `node --check` no script: sintaxe ok; `GET /` → 200 com servidor real.

## Achados

| # | Gravidade | Descrição | Arquivo | Regra | Status |
|---|---|---|---|---|---|
| 1 | Alto | `GET /api/turmas/99999999999999999999` e `POST /api/inscricoes/99999999999999999999/cancelar` retornavam 500 (`OverflowError` do SQLite com inteiro acima de 64 bits). | `app/rotas/turmas.py`, `app/rotas/inscricoes.py` | Erros 4xx | CORRIGIDO: tipo `Id = Annotated[int, Path(ge=1, le=2**63-1)]` em todos os caminhos → 422. |
| 2 | Alto | `POST /api/turmas` com `inicio` `9999-12-31T23:00:00-03:00` retornava 500 (estouro de data ao converter para UTC). | `app/rotas/modelos.py` | RF-01 | CORRIGIDO: validador do ano de 2000 a 2999 → 422; SPEC atualizada. |
| 3 | Médio | Título e nome só com espaços eram aceitos, contrariando "texto obrigatório" (RN-03). | `app/rotas/modelos.py` | RN-03 | CORRIGIDO: `StringConstraints(strip_whitespace=True, min_length=1, max_length=200)`; `test_rn_03_texto_so_com_espacos_recusado`. |
| 4 | Médio | Não havia teste para campo faltando nem tipo errado. | `tests/test_regras.py` | Checklist Erros | CORRIGIDO: `test_entradas_invalidas_retornam_4xx`. |
| 5 | Baixo | `app/dominio/*` importa `app.erros`, que importa FastAPI (dependência transitiva). | `app/dominio/*.py` | Estrutura | ACEITO: padrão do modelo de projeto (a construção manda o domínio levantar `regra_violada`/`conflito`). |
| 6 | Baixo | Erros de formato vêm no padrão do framework (`{"detail": [...]}`, em inglês). | framework | Erros | ACEITO: as regras transversais mandam usar o 422 padrão do framework para formato. |
| 7 | Baixo | `DeprecationWarning` do anyio dentro do `starlette.testclient`. | dependência | — | ACEITO: versões fixadas pelo modelo; não afeta o código gerado. |
| 8 | Baixo | `/docs` e `/openapi.json` (padrão do FastAPI) não estão na SPEC. | `app/main.py` | Construção | ACEITO: documentação automática, só leitura; citada no README. |
| 9 | Baixo | Tela não aberta num navegador real (painel de navegador sem aba livre neste ambiente). | `app/estatico/index.html` | Tela | ACEITO: IDs conferidos, sintaxe validada com `node --check`, `GET /` 200. |

## Resultado

Nenhum achado alto ou médio aberto. `PY -m pytest -q` → `50 passed, 1 warning`.
