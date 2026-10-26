# Inscrição em treinamentos

Cadastro de turmas de treinamento interno, inscrições com lista de espera automática, cancelamento com promoção da espera, registro de presença e taxa de presença por turma. Sem login. Dados em SQLite local (`dados/app.db`).

Requisitos em `docs/PRD.md`; contrato da API e plano de testes em `docs/SPEC.md`.

## Comandos

Rode tudo a partir desta pasta (`gerado/`). No Windows, `PY` é `.venv/Scripts/python`; no Linux e no macOS, `.venv/bin/python`.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite via HTTP | `PY verificacao/verificar_ca.py` (grava `../evidencias/criterios-aceite.md`) |
| Subida manual conferida | `PY verificacao/subida_manual.py` (grava `../evidencias/subida-manual.md`) |

Com o servidor rodando:

- Tela: http://127.0.0.1:8000/ (turmas futuras, inscrição, inscritos de uma turma)
- Documentação da API: http://127.0.0.1:8000/docs

A variável `APP_AGORA` (ISO 8601 com offset, ex.: `2030-01-07T09:00:00-03:00`) fixa o relógio do servidor; `APP_DB` troca o arquivo do banco. Na primeira subida com banco vazio, o sistema cria 3 turmas futuras (7, 14 e 21 dias à frente).

## API

| Método | Caminho | O que faz |
|---|---|---|
| POST | `/api/turmas` | Cadastra turma (`titulo`, `inicio`, `duracao_minutos` 1–1440, `modalidade` PRESENCIAL/ONLINE, `vagas` 1–50) |
| GET | `/api/turmas` | Turmas futuras com `vagas_restantes` |
| GET | `/api/turmas/{id}` | Uma turma |
| GET | `/api/turmas/{id}/inscricoes` | Inscritos da turma, por ordem de chegada, com `posicao_espera` |
| GET | `/api/turmas/{id}/relatorio-presenca` | Presentes, ausentes e `taxa_presenca_percentual` |
| POST | `/api/inscricoes` | Inscreve (`turma_id`, `nome`, `email`): CONFIRMADA ou ESPERA |
| POST | `/api/inscricoes/{id}/cancelar` | Cancela; se era CONFIRMADA, promove a primeira da ESPERA |
| POST | `/api/inscricoes/{id}/presenca` | Marca `PRESENTE` ou `AUSENTE` (só CONFIRMADA, só depois do início) |

Erros de negócio: `{"erro": "<CODIGO>", "mensagem": "<texto>"}` com 404, 409 ou 422.
