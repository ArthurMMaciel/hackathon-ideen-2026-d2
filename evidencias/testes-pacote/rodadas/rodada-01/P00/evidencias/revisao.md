# Revisão de qualidade

Sistema: `gerado/` (Reserva de salas). Referências: `gerado/docs/PRD.md`, `gerado/docs/SPEC.md`.

## Testes

| Momento | Comando | Resultado |
|---|---|---|
| Antes da revisão | `.venv/Scripts/python -m pytest -q` | `44 passed, 1 warning` |
| Depois das correções | `.venv/Scripts/python -m pytest -q` | `58 passed, 1 warning` |

O aviso é `DeprecationWarning` do `anyio` dentro de `starlette/testclient.py` (dependência transitiva), sem relação com o código gerado.

## Checklist

**Aderência**
- [x] Cada RF e RN implementado como a SPEC descreve. Conferido linha a linha pela tabela de rastreabilidade: RF-01 `POST /api/salas`; RF-02 `GET /api/salas`, `GET /api/salas/{id}`; RF-03 `banco.carga_inicial`; RF-04 `POST /api/reservas`, `GET /api/reservas/{id}`; RF-05 `/cancelar`; RF-06 `/api/salas/livres`; RF-07 `/api/relatorios/ocupacao`; RF-08 `GET /api/reservas?data=`; RF-09 todos em `/api`; RF-10 `/`; RF-11 SQLite local, sem autenticação. RN-01..RN-11 nas funções listadas na SPEC (`app/dominio/reservas.py`, `salas.py`, `ocupacao.py`, `app/rotas/modelos.py`), cada uma com comentário `# RN-xx`.
- [x] Enums e status exatamente como no pedido: `SAO_PAULO`, `ARARAQUARA`, `COWORKING`, `TV`, `VIDEOCONFERENCIA`, `QUADRO`, `ATIVA`, `CANCELADA` (CHECK no DDL e `Literal` nos modelos).
- [x] Carga inicial: 6 salas, 2 por local, idempotente (`test_rf_03_carga_inicial` reinicia no mesmo banco).

**Testes**
- [x] Todo CA confere status e campo do corpo (`status`, `erro`, `minutos_ocupados`, `taxa_ocupacao`, nomes das salas livres).
- [x] Limites com teste no limite, abaixo e acima: RN-02 (14/15/16 e 239/240/241 min), RN-03 (−1/0/+1 min), RN-04 (3/4/5 e 0), RN-05 (início −1 min, = agora, em andamento), RN-08 (bordas 08:00 e 18:00), RN-10 (0/1/500/501).
- [x] Regras de tempo usam o `relogio` de teste (`AGORA_INICIAL` 2030-01-07 09:00, `avancar()`); nenhum teste depende da hora real.

**Erros**
- [x] Entradas inválidas comuns retornam 4xx: campo faltando, tipo errado, id inexistente (404) e data sem fuso (422) testados. **Antes da correção**, ids acima do inteiro de 64 bits e datas nos anos 1 ou 9999 davam 500 (achados R-01 e R-02).
- [x] Erros de negócio no formato `{"erro", "mensagem"}`, mensagens em português.

**Estrutura**
- [x] `app/dominio/` não importa FastAPI nem `sqlite3` diretamente (`grep -rn "fastapi\|sqlite3" app/dominio/` vazio). Ver achado R-04 sobre a importação indireta via `app.erros`.
- [x] SQL só em `app/repositorio/` e DDL em `app/banco.py`.
- [x] Nenhum `datetime.now()` fora de `app/relogio.py`.
- [x] Escritas que dependem de leitura dentro de `banco.transacao`: criar sala (nome único), criar reserva (sala, capacidade, conflito), cancelar (status, início).

**Tela**
- [x] Executa as ações da SPEC e mostra o erro da API. Conferido no navegador contra o servidor real (relógio fixo em 2030-01-07 09:00): reserva criada ("Reserva 1 criada com status ATIVA."), segunda reserva no mesmo horário mostrou "Erro: Conflito de horário: ...", salas livres listadas com filtro, botão Cancelar mudou a linha para CANCELADA e zerou a ocupação, título `<b>Teste</b>` apareceu literal (nenhum elemento `<b>` criado).
- [x] Abre sem erro de JavaScript: o console só registrou o 409 esperado da tentativa de conflito; todos os IDs usados no script existem no HTML.

## Achados

| ID | Gravidade | Descrição | Arquivo | Status |
|---|---|---|---|---|
| R-01 | Alto | `sala_id`/`reserva_id` acima de 2^63−1 (caminho, consulta ou corpo) causava `OverflowError` no driver SQLite: HTTP 500. | `app/rotas/salas.py`, `app/rotas/reservas.py`, `app/rotas/modelos.py` | CORRIGIDO: limite `le=2**63-1` em `Path`, `Query` e no tipo `Id`; testes `test_robustez_*` |
| R-02 | Alto | Datas extremas (ano 1 ou 9999) estouravam na conversão para UTC ou no cálculo do dia seguinte: HTTP 500 em `POST /api/reservas`, `GET /api/reservas`, `GET /api/salas/livres`. | `app/rotas/modelos.py`, rotas | CORRIGIDO: tipos `DataHora`/`Data` com ano entre 2000 e 2100 (nova premissa PR-10 no PRD, limite na SPEC); `Annotated[..., Query()]` para o validador valer também em parâmetros de consulta; testes `test_robustez_*` |
| R-03 | Médio | Faltavam testes de "campo faltando" e "tipo errado" pedidos no checklist. | `tests/` | CORRIGIDO: `test_robustez_campo_faltando`, `test_robustez_corpo_invalido` |
| R-04 | Baixo | `app/dominio/*` importa `app.erros`, que importa `fastapi` (Request, JSONResponse). O domínio não importa FastAPI diretamente, mas depende dele de forma indireta. | `app/erros.py` (modelo) | ACEITO: é o desenho do modelo de projeto, que manda o domínio levantar `regra_violada`/`conflito`; mudar exigiria reescrever `erros.py` |
| R-05 | Baixo | Mensagens de validação de formato (422 padrão) vêm em inglês do Pydantic e a tela mostra o JSON de `detail`. | `app/estatico/index.html` | ACEITO: as regras transversais definem o 422 de formato como padrão do framework; os formulários usam `required`/`min`/`type` e evitam a maior parte desses casos |
| R-06 | Baixo | Na agenda, reserva que atravessa a meia-noite mostra só as horas (ex.: 22:00–02:00), sem a data. | `app/estatico/index.html` | ACEITO: caso raro, a API devolve a data completa |
