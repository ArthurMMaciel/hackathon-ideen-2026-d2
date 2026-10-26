# SPEC · Reserva de salas

Stack padrão (Python 3.11, FastAPI, SQLite em `dados/app.db`, pytest). Datas e horas na API em ISO 8601 com offset; no banco, texto UTC no formato de `relogio.para_banco`. Fuso `America/Sao_Paulo` (PR-01). Respostas devolvem horários no fuso padrão (`-03:00`). Frações de segundo em `inicio`/`fim` (reserva e salas livres) são descartadas na entrada, antes das regras, para o valor validado ser o mesmo gravado (decisão da revisão).

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS salas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
  local TEXT NOT NULL CHECK (local IN ('SAO_PAULO', 'ARARAQUARA', 'COWORKING')),
  capacidade INTEGER NOT NULL CHECK (capacidade BETWEEN 1 AND 1000),
  recursos TEXT NOT NULL DEFAULT '[]',
  UNIQUE (nome COLLATE NOCASE, local)
);

CREATE TABLE IF NOT EXISTS reservas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sala_id INTEGER NOT NULL REFERENCES salas(id),
  responsavel_nome TEXT NOT NULL CHECK (length(responsavel_nome) BETWEEN 1 AND 200),
  responsavel_email TEXT NOT NULL CHECK (length(responsavel_email) BETWEEN 3 AND 254),
  titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
  participantes INTEGER NOT NULL CHECK (participantes >= 1),
  inicio TEXT NOT NULL,
  fim TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ATIVA', 'CANCELADA')),
  criada_em TEXT NOT NULL,
  cancelada_em TEXT,
  CHECK (fim > inicio)
);

