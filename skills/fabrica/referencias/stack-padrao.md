# Stack padrão

Use esta stack, salvo se o pedido exigir outra. Ela foi escolhida para rodar localmente, sem compilação nativa e sem serviço externo.

| Camada | Escolha |
|---|---|
| Linguagem | Python 3.11 ou superior |
| API | FastAPI, servida por uvicorn |
| Banco | SQLite pelo módulo `sqlite3` da biblioteca padrão, arquivo em `gerado/dados/app.db` |
| Testes | pytest, com `fastapi.testclient.TestClient` |
| Tela | Um `index.html` com JavaScript simples (`fetch`), servido pela própria API em `/`. Sem framework, sem build |

## Ponto de partida obrigatório

A construção começa copiando `../construcao/modelo-projeto/` para `gerado/`. O modelo já traz, testados:

| Arquivo | O que resolve |
|---|---|
| `app/relogio.py` | `obter_agora` injetável, `APP_AGORA` para fixar o relógio do servidor, conversão de e para UTC no banco |
| `app/banco.py` | conexão por requisição, `ESQUEMA`, `carga_inicial(conn, agora)`, `transacao()` com `BEGIN IMMEDIATE` |
| `app/tipos.py` | `Id`, `DataHora`, `Data`, `Texto`, `TextoLongo`, `Email`, `Centavos`: limites que evitam HTTP 500 |
| `app/dominio/erros.py` | `regra_violada` (422), `conflito` (409), `nao_encontrado` (404), sem dependência de FastAPI |
| `app/main.py` | `criar_app(caminho_db)`, tradução de `ErroNegocio` para JSON, `/api/saude`, tela em `/` com `HTMLResponse` |
| `app/estatico/index.html` | CSS pronto e funções `api()`, `mostrarMensagem()`, `lerFormulario()`, `desenharTabela()` |
| `tests/conftest.py` | fixtures `cliente` (banco novo por teste) e `relogio` (fixo, com `avancar()`), função `iso()` |
| `tests/test_modelo.py` | testes dos tipos e do relógio da carga inicial; mantenha |
| `verificacao/harness.py` | `servidor(agora_iso, banco)` em porta livre, `resumo(resposta, *campos)`, `Verificacao` que grava em `evidencias/` ordenado por código |
| `verificacao/subida_manual.py` | sobe com relógio real, confere `/api/saude`, `/` e `/docs`, derruba e grava `evidencias/subida-manual.md` |
| `.gitignore` | `.venv/`, `dados/`, `.tmp/`, caches |

Não reescreva esses arquivos do zero. Estenda.

## Dependências

Use o `requirements.txt` do modelo sem alterar versões. Todas as dependências, inclusive as transitivas, estão fixadas, e o conjunto passou no `pip-audit` sem vulnerabilidade conhecida em 26/10/2026. Não adicione ORM nem outra biblioteca sem necessidade registrada no log.

## Estrutura

```
gerado/
  app/
    main.py  relogio.py  banco.py  tipos.py
    dominio/         # regras de negócio puras e erros.py: recebem dados e `agora`, sem FastAPI e sem SQL
    repositorio/     # SQL parametrizado
    rotas/           # routers FastAPI, modelos Pydantic de entrada e saída
    estatico/index.html
  tests/
  verificacao/
  docs/PRD.md  docs/SPEC.md
  requirements.txt  pytest.ini  README.md  .gitignore
```

## Comandos

Rode a partir de `gerado/`. No Windows o Python do ambiente fica em `.venv/Scripts/python`; no Linux e no macOS, em `.venv/bin/python`. Abaixo, `PY` é esse caminho. Para criar o ambiente, use `python` no Windows e `python3` no Linux e no macOS, onde `python` costuma não existir. O `gerado/README.md` traz os comandos separados para Windows, Linux e macOS.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite | `PY verificacao/verificar_ca.py` |
| Subida manual conferida | `PY verificacao/subida_manual.py` |

- Use apenas SQL parametrizado (`?`). Nunca interpole dado de entrada em SQL.
- Toda operação que confere e depois grava (ex.: checar conflito e inserir) roda dentro de `banco.transacao(conn)`.
