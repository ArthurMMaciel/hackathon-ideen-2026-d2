# Reembolso de despesas

Sistema local para o colaborador lançar despesas de viagem, o gestor aprovar ou recusar, o financeiro marcar como paga e todos verem o resumo do mês (só despesas `APROVADA` e `PAGA`). Sem login: o colaborador informa nome e e-mail ao lançar.

- Regras: valor maior que zero; limite por despesa (ALIMENTACAO R$ 120,00, HOSPEDAGEM R$ 450,00, TRANSPORTE e OUTROS R$ 1.000,00); data entre hoje e 60 dias atrás; comprovante único por colaborador; fluxo `PENDENTE → APROVADA | RECUSADA (com motivo)`, `APROVADA → PAGA`; só `PENDENTE` pode ser excluída.
- O banco SQLite fica em `dados/app.db` e começa com 5 despesas fictícias.
- Requisitos e contrato: [docs/PRD.md](docs/PRD.md) e [docs/SPEC.md](docs/SPEC.md).

## Comandos

Rode a partir desta pasta (`gerado/`). No Windows, `PY` é `.venv/Scripts/python`; no Linux e no macOS, `.venv/bin/python`.

| Ação | Comando |
|---|---|
| Criar ambiente | `python -m venv .venv` |
| Instalar | `PY -m pip install -r requirements.txt` |
| Testar | `PY -m pytest -q` |
| Rodar | `PY -m uvicorn app.main:app --port 8000` |
| Verificar critérios de aceite (sobe o servidor real, grava `../evidencias/criterios-aceite.md`) | `PY verificacao/verificar_ca.py` |
| Subida manual conferida (grava `../evidencias/subida-manual.md`) | `PY verificacao/subida_manual.py` |

Variáveis opcionais: `APP_DB` (caminho do banco) e `APP_AGORA` (fixa o relógio, ISO 8601 com fuso, ex.: `2030-01-07T09:00:00-03:00`).

## Endereços

- Tela: http://127.0.0.1:8000/
- Documentação da API: http://127.0.0.1:8000/docs

## API

| Método | Caminho | O que faz |
|---|---|---|
| POST | `/api/despesas` | Lança despesa (`valor_centavos` inteiro; nasce `PENDENTE`) |
| GET | `/api/despesas?email=&situacao=` | Lista com filtros opcionais |
| POST | `/api/despesas/{id}/aprovar` | Aprova |
| POST | `/api/despesas/{id}/recusar` | Recusa; corpo `{"motivo": "..."}` obrigatório |
| POST | `/api/despesas/{id}/pagar` | Marca como paga |
| DELETE | `/api/despesas/{id}` | Exclui (só `PENDENTE`) |
| GET | `/api/relatorios/mensal?mes=AAAA-MM` | Total por categoria e total geral do mês |
