# Empréstimo de equipamentos

Sistema local para controlar notebooks, projetores e headsets emprestados: cadastro de equipamentos (patrimônio `EQ-0000`), registro de empréstimo e devolução, equipamentos disponíveis, empréstimos atrasados e relatório mensal por tipo. Sem login. Dados em SQLite (`dados/app.db`), criados na primeira subida com 8 equipamentos fictícios.

Requisitos e decisões: [docs/PRD.md](docs/PRD.md). Contrato da API e plano de testes: [docs/SPEC.md](docs/SPEC.md).

## Instalar

Requer Python 3.11 ou superior. A partir desta pasta (`gerado/`):

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Windows
.venv/bin/python -m pip install -r requirements.txt         # Linux e macOS
```

Nos comandos abaixo, `PY` é `.venv/Scripts/python` (Windows) ou `.venv/bin/python` (Linux/macOS).

## Testar

```bash
PY -m pytest -q
```

## Rodar

```bash
PY -m uvicorn app.main:app --port 8000
```

- Tela: http://127.0.0.1:8000/ (emprestar, devolver, ver atrasados e disponíveis)
- Documentação da API: http://127.0.0.1:8000/docs
- `APP_AGORA=2030-01-07T09:00:00-03:00` fixa o relógio do servidor (útil para demonstrar atrasos); `APP_DB` troca o arquivo do banco.

## Verificar

```bash
PY verificacao/verificar_ca.py    # critérios de aceite via HTTP -> ../evidencias/criterios-aceite.md
PY verificacao/subida_manual.py   # subida com relógio real -> ../evidencias/subida-manual.md
```

## API

| Método | Caminho | O que faz |
|---|---|---|
| POST | `/api/equipamentos` | Cadastra equipamento (nasce `DISPONIVEL`) |
| GET | `/api/equipamentos` | Lista equipamentos |
| GET | `/api/equipamentos/disponiveis?tipo=` | Disponíveis, filtro opcional por tipo |
| GET | `/api/equipamentos/{id}` | Consulta um equipamento |
| POST | `/api/emprestimos` | Registra empréstimo |
| GET | `/api/emprestimos?status=` | Lista empréstimos |
| GET | `/api/emprestimos/atrasados` | Atrasados com dias de atraso |
| POST | `/api/emprestimos/{id}/devolver` | Registra devolução (`{"defeito": true/false}`) |
| GET | `/api/relatorios/emprestimos-por-tipo?mes=AAAA-MM` | Empréstimos do mês por tipo |
