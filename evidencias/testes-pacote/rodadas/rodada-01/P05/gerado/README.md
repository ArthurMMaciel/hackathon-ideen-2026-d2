# Chamados de suporte com prazo

Sistema local para o suporte interno: abrir chamado, assumir, resolver, fechar e reabrir (até 7 dias depois da resolução), com prazo de resolução por prioridade (`CRITICA` 4h, `ALTA` 8h, `MEDIA` 24h, `BAIXA` 72h, em horas corridas), fila dos não resolvidos com indicação `ATRASADO` e relatório de cumprimento de prazo por prioridade. Sem login. Começa com 6 chamados de exemplo fictícios.

Documentos: [docs/PRD.md](docs/PRD.md) (requisitos) e [docs/SPEC.md](docs/SPEC.md) (contrato da API, modelo de dados, plano de testes).

## Requisitos

Python 3.11 ou superior.

## Comandos (a partir desta pasta, `gerado/`)

No Windows, `PY` = `.venv/Scripts/python`; no Linux/macOS, `PY` = `.venv/bin/python`.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite | `PY verificacao/verificar_ca.py` (grava `../evidencias/criterios-aceite.md`) |

- Tela web: <http://127.0.0.1:8000/>
- Documentação interativa da API: <http://127.0.0.1:8000/docs>
- Banco SQLite em `dados/app.db` (criado na primeira subida; apague-o para recomeçar com os dados de exemplo).
- `APP_AGORA=2030-01-07T09:00:00-03:00` fixa o relógio do servidor (usado na verificação). `APP_DB` troca o arquivo do banco.

## API

| Método e caminho | O que faz |
|---|---|
| `POST /api/chamados` | Abre chamado (`titulo`, `descricao`, `solicitante_nome`, `solicitante_email`, `categoria`, `prioridade`) |
| `GET /api/chamados` | Lista todos os chamados |
| `GET /api/chamados/{id}` | Consulta um chamado |
| `GET /api/chamados/fila` | Não resolvidos ordenados pelo prazo, com `indicacao` `ATRASADO` |
| `POST /api/chamados/{id}/assumir` | `ABERTO` → `EM_ATENDIMENTO` (`{"responsavel": "..."}`) |
| `POST /api/chamados/{id}/resolver` | `EM_ATENDIMENTO` → `RESOLVIDO` (`{"solucao": "..."}`) |
| `POST /api/chamados/{id}/fechar` | `RESOLVIDO` → `FECHADO` |
| `POST /api/chamados/{id}/reabrir` | `RESOLVIDO` → `EM_ATENDIMENTO`, até 7 dias após a resolução |
| `GET /api/relatorios/prazo?data_inicial=AAAA-MM-DD&data_final=AAAA-MM-DD` | Por prioridade: resolvidos no período e percentual dentro do prazo |

Datas e horas em ISO 8601 com offset (fuso America/Sao_Paulo). Erros de regra: `{"erro": "CODIGO", "mensagem": "..."}`.