CREATE INDEX IF NOT EXISTS ix_reservas_sala_inicio ON reservas (sala_id, inicio);
```

`recursos` guarda uma lista JSON de valores de `TV`, `VIDEOCONFERENCIA`, `QUADRO`, na ordem `TV, VIDEOCONFERENCIA, QUADRO` (lista curta, só lida junto da sala; não há consulta por recurso).

## Carga inicial
Só insere quando `salas` está vazia (RF-03). Sem datas. Nenhuma reserva inicial.

| nome | local | capacidade | recursos |
|---|---|---|---|
| Paulista | SAO_PAULO | 8 | TV, VIDEOCONFERENCIA |
| Ibirapuera | SAO_PAULO | 4 | QUADRO |
| Laranjeira | ARARAQUARA | 10 | TV, QUADRO |
| Morada do Sol | ARARAQUARA | 6 | VIDEOCONFERENCIA |
| Coworking Azul | COWORKING | 12 | TV, VIDEOCONFERENCIA, QUADRO |
| Coworking Verde | COWORKING | 3 | (nenhum) |

## Endpoints

Objeto `Sala`: `{"id": 1, "nome": "Paulista", "local": "SAO_PAULO", "capacidade": 8, "recursos": ["TV", "VIDEOCONFERENCIA"]}`.

Objeto `Reserva`: `{"id": 1, "sala_id": 1, "sala_nome": "Paulista", "responsavel_nome": "Ana Teste", "responsavel_email": "ana@exemplo.com", "titulo": "Planejamento", "participantes": 4, "inicio": "2030-01-08T10:00:00-03:00", "fim": "2030-01-08T11:00:00-03:00", "status": "ATIVA"}`.

### GET /api/salas · RF-02
- **Entrada:** nenhuma.
- **Sucesso:** 200 lista de `Sala`, ordenada por local e nome (PR-10).
- **Erros:** nenhum de negócio.

### GET /api/salas/livres · RF-07
- **Entrada (consulta):** `inicio: DataHora` obrigatório; `fim: DataHora` obrigatório; `local: SAO_PAULO|ARARAQUARA|COWORKING` opcional; `capacidade_minima: int 1..1000` opcional.
- **Sucesso:** 200 lista de `Sala` livres (RN-07), ordenada por local e nome.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | INTERVALO_INVALIDO | RN-07 (fim igual ou anterior ao início) |
  | 422 | (validação) | formato, fuso ausente, enum ou faixa |

Declarado antes de `/api/salas/{id}` para não colidir.

### GET /api/salas/{id} · RF-02
- **Entrada (caminho):** `id: Id`.
- **Sucesso:** 200 `Sala`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SALA_NAO_ENCONTRADA | — |

### POST /api/salas · RF-01
- **Entrada (corpo):** `nome: Texto`; `local: SAO_PAULO|ARARAQUARA|COWORKING`; `capacidade: int 1..1000`; `recursos: lista de TV|VIDEOCONFERENCIA|QUADRO`, opcional, padrão `[]`, até 3 itens.
- **Sucesso:** 201 `Sala`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | RECURSOS_REPETIDOS | RN-09 |
  | 409 | SALA_DUPLICADA | RN-10 |
  | 422 | (validação) | RN-09 (capacidade fora de 1..1000, local ou recurso fora do enum) |

### POST /api/reservas · RF-04
- **Entrada (corpo):** `sala_id: Id`; `responsavel_nome: Texto`; `responsavel_email: Email`; `titulo: Texto`; `participantes: int 1..1000`; `inicio: DataHora`; `fim: DataHora`.
- **Sucesso:** 201 `Reserva` com `status` `ATIVA`.
- **Ordem das verificações:** sala existe → RN-02 → RN-03 → RN-04 → RN-01 (dentro de `banco.transacao`).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SALA_NAO_ENCONTRADA | — |
  | 422 | DURACAO_INVALIDA | RN-02 |
  | 422 | INICIO_NO_PASSADO | RN-03 |
  | 422 | CAPACIDADE_EXCEDIDA | RN-04 |
  | 409 | CONFLITO_HORARIO | RN-01 |
  | 422 | (validação) | participantes < 1, e-mail inválido, horário sem fuso |

### GET /api/reservas · RF-05
- **Entrada (consulta):** `dia: Data` obrigatório; `sala_id: Id` opcional.
- **Sucesso:** 200 lista de `Reserva` (ATIVAS e CANCELADAS) cujo intervalo toca o dia `[dia 00:00, dia+1 00:00)` no fuso padrão (PR-06), ordenada por início e sala (PR-10).
- **Erros:** 422 (validação) para dia fora do formato; 404 SALA_NAO_ENCONTRADA se `sala_id` não existe.

### POST /api/reservas/{id}/cancelar · RF-06
- **Entrada (caminho):** `id: Id`. Sem corpo.
- **Sucesso:** 200 `Reserva` com `status` `CANCELADA`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | RESERVA_NAO_ENCONTRADA | — |
  | 409 | RESERVA_JA_CANCELADA | RN-05, PR-04 |
  | 409 | RESERVA_NAO_FUTURA | RN-05, PR-04 |

409 porque a mesma requisição seria aceita se a reserva guardada estivesse ATIVA e com início futuro (teste das regras transversais).

### GET /api/relatorios/ocupacao · RF-08
- **Entrada (consulta):** `dia: Data` obrigatório.
- **Sucesso:** 200 `{"dia": "2030-01-08", "janela_inicio": "08:00", "janela_fim": "18:00", "minutos_janela": 600, "salas": [{"sala_id": 1, "sala_nome": "Paulista", "local": "SAO_PAULO", "minutos_ocupados": 60.0, "taxa_ocupacao": 10.0}]}`. Todas as salas, ordem local e nome (PR-08, PR-10). `minutos_ocupados` e `taxa_ocupacao` (percentual) com 1 casa decimal, arredondamento meio para cima (PR-07).
- **Erros:** 422 (validação) para dia fora do formato.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `reservas.verificar_conflito(inicio, fim, existentes)` usando `intervalos.sobrepoe` | 409 CONFLITO_HORARIO |
| RN-02 | `reservas.validar_duracao(inicio, fim)` | 422 DURACAO_INVALIDA |
| RN-03 | `reservas.validar_inicio(inicio, agora)` | 422 INICIO_NO_PASSADO |
| RN-04 | `reservas.validar_participantes(participantes, capacidade)` | 422 CAPACIDADE_EXCEDIDA |
| RN-05 | `reservas.validar_cancelamento(status, inicio, agora)` | 409 RESERVA_JA_CANCELADA, 409 RESERVA_NAO_FUTURA |
| RN-06 | repositório filtra `status = 'ATIVA'` em conflito, livres e ocupação; cancelamento só faz `UPDATE status` | — |
| RN-07 | `salas.validar_intervalo_consulta(inicio, fim)` e `salas.filtrar_livres(salas, ocupadas, local, capacidade_minima)` | 422 INTERVALO_INVALIDO |
| RN-08 | `ocupacao.calcular(dia, salas, reservas)` | — |
| RN-09 | Pydantic (faixas e enums) e `salas.normalizar_recursos(recursos)` | 422 RECURSOS_REPETIDOS |
| RN-10 | `salas.verificar_nome_unico(nome, local, existentes)` | 409 SALA_DUPLICADA |

## Tela
Uma página em `/`, título "Reserva de salas".
- **Nova reserva:** formulário (sala em lista vinda de `GET /api/salas`, responsável, e-mail, título, participantes, início e fim em `datetime-local`). O script acrescenta `:00-03:00` (fuso padrão) antes de enviar a `POST /api/reservas`. Sucesso e erro por `mostrarMensagem`; recarrega a agenda.
- **Agenda do dia por sala:** data e sala opcional; chama `GET /api/reservas?dia=&sala_id=`; tabela com sala, horário, título, responsável, participantes, status e botão "Cancelar" nas ATIVAS (`POST /api/reservas/{id}/cancelar`).
- **Salas livres** (pedido: "um jeito rápido de achar sala livre"): início, fim, local e capacidade mínima; chama `GET /api/salas/livres`.
- **Ocupação do dia** (pedido: "saber quanto cada sala é usada"): data; chama `GET /api/relatorios/ocupacao`.
- Dados da API exibidos só por `textContent`/`desenharTabela`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/salas` |
| RF-02 | `GET /api/salas`, `GET /api/salas/{id}`, lista de salas na tela |
| RF-03 | `banco.carga_inicial` |
| RF-04 | `POST /api/reservas`, formulário "Nova reserva" |
| RF-05 | `GET /api/reservas?dia=&sala_id=`, seção "Agenda do dia por sala" |
| RF-06 | `POST /api/reservas/{id}/cancelar`, botão "Cancelar" |
| RF-07 | `GET /api/salas/livres`, seção "Salas livres" |
| RF-08 | `GET /api/relatorios/ocupacao`, seção "Ocupação do dia" |
| RF-09 | todos os endpoints `/api` acima |
| RF-10 | tela em `/` |
| RF-11 | SQLite em `dados/app.db`; nenhum endpoint de login |

