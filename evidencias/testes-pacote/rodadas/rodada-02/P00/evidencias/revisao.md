# Revisão de qualidade

Revisão feita contra `docs/PRD.md` e `docs/SPEC.md`, abrindo cada arquivo de `app/`, `tests/` e a tela.

## Testes

- Antes das correções: `69 passed, 1 warning in 9.10s`
- Depois das correções: `70 passed, 1 warning in 7.37s` (um teste novo: `test_rn_02_fracao_de_segundo_descartada`)

## Achados

| # | Gravidade | Descrição | Arquivo | Regra | Status |
|---|---|---|---|---|---|
| 1 | Médio | Horário com fração de segundo (`10:00:00.700`) era validado com a fração, mas gravado truncado por `relogio.para_banco`; a resposta devolvia um horário diferente do enviado e a duração validada não era a gravada. | `app/rotas/modelos.py:16`, `app/rotas/salas.py:27` | RN-02, RN-01 | CORRIGIDO: tipo `HorarioReserva` descarta a fração na entrada (reserva e salas livres); SPEC atualizada; teste `test_rn_02_fracao_de_segundo_descartada` |
| 2 | Baixo | Mensagens de validação de formato (422 do framework) saem em inglês ("Input should be...") e a tela as mostra assim. | `app/main.py` | Idioma | ACEITO: regras transversais mandam usar o 422 padrão do framework para validação de formato; erros de negócio estão em português |
| 3 | Baixo | `GET /api/saude` não está na SPEC. | `app/main.py` | — | ACEITO: vem do modelo de projeto e é usado pelo harness de verificação |
| 4 | Baixo | A tela acrescenta o offset fixo `-03:00` ao `datetime-local`; um navegador em outro fuso envia o horário como se fosse de São Paulo. | `app/estatico/index.html` | PR-01 | ACEITO: decisão registrada na SPEC (fuso único do sistema, sem horário de verão) |

## Checklist

**Aderência**
- [x] Rastreabilidade da SPEC conferida linha a linha: RF-01 `POST /api/salas`; RF-02 `GET /api/salas`, `GET /api/salas/{id}`; RF-03 `banco.carga_inicial`; RF-04 `POST /api/reservas`; RF-05 `GET /api/reservas`; RF-06 `POST /api/reservas/{id}/cancelar`; RF-07 `GET /api/salas/livres`; RF-08 `GET /api/relatorios/ocupacao`; RF-09 rotas `/api`; RF-10 tela em `/`; RF-11 SQLite, sem login. RN-01..RN-10 nas funções listadas na SPEC com comentário `# RN-xx`.
- [x] Enums e status exatamente do pedido: `SAO_PAULO`, `ARARAQUARA`, `COWORKING`, `TV`, `VIDEOCONFERENCIA`, `QUADRO`, `ATIVA`, `CANCELADA`.
- [x] Carga inicial: 6 salas, 2 por local (`test_rf_03_carga_inicial_seis_salas`).

**Testes**
- [x] Todo CA tem teste que confere status e campo do corpo (`status`, `erro`, `minutos_ocupados`, `taxa_ocupacao`, ids da lista).
- [x] Regras com limite testadas no limite, abaixo e acima: RN-02 (14/15/16 min, 3h59/4h/4h01), RN-03 (08:59/09:00/09:01), RN-04 (3/4/5 para capacidade 4, e 0), RN-05 (09:59/10:00/10:30 para início 10:00), RN-07 (capacidade mínima 6/7/8 para sala de 7), RN-08 (bordas 08:00 e 18:00), RN-09 (0/1/1000/1001).
- [x] Regras de tempo usam o `relogio` de teste; nenhum teste usa a hora real.

**Erros e valores extremos** (sonda com `TestClient`, `raise_server_exceptions=False`)

| Requisição | Status |
|---|---|
| `GET /api/salas/99999999999999999999` | 422 |
| `GET /api/salas/-1` | 422 |
| `POST /api/reservas/99999999999999999999/cancelar` | 422 |
| `POST /api/reservas` com `sala_id` 99999999999999999999 | 422 |
| `POST /api/reservas` com início no ano 9999 | 422 |
| `POST /api/reservas` com início no ano 0001 | 422 |
| `POST /api/reservas` com título só com espaços | 422 |
| `POST /api/reservas` com título de 5000 caracteres | 422 |
| `POST /api/reservas` com participantes -1 | 422 |
| `POST /api/reservas` com participantes `"１２"` | 422 |
| `POST /api/reservas` com e-mail sem arroba | 422 |
| `POST /api/reservas` corpo vazio | 422 |
| `POST /api/reservas` com fração de segundo | 201 (achado 1, corrigido) |
| `POST /api/salas` com nome de 5000 caracteres / só espaços | 422 / 422 |
| `POST /api/salas` com capacidade -5 / `"１２"` | 422 / 422 |
| `POST /api/salas` com recursos `"TV"` (não lista) / 4 itens | 422 / 422 |
| `GET /api/salas/livres` com ano 9999 / sem fuso | 422 / 422 |
| `GET /api/salas/livres` com capacidade_minima -1 / `"１２"` / local `RIO` | 422 / 422 / 422 |
| `GET /api/reservas` com dia 9999-01-01 / 0001-01-01 / sem dia | 422 / 422 / 422 |
| `GET /api/reservas` com sala_id gigante | 422 |
| `GET /api/relatorios/ocupacao` com dia 9999-12-31 / `２０３０-01-08` | 422 / 422 |
| `GET /api/relatorios/ocupacao` com dia 2100-12-31 (limite) | 200 |

- [x] Nenhum 500. Erros de negócio em `{"erro", "mensagem"}`, mensagem em português; 409 para conflito, já cancelada e não futura (estado guardado); 422 para duração, passado, capacidade, intervalo e recursos repetidos; 404 para sala e reserva inexistentes.

**Estrutura**
- [x] `app/dominio/` importa só `datetime`, `decimal`, `zoneinfo` e módulos do próprio domínio (sem `fastapi`, sem `sqlite3`).
- [x] SQL só em `app/repositorio/` e DDL/carga em `app/banco.py` (grep por `execute|SELECT|INSERT|UPDATE` fora deles: nada).
- [x] `datetime.now` só em `app/relogio.py`.
- [x] Criação de sala (nome único), criação de reserva (conflito) e cancelamento (status) dentro de `banco.transacao`.
- [x] Carga inicial sem datas; não usa relógio.

**Tela**
- [x] Ações da SPEC: reservar, ver agenda do dia (com filtro de sala), cancelar, buscar salas livres, calcular ocupação; erros da API exibidos com `mostrarMensagem` (ex.: `CAPACIDADE_EXCEDIDA` devolve mensagem em português).
- [x] Todo `getElementById` aponta para id existente (script de conferência: nenhum faltando); `node --check` do script extraído: OK (Node v22.23.2).
- [x] Endpoints chamados com os parâmetros que a tela envia: `GET /api/salas` 200; `POST /api/reservas` (horário `AAAA-MM-DDTHH:MM:00-03:00`) 201; `GET /api/reservas?dia=` 200; `GET /api/reservas?dia=&sala_id=` 200; `POST /api/reservas/{id}/cancelar` 200; `GET /api/salas/livres?inicio=&fim=&capacidade_minima=` 200; `GET /api/relatorios/ocupacao?dia=` 200.
