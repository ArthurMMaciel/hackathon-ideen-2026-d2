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
| `app/banco.py` | conexão por requisição, `ESQUEMA`, `carga_inicial`, `transacao()` com `BEGIN IMMEDIATE` |
| `app/erros.py` | `regra_violada` (422), `conflito` (409), `nao_encontrado` (404) no formato padrão |
| `app/main.py` | `criar_app(caminho_db)`, `/api/saude`, tela em `/` |
| `tests/conftest.py` | fixtures `cliente` (banco novo por teste) e `relogio` (fixo, com `avancar()`), função `iso()` |
| `verificacao/harness.py` | `servidor(agora_iso, banco)` que sobe o uvicorn real e `Verificacao` que grava `evidencias/criterios-aceite.md` |

Não reescreva esses arquivos do zero. Estenda.

## Dependências (`gerado/requirements.txt`)

```
fastapi==0.115.6
uvicorn==0.32.1
pytest==8.3.4
httpx==0.28.1
tzdata==2025.2
```

`tzdata` é obrigatório: no Windows o `zoneinfo` não tem base de fusos sem ele. Não adicione ORM nem outra biblioteca sem necessidade registrada no log.

## Estrutura

```
gerado/
  app/
    main.py  relogio.py  banco.py  erros.py
    dominio/         # regras de negócio puras: recebem dados e `agora`, sem FastAPI e sem SQL
    repositorio/     # SQL parametrizado
    rotas/           # routers FastAPI, modelos Pydantic de entrada e saída
    estatico/index.html
  tests/
  verificacao/
  docs/PRD.md  docs/SPEC.md
  requirements.txt  pytest.ini  README.md
```

## Comandos

Rode a partir de `gerado/`. No Windows o Python do ambiente fica em `.venv/Scripts/python`; no Linux e no macOS, em `.venv/bin/python`. Abaixo, `PY` é esse caminho.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite | `PY verificacao/verificar_ca.py` |

- Use apenas SQL parametrizado (`?`). Nunca monte SQL com f-string ou concatenação.
- Toda operação que confere e depois grava (ex.: checar conflito e inserir) roda dentro de `banco.transacao(conn)`.
