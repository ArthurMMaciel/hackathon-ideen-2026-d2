# Reserva de salas

Sistema simples para as salas de São Paulo, Araraquara e do coworking: cadastro de salas, reserva sem conflito de horário, cancelamento com histórico, busca de salas livres, agenda do dia por sala e relatório de ocupação (08:00–18:00, só reservas ativas). Começa com 6 salas fictícias, duas por local. Sem login.

- Requisitos: `docs/PRD.md`. Especificação (endpoints, erros, plano de testes): `docs/SPEC.md`.
- Fuso `America/Sao_Paulo`. Datas e horas na API em ISO 8601 com offset (ex.: `2030-01-08T10:00:00-03:00`); horário sem fuso é recusado com 422.
- Banco SQLite local em `dados/app.db` (criado na primeira subida; outro caminho com a variável `APP_DB`).

## Comandos

Rode a partir desta pasta (`gerado/`). No Windows `PY` é `.venv/Scripts/python`; no Linux e no macOS, `.venv/bin/python`.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite | `PY verificacao/verificar_ca.py` (sobe o servidor real na porta 8765 e grava `../evidencias/criterios-aceite.md`) |

Para fixar o relógio do servidor (demonstrações e verificação), defina `APP_AGORA` com data e hora ISO 8601 com offset.

## Tela e API

- Tela: http://127.0.0.1:8000/ (nova reserva, salas livres, agenda do dia por sala com cancelamento, ocupação do dia).
- Documentação interativa da API: http://127.0.0.1:8000/docs

| Método | Caminho | O que faz |
|---|---|---|
| GET | `/api/salas` | Lista salas |
| POST | `/api/salas` | Cadastra sala |
| GET | `/api/salas/{id}` | Consulta sala |
| GET | `/api/salas/livres?inicio=&fim=&local=&capacidade_minima=` | Salas livres no intervalo |
| POST | `/api/reservas` | Cria reserva (status `ATIVA`) |
| GET | `/api/reservas?data=AAAA-MM-DD&sala_id=` | Agenda do dia (inclui canceladas) |
| GET | `/api/reservas/{id}` | Consulta reserva |
| POST | `/api/reservas/{id}/cancelar` | Cancela reserva futura (status `CANCELADA`) |
| GET | `/api/relatorios/ocupacao?data=AAAA-MM-DD` | Taxa de ocupação por sala no dia |
