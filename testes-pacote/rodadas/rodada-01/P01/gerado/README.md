# Empréstimo de equipamentos

Sistema simples para controlar notebooks, projetores e headsets emprestados: cadastro de equipamentos,
registro de empréstimo e devolução, consulta de disponíveis e de atrasados e relatório mensal por tipo.
Sem login. Dados num SQLite local em `dados/app.db`, criado na primeira execução com 8 equipamentos fictícios
(3 notebooks, 2 projetores e 3 headsets, um deles em manutenção).

Documentos: [docs/PRD.md](docs/PRD.md) (o quê) e [docs/SPEC.md](docs/SPEC.md) (contrato da API, regras e plano de testes).

## Requisitos

Python 3.11 ou superior. Todos os comandos rodam a partir desta pasta (`gerado/`).
No Windows, `PY` é `.venv/Scripts/python`; no Linux e no macOS, `.venv/bin/python`.

## Instalar

```
python -m venv .venv
PY -m pip install -r requirements.txt
```

## Testar

```
PY -m pytest -q
```

## Rodar

```
PY -m uvicorn app.main:app --port 8000
```

- Tela web: http://127.0.0.1:8000/ (emprestar, devolver, ver em aberto e atrasados)
- Documentação interativa da API: http://127.0.0.1:8000/docs
- Variáveis opcionais: `APP_DB` (caminho do banco, padrão `dados/app.db`) e `APP_AGORA` (fixa o relógio, ISO 8601 com offset, ex. `2030-01-07T09:00:00-03:00`).

## Verificar critérios de aceite

```
PY verificacao/verificar_ca.py
```

Sobe o servidor real em porta livre, executa CA-01 a CA-10 via HTTP e grava `../evidencias/criterios-aceite.md`.

## API

| Método | Caminho | O que faz |
|---|---|---|
| POST | `/api/equipamentos` | Cadastra equipamento (`patrimonio` EQ-0000, `tipo`, `descricao`) |
| GET | `/api/equipamentos?tipo=&situacao=` | Lista equipamentos; disponíveis: `?situacao=DISPONIVEL&tipo=PROJETOR` |
| GET | `/api/equipamentos/{id}` | Consulta um equipamento |
| POST | `/api/emprestimos` | Registra empréstimo (`equipamento_id`, `nome`, `email`, `data_prevista` AAAA-MM-DD) |
| GET | `/api/emprestimos?status=` | Lista empréstimos (`ABERTO` ou `DEVOLVIDO`) |
| GET | `/api/emprestimos/atrasados` | Empréstimos em aberto vencidos, com `dias_atraso` |
| POST | `/api/emprestimos/{id}/devolver` | Registra devolução (`{"defeito": true\|false}`) |
| GET | `/api/relatorios/emprestimos-por-tipo?mes=AAAA-MM` | Quantidade de empréstimos por tipo no mês |

Regras principais: só equipamento `DISPONIVEL` é emprestado; prazo máximo de 14 dias (notebook) ou 3 dias
(projetor e headset) contados da retirada; no máximo 2 empréstimos em aberto por e-mail; devolução com defeito
manda o equipamento para `MANUTENCAO`.