## Plano de testes
Relógio padrão `2030-01-07 09:00 -03:00` (segunda). "D+1" = 2030-01-08. Cada teste cria a sala que usa (`POST /api/salas`), salvo os de carga inicial.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_reserva_criada_ativa | CA-01 | padrão | sala cap 8, D+1 10:00–11:00, 4 participantes | 201, status ATIVA |
| test_ca_02_recusa_conflito | CA-02 | padrão | 10:00–11:00 e depois 10:30–11:30 na mesma sala | 409 CONFLITO_HORARIO, mensagem cita conflito |
| test_ca_03_reserva_encostada_criada | CA-03 | padrão | 10:00–11:00 e depois 11:00–12:00 | 201, status ATIVA |
| test_ca_04_recusa_duracao_10_minutos | CA-04 | padrão | 10:00–10:10 | 422 DURACAO_INVALIDA |
| test_ca_04_recusa_duracao_4h01 | CA-04 | padrão | 10:00–14:01 | 422 DURACAO_INVALIDA |
| test_ca_05_recusa_inicio_no_passado | CA-05 | padrão | 2030-01-07 08:00–09:00 | 422 INICIO_NO_PASSADO |
| test_ca_06_recusa_participantes_acima_da_capacidade | CA-06 | padrão | sala cap 4, 5 participantes | 422 CAPACIDADE_EXCEDIDA |
| test_ca_07_cancelar_futura_libera_horario | CA-07 | padrão | cancela D+1 10–11; cria de novo 10–11 | 200 CANCELADA; 201 nova ATIVA; agenda mostra a CANCELADA |
| test_ca_08_recusa_cancelar_reserva_passada | CA-08 | padrão, depois `avancar(hours=3)` | reserva 2030-01-07 10:00–11:00 | 409 RESERVA_NAO_FUTURA, status segue ATIVA |
| test_ca_09_salas_livres_com_filtros | CA-09 | padrão | 3 salas: SP cap 10 ocupada, SP cap 10 livre, SP cap 4 livre, ARA cap 10 livre; filtro SAO_PAULO, cap≥6 | 200, só a SP cap 10 livre |
| test_ca_10_ocupacao_ignora_canceladas | CA-10 | padrão | D+1: ativa 08–10, cancelada 10–12 | 200, minutos 120.0, taxa 20.0 |
| test_rn_01_sobreposicao_contida_recusada | RN-01 | padrão | 10–12 e 10:30–11:00 | 409 CONFLITO_HORARIO |
| test_rn_01_encostar_antes_permitido | RN-01 | padrão | 10–11 e 09:00–10:00 | 201 |
| test_rn_01_outra_sala_sem_conflito | RN-01 | padrão | mesmo horário em outra sala | 201 |
| test_rn_02_duracao_15_minutos_aceita | RN-02 | padrão | 10:00–10:15 | 201 |
| test_rn_02_duracao_14_minutos_recusada | RN-02 | padrão | 10:00–10:14 | 422 DURACAO_INVALIDA |
| test_rn_02_duracao_16_minutos_aceita | RN-02 | padrão | 10:00–10:16 | 201 |
| test_rn_02_duracao_4h_aceita | RN-02 | padrão | 10:00–14:00 | 201 |
| test_rn_02_duracao_3h59_aceita | RN-02 | padrão | 10:00–13:59 | 201 |
| test_rn_02_fracao_de_segundo_descartada | RN-02 | padrão | 10:00:00.700–10:15:00.300 | 201, horários sem fração (15 min exatos) |
| test_rn_02_fim_antes_do_inicio_recusado | RN-02 | padrão | 11:00–10:00 | 422 DURACAO_INVALIDA |
| test_rn_03_inicio_igual_agora_aceito | RN-03 | padrão | 2030-01-07 09:00–10:00 | 201 |
| test_rn_03_inicio_um_minuto_antes_recusado | RN-03 | padrão | 08:59–10:00 | 422 INICIO_NO_PASSADO |
| test_rn_03_inicio_um_minuto_depois_aceito | RN-03 | padrão | 09:01–10:00 | 201 |
| test_rn_04_participantes_igual_capacidade_aceito | RN-04 | padrão | cap 4, 4 | 201 |
| test_rn_04_participantes_abaixo_capacidade_aceito | RN-04 | padrão | cap 4, 3 | 201 |
| test_rn_04_participantes_zero_recusado | RN-04 | padrão | 0 | 422 |
| test_rn_05_cancelar_um_minuto_antes_do_inicio | RN-05 | `avancar` até 09:59 de D | reserva D 10–11 | 200 CANCELADA |
| test_rn_05_cancelar_no_inicio_recusado | RN-05 | `avancar` até 10:00 de D | reserva D 10–11 | 409 RESERVA_NAO_FUTURA |
| test_rn_05_cancelar_em_andamento_recusado | RN-05 | `avancar` até 10:30 de D | reserva D 10–11 | 409 RESERVA_NAO_FUTURA |
| test_rn_05_cancelar_duas_vezes_recusado | RN-05 | padrão | cancela duas vezes | 409 RESERVA_JA_CANCELADA |
| test_rn_05_cancelar_inexistente | RN-05 | padrão | id 999 | 404 RESERVA_NAO_ENCONTRADA |
| test_rn_07_intervalo_invalido | RN-07 | padrão | fim = início | 422 INTERVALO_INVALIDO |
| test_rn_07_encostada_conta_como_livre | RN-07 | padrão | reserva 10–11, consulta 11–12 | sala na lista |
| test_rn_07_cancelada_libera_sala | RN-07, RN-06 | padrão | reserva cancelada 10–11, consulta 10–11 | sala na lista |
| test_rn_07_capacidade_minima_igual_aceita | RN-07 | padrão | cap 6, filtro 6 e 7 | aparece com 6, some com 7 |
| test_rn_08_janela_corta_bordas | RN-08 | padrão | D+1 07:00–09:00 e 17:30–19:00 | minutos 90.0, taxa 15.0 |
| test_rn_08_fora_da_janela_nao_conta | RN-08 | padrão | D+1 07:00–08:00 e 18:00–19:00 | minutos 0.0, taxa 0.0 |
| test_rn_08_dia_inteiro_100 | RN-08 | padrão | D+1 08–12, 12–16, 16–18 | taxa 100.0 |
| test_rn_08_arredondamento_uma_casa | RN-08 | padrão | D+1 10:00–10:20 | taxa 3.3 |
| test_rn_08_lista_todas_as_salas | RN-08, PR-08 | padrão | dia sem reservas | 6 salas, taxa 0.0 |
| test_rn_09_capacidade_bordas | RN-09 | padrão | 0, 1, 1000, 1001 | 422, 201, 201, 422 |
| test_rn_09_enum_invalido | RN-09 | padrão | local `RIO`, recurso `PROJETOR` | 422 |
| test_rn_09_recursos_repetidos | RN-09 | padrão | `["TV", "TV"]` | 422 RECURSOS_REPETIDOS |
| test_rn_10_nome_duplicado_mesmo_local | RN-10 | padrão | "Sala X" e "sala x" em SAO_PAULO | 409 SALA_DUPLICADA |
| test_rn_10_mesmo_nome_outro_local | RN-10 | padrão | "Sala X" em SAO_PAULO e ARARAQUARA | 201 |
| test_rf_02_consultar_sala | RF-02 | padrão | id existente e 999 | 200; 404 SALA_NAO_ENCONTRADA |
| test_rf_03_carga_inicial_seis_salas | RF-03 | padrão | banco novo | 6 salas, 2 por local |
| test_rf_04_sala_inexistente | RF-04 | padrão | sala_id 999 | 404 SALA_NAO_ENCONTRADA |
| test_rf_05_agenda_do_dia_por_sala | RF-05 | padrão | reservas em D+1 e D+2, duas salas | só D+1; filtro de sala |
| test_rf_05_reserva_atravessando_meia_noite | RF-05, PR-05 | padrão | D+1 23:00 – D+2 01:00 | aparece em D+1 e D+2 |
