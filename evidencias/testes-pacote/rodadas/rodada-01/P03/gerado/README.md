# Inscrição em treinamentos

Sistema local para cadastrar turmas de treinamentos internos, receber inscrições com lista de espera automática, cancelar (com promoção da espera), marcar presença e calcular a taxa de presença. Sem login. Requisitos em `docs/PRD.md`; contrato da API em `docs/SPEC.md`.

## O que faz

- Turmas: cadastro (título, início com fuso, duração em minutos, `PRESENCIAL`/`ONLINE`, 1 a 50 vagas). Começa com 3 turmas futuras fictícias.
- Inscrições: nasce `CONFIRMADA` se há vaga, senão `ESPERA` por ordem de chegada; um e-mail ativo por turma; fecham 24 h antes do início.
- Cancelamento até o início; cancelar uma `CONFIRMADA` promove a primeira da `ESPERA`.
- Presença (`PRESENTE`/`AUSENTE`) só depois do início e só para `CONFIRMADA`.
- Consulta de turmas futuras com vagas restantes e taxa de presença por turma.

## Comandos (a partir desta pasta)

No Windows, `PY` = `.venv/Scripts/python`; no Linux/macOS, `PY` = `.venv/bin/python`.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite | `PY verificacao/verificar_ca.py` (grava `../evidencias/criterios-aceite.md`) |

Variáveis opcionais: `APP_DB` (caminho do banco SQLite, padrão `dados/app.db`) e `APP_AGORA` (fixa o relógio do servidor, ISO 8601 com offset, ex.: `2030-01-07T09:00:00-03:00`).

## Tela

Com o servidor rodando: <http://127.0.0.1:8000/> — turmas futuras, formulário de inscrição e lista de inscritos por turma.

## API

| Método | Caminho | Uso |
|---|---|---|
| POST | `/api/turmas` | cadastrar turma |
| GET | `/api/turmas` | turmas futuras com vagas restantes |
| GET | `/api/turmas/{id}` | consultar turma |
| POST | `/api/turmas/{id}/inscricoes` | inscrever (`nome`, `email`) |
| GET | `/api/turmas/{id}/inscricoes` | inscritos da turma |
| POST | `/api/inscricoes/{id}/cancelar` | cancelar inscrição |
| POST | `/api/inscricoes/{id}/presenca` | marcar `PRESENTE` ou `AUSENTE` |
| GET | `/api/turmas/{id}/taxa-presenca` | taxa de presença (%) |
| GET | `/api/saude` | saúde |

Documentação interativa em `/docs`.
