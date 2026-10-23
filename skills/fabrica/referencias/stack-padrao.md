# Stack padrão

Use esta stack, salvo se o pedido exigir outra. Ela foi escolhida para rodar localmente, sem compilação nativa e sem serviço externo.

| Camada | Escolha |
|---|---|
| Linguagem | Python 3.11 ou superior |
| API | FastAPI, servida por uvicorn |
| Banco | SQLite pelo módulo `sqlite3` da biblioteca padrão, arquivo em `gerado/dados/app.db` |
| Testes | pytest, com `fastapi.testclient.TestClient` |
| Tela | Um `index.html` com JavaScript simples (`fetch`), servido pela própria API em `/`. Sem framework, sem build |

## Dependências (`gerado/requirements.txt`)

```
fastapi==0.115.6
uvicorn==0.32.1
pytest==8.3.4
httpx==0.28.1
```

Não adicione ORM nem outra biblioteca sem necessidade registrada no log.

## Estrutura

```
gerado/
  app/
    __init__.py
    main.py          # cria o FastAPI, rotas, monta a tela em /
    banco.py         # conexão, criação de tabelas, carga inicial
    relogio.py       # agora() injetável
    dominio/         # regras de negócio, sem FastAPI e sem SQL
    repositorio/     # SQL parametrizado
    estatico/index.html
  tests/
    conftest.py      # banco temporário e relógio fixo por teste
    test_*.py
  docs/
    PRD.md
    SPEC.md
  requirements.txt
  README.md
```

## Comandos

Rode a partir de `gerado/`. No Windows o Python do ambiente fica em `.venv/Scripts/python`; no Linux e no macOS, em `.venv/bin/python`. Abaixo, `PY` é esse caminho.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |

- O caminho do banco vem da variável `APP_DB` (padrão `dados/app.db`). Os testes usam um arquivo temporário por teste.
- Use apenas SQL parametrizado (`?`). Nunca monte SQL com f-string ou concatenação.
- Ligue `PRAGMA foreign_keys = ON` em toda conexão.
