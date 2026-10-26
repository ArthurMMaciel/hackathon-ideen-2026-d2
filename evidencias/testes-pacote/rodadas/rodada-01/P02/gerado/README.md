# Reembolso de despesas

Sistema simples para o colaborador lançar despesas de viagem, o gestor aprovar ou recusar, o financeiro marcar como paga e todos verem o resumo do mês. Sem login: a pessoa informa nome e e-mail. Documentação: [docs/PRD.md](docs/PRD.md) e [docs/SPEC.md](docs/SPEC.md).

- Categorias e limites por despesa: ALIMENTACAO até R$ 120,00; HOSPEDAGEM até R$ 450,00; TRANSPORTE e OUTROS até R$ 1.000,00.
- Data da despesa entre hoje − 60 dias e hoje (fuso America/Sao_Paulo).
- Fluxo: PENDENTE → APROVADA → PAGA, ou PENDENTE → RECUSADA (com motivo). Só PENDENTE pode ser excluída.
- O banco SQLite fica em `dados/app.db` e começa com 5 despesas fictícias.

## Comandos (a partir desta pasta)

`PY` é `.venv/Scripts/python` no Windows e `.venv/bin/python` no Linux/macOS.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite | `PY verificacao/verificar_ca.py` (grava `../evidencias/criterios-aceite.md`) |

Variáveis opcionais: `APP_DB` (caminho do banco) e `APP_AGORA` (fixa o relógio, ISO 8601 com offset, ex.: `2030-01-07T09:00:00-03:00`).

## Tela e API

- Tela: http://127.0.0.1:8000/
- Documentação interativa da API: http://127.0.0.1:8000/docs

| Método | Caminho | O que faz |
|---|---|---|
| POST | `/api/despesas` | Lança despesa (nasce PENDENTE) |
| GET | `/api/despesas?email=&situacao=` | Lista com filtros |
| GET | `/api/despesas/{id}` | Consulta uma despesa |
| POST | `/api/despesas/{id}/aprovar` | PENDENTE → APROVADA |
| POST | `/api/despesas/{id}/recusar` | PENDENTE → RECUSADA, corpo `{"motivo": "..."}` |
| POST | `/api/despesas/{id}/pagar` | APROVADA → PAGA |
| DELETE | `/api/despesas/{id}` | Exclui despesa PENDENTE |
| GET | `/api/relatorios/mensal?mes=AAAA-MM` | Totais por categoria e geral (só APROVADA e PAGA) |
