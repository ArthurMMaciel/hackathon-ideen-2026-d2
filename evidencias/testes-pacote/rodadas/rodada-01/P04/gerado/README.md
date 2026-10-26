# Férias da equipe

Sistema para colaboradores pedirem férias, o gestor aprovar ou reprovar sem deixar mais de uma pessoa da mesma equipe fora no mesmo dia, e um calendário mensal de quem está de férias. Sem login. Dados em SQLite local (`dados/app.db`), com 9 colaboradores fictícios carregados na primeira execução.

Documentos: `docs/PRD.md` (requisitos) e `docs/SPEC.md` (contrato da API, regras e plano de testes).

## Comandos

Rode a partir desta pasta (`gerado/`). No Windows, `PY` = `.venv/Scripts/python`; no Linux/macOS, `.venv/bin/python`.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite | `PY verificacao/verificar_ca.py` (sobe o servidor real em porta livre e grava `../evidencias/criterios-aceite.md`) |

Tela web: http://127.0.0.1:8000/ · Documentação interativa da API: http://127.0.0.1:8000/docs

Variáveis opcionais: `APP_DB` (caminho do banco) e `APP_AGORA` (fixa o relógio, ISO 8601 com offset, ex.: `2030-01-07T09:00:00-03:00`).

## API

| Método | Caminho | O que faz |
|---|---|---|
| GET | `/api/colaboradores` | Lista colaboradores com saldo e saldo disponível |
| GET | `/api/colaboradores/{id}` | Consulta um colaborador e seu saldo |
| POST | `/api/colaboradores` | Cadastra colaborador (`nome`, `email`, `equipe`, `saldo` opcional = 30) |
| GET | `/api/solicitacoes` | Lista solicitações (filtros `situacao`, `colaborador_id`) |
| POST | `/api/solicitacoes` | Solicita férias (`colaborador_id`, `inicio`, `fim` em `AAAA-MM-DD`) |
| POST | `/api/solicitacoes/{id}/aprovar` | Aprova (desconta do saldo) |
| POST | `/api/solicitacoes/{id}/reprovar` | Reprova |
| POST | `/api/solicitacoes/{id}/cancelar` | Cancela até a véspera do início (devolve saldo se aprovada) |
| GET | `/api/calendario?mes=AAAA-MM` | Quem está de férias aprovadas em cada dia, por equipe |

Regras principais: 5 a 30 dias corridos (contando início e fim); início com pelo menos 30 dias de antecedência; dias não podem passar do saldo disponível (saldo menos pedidos pendentes); no máximo 1 pessoa por equipe com férias aprovadas no mesmo dia. Erros de negócio voltam como `{"erro": "CODIGO", "mensagem": "..."}`.
