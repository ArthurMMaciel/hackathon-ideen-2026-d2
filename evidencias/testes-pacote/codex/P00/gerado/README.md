# Reserva de salas

Sistema local com API REST, seis salas iniciais, reservas sem conflito, busca de salas livres, cancelamento com histórico, relatório de ocupação e tela web em `http://127.0.0.1:8000/`. Documentação interativa da API em `/docs`. O banco SQLite fica em `dados/app.db`.

Execute os comandos dentro de `gerado/`.

## Windows (PowerShell)

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verificação: `.venv/Scripts/python verificacao/verificar_ca.py` e `.venv/Scripts/python verificacao/subida_manual.py`.

## Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verificação: `.venv/bin/python verificacao/verificar_ca.py` e `.venv/bin/python verificacao/subida_manual.py`.

## macOS

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verificação: `.venv/bin/python verificacao/verificar_ca.py` e `.venv/bin/python verificacao/subida_manual.py`.
