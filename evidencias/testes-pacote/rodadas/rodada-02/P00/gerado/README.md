# Reserva de salas

Sistema simples para reservar salas em São Paulo, Araraquara e no coworking sem conflito de horário: cadastro de salas, reservas com validação (sobreposição, duração de 15 min a 4 h, sem passado, capacidade), cancelamento com histórico, consulta de salas livres e relatório de ocupação diária (8h às 18h). Começa com 6 salas fictícias, duas por local. Sem login.

Documentos: [docs/PRD.md](docs/PRD.md) e [docs/SPEC.md](docs/SPEC.md).

## Requisitos

Python 3.11 ou superior. Comandos a partir desta pasta (`gerado/`). No Windows, `PY` = `.venv/Scripts/python`; no Linux/macOS, `.venv/bin/python`.

## Comandos

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite (sobe o servidor real, grava `../evidencias/criterios-aceite.md`) | `PY verificacao/verificar_ca.py` |
| Subida manual conferida (grava `../evidencias/subida-manual.md`) | `PY verificacao/subida_manual.py` |

## Endereços

- Tela: http://127.0.0.1:8000/ (nova reserva, agenda do dia por sala com cancelamento, salas livres, ocupação do dia)
- Documentação da API: http://127.0.0.1:8000/docs
- Banco SQLite: `dados/app.db` (outro caminho com a variável `APP_DB`)
- `APP_AGORA` (ISO 8601 com offset) fixa o relógio do servidor, usado na verificação.

## API

| Método | Caminho | O que faz |
|---|---|---|
| GET | `/api/salas` | Lista salas |
| GET | `/api/salas/livres?inicio=&fim=&local=&capacidade_minima=` | Salas livres no intervalo |
| GET | `/api/salas/{id}` | Consulta sala |
| POST | `/api/salas` | Cadastra sala |
| POST | `/api/reservas` | Cria reserva (status `ATIVA`) |
| GET | `/api/reservas?dia=&sala_id=` | Agenda do dia |
| POST | `/api/reservas/{id}/cancelar` | Cancela reserva futura (status `CANCELADA`) |
| GET | `/api/relatorios/ocupacao?dia=` | Taxa de ocupação por sala no dia |

Horários sempre em ISO 8601 com offset (ex.: `2030-01-08T10:00:00-03:00`); fuso `America/Sao_Paulo`.
