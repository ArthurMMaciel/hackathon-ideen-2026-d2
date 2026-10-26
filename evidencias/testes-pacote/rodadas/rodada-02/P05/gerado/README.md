# Chamados de suporte com prazo

Registra chamados do suporte interno com prazo de resolução por prioridade (CRITICA 4h, ALTA 8h, MEDIA 24h, BAIXA 72h), controla o fluxo `ABERTO → EM_ATENDIMENTO → RESOLVIDO → FECHADO` (com reabertura até 7 dias após a resolução), mostra a fila dos não resolvidos com a indicação `ATRASADO` e emite o relatório de cumprimento de prazo por prioridade. Sem login. Começa com 6 chamados de exemplo fictícios.

Documentos: [docs/PRD.md](docs/PRD.md) (requisitos) e [docs/SPEC.md](docs/SPEC.md) (contrato da API, modelo de dados, plano de testes).

## Requisitos

Python 3.11 ou superior. Todos os comandos rodam a partir desta pasta (`gerado/`). Abaixo, `PY` é `.venv/Scripts/python` no Windows e `.venv/bin/python` no Linux e no macOS.

## Comandos

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite (sobe o servidor real e grava `../evidencias/criterios-aceite.md`) | `PY verificacao/verificar_ca.py` |
| Subida manual conferida (grava `../evidencias/subida-manual.md`) | `PY verificacao/subida_manual.py` |

Com o servidor rodando:

- Tela: http://127.0.0.1:8000/ (abrir chamado, fila, mudar situação, relatório)
- Documentação da API: http://127.0.0.1:8000/docs

O banco SQLite fica em `dados/app.db` (criado na primeira subida; `APP_DB` muda o caminho). Para fixar o relógio do servidor, defina `APP_AGORA` com data e hora ISO 8601 com fuso, por exemplo `2030-01-07T09:00:00-03:00`.

## API

| Método e caminho | O que faz |
|---|---|
| `POST /api/chamados` | Abre chamado (`titulo`, `descricao`, `solicitante_nome`, `solicitante_email`, `categoria`, `prioridade`) |
| `GET /api/chamados` | Lista todos os chamados |
| `GET /api/chamados/{id}` | Consulta um chamado |
| `POST /api/chamados/{id}/assumir` | `ABERTO → EM_ATENDIMENTO`, corpo `{"responsavel": "..."}` |
| `POST /api/chamados/{id}/resolver` | `EM_ATENDIMENTO → RESOLVIDO`, corpo `{"solucao": "..."}` |
| `POST /api/chamados/{id}/fechar` | `RESOLVIDO → FECHADO` |
| `POST /api/chamados/{id}/reabrir` | `RESOLVIDO → EM_ATENDIMENTO`, até 7 dias depois da resolução |
| `GET /api/fila` | Não resolvidos, por prazo, com `indicacao` `ATRASADO` ou `NO_PRAZO` |
| `GET /api/relatorio?data_inicial=AAAA-MM-DD&data_final=AAAA-MM-DD` | Por prioridade: resolvidos, dentro do prazo e percentual |

Erros de negócio: `{"erro": "<CODIGO>", "mensagem": "..."}` com 404, 409 ou 422.
