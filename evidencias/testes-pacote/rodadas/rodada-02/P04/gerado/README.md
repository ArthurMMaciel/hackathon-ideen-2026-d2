# Férias da equipe

Sistema para colaboradores pedirem férias, o gestor aprovar ou reprovar sem deixar mais de uma pessoa da mesma equipe (`DADOS`, `PRODUTO`, `SUPORTE`) de férias no mesmo dia, e um calendário mensal de quem está de férias. Sem login. Dados em SQLite local (`dados/app.db`), criado e carregado com 9 colaboradores fictícios na primeira subida.

Documentos: [docs/PRD.md](docs/PRD.md) (requisitos) e [docs/SPEC.md](docs/SPEC.md) (contrato da API, regras, plano de testes).

## Regras principais
- Período de 5 a 30 dias corridos, contando o primeiro e o último dia.
- Início com pelo menos 30 dias de antecedência.
- Dias pedidos ≤ saldo disponível (saldo − dias das solicitações pendentes); ao aprovar, os dias saem do saldo.
- Sem duas solicitações ativas do mesmo colaborador com dias em comum.
- No máximo 1 pessoa por equipe com férias aprovadas em um mesmo dia.
- Cancelamento até o dia anterior ao início; aprovada cancelada devolve os dias.

## Comandos (a partir desta pasta)

No Windows `PY` é `.venv/Scripts/python`; no Linux e no macOS, `.venv/bin/python`.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite (sobe servidor real, grava `../evidencias/criterios-aceite.md`) | `PY verificacao/verificar_ca.py` |
| Subida manual conferida (grava `../evidencias/subida-manual.md`) | `PY verificacao/subida_manual.py` |

Variáveis opcionais: `APP_DB` (caminho do banco, padrão `dados/app.db`) e `APP_AGORA` (fixa o relógio, ISO 8601 com fuso, ex.: `2030-01-07T09:00:00-03:00`).

## Endereços
- Tela: <http://127.0.0.1:8000/>
- Documentação da API: <http://127.0.0.1:8000/docs>

## API
| Método | Caminho | O que faz |
|---|---|---|
| POST | `/api/colaboradores` | cadastra colaborador (`nome`, `email`, `equipe`, `saldo` opcional, padrão 30) |
| GET | `/api/colaboradores` | lista colaboradores com `saldo` e `saldo_disponivel` |
| GET | `/api/colaboradores/{id}` | consulta um colaborador |
| POST | `/api/solicitacoes` | solicita férias (`colaborador_id`, `inicio`, `fim` em `AAAA-MM-DD`) |
| GET | `/api/solicitacoes` | lista solicitações |
| GET | `/api/solicitacoes/{id}` | consulta uma solicitação |
| POST | `/api/solicitacoes/{id}/aprovar` | aprova |
| POST | `/api/solicitacoes/{id}/reprovar` | reprova |
| POST | `/api/solicitacoes/{id}/cancelar` | cancela |
| GET | `/api/calendario?mes=AAAA-MM` | quem está de férias aprovadas em cada dia do mês, por equipe |
