# SPEC · Reserva de salas

Stack: a da `stack-padrao` (Python 3.11, FastAPI, SQLite `gerado/dados/app.db`, pytest). Fuso `America/Sao_Paulo` (PR-01). Datas e horas na API em ISO 8601 com offset; horário sem fuso é recusado com `422`. No banco, texto UTC no formato de `relogio.para_banco`.

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS salas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(nome) BETWEEN 1 AND 200),
  local TEXT NOT NULL CHECK (local IN ('SAO_PAULO', 'ARARAQUARA', 'COWORKING')),
  capacidade INTEGER NOT NULL CHECK (capacidade BETWEEN 1 AND 500),
  recursos TEXT NOT NULL DEFAULT '[]'
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
  status TEXT NOT NULL DEFAULT 'ATIVA' CHECK (status IN ('ATIVA', 'CANCELADA')),
  criada_em TEXT NOT NULL,
  cancelada_em TEXT,
  CHECK (fim > inicio)
);

CREATE INDEX IF NOT EXISTS idx_reservas_sala_inicio ON reservas (sala_id, inicio);
```

`recursos` é uma lista JSON em texto (ex.: `["TV","QUADRO"]`): as consultas do PRD não filtram por recurso, então não há tabela de ligação.

## Carga inicial
Roda em `banco.carga_inicial` só quando `salas` está vazia (RF-03). Nomes fictícios.

| nome | local | capacidade | recursos |
|---|---|---|---|
| Sala Paulista | SAO_PAULO | 8 | TV, VIDEOCONFERENCIA |
| Sala Ibirapuera | SAO_PAULO | 4 | QUADRO |
| Sala Laranjeira | ARARAQUARA | 10 | TV, QUADRO |
| Sala Morada do Sol | ARARAQUARA | 6 | VIDEOCONFERENCIA |
| Coworking Aquario | COWORKING | 12 | TV, VIDEOCONFERENCIA, QUADRO |
| Coworking Cabine | COWORKING | 2 | (nenhum) |

## Endpoints

Erros de validação de formato: `422` padrão do FastAPI (`{"detail": [...]}`). Limites comuns: identificadores (`sala_id`, `reserva_id`) inteiros de 1 a 2^63-1; datas e data-horas com ano entre 2000 e 2100 (PR-10); fora disso, `422`. Erros de regra: `{"erro": "<CODIGO>", "mensagem": "<texto>"}`.

Representação de sala: `{"id": 1, "nome": "Sala Paulista", "local": "SAO_PAULO", "capacidade": 8, "recursos": ["TV", "VIDEOCONFERENCIA"]}`.

Representação de reserva: `{"id": 1, "sala_id": 1, "responsavel_nome": "Ana Teste", "responsavel_email": "ana@exemplo.com", "titulo": "Planejamento", "participantes": 4, "inicio": "2030-01-08T10:00:00-03:00", "fim": "2030-01-08T11:00:00-03:00", "status": "ATIVA", "criada_em": "2030-01-07T09:00:00-03:00", "cancelada_em": null}`. Datas de saída sempre no fuso PR-01.

### GET /api/salas · RF-02
- **Entrada:** nenhuma.
- **Sucesso:** 200 `[<sala>, ...]`, ordenado por local e nome (PR-06).
- **Erros:** nenhum.

### GET /api/salas/{sala_id} · RF-02
- **Entrada:** `sala_id` inteiro no caminho.
- **Sucesso:** 200 `<sala>`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SALA_NAO_ENCONTRADA | RF-02 |
  | 422 | (validação) | `sala_id` não inteiro |

### POST /api/salas · RF-01
- **Entrada (JSON):** `nome` texto 1..200 (obrigatório, espaços nas pontas removidos); `local` enum `SAO_PAULO|ARARAQUARA|COWORKING` (obrigatório); `capacidade` inteiro 1..500 (obrigatório); `recursos` lista de enum `TV|VIDEOCONFERENCIA|QUADRO`, sem repetição, opcional (padrão `[]`).
- **Sucesso:** 201 `<sala>`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 409 | SALA_NOME_DUPLICADO | RN-10 |
  | 422 | (validação) | RN-10 (faixa, enum, repetição, vazio) |

### GET /api/salas/livres · RF-06
- **Entrada (consulta):** `inicio` e `fim` data-hora com offset (obrigatórios); `local` enum (opcional); `capacidade_minima` inteiro 1..500 (opcional).
- **Sucesso:** 200 `[<sala>, ...]` só com salas sem reserva ATIVA sobreposta e que atendem aos filtros, ordem PR-06.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | INTERVALO_INVALIDO | RN-09 |
  | 422 | (validação) | sem fuso, enum ou faixa inválidos |

### POST /api/reservas · RF-04
- **Entrada (JSON):** `sala_id` inteiro >= 1; `responsavel_nome` texto 1..200; `responsavel_email` texto 3..254 no formato `^[^@\s]+@[^@\s]+\.[^@\s]+$`; `titulo` texto 1..200; `participantes` inteiro 1..1000; `inicio` e `fim` data-hora com offset. Todos obrigatórios.
- **Sucesso:** 201 `<reserva>` com `status` `ATIVA`.
- **Erros (na ordem em que são conferidos):**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | (validação) | RN-11, formato, sem fuso, participantes < 1 |
  | 422 | INTERVALO_INVALIDO | RN-09 |
  | 422 | DURACAO_INVALIDA | RN-02 |
  | 422 | INICIO_NO_PASSADO | RN-03 |
  | 404 | SALA_NAO_ENCONTRADA | RF-04 |
  | 422 | CAPACIDADE_EXCEDIDA | RN-04 |
  | 409 | CONFLITO_HORARIO | RN-01 |

### GET /api/reservas · RF-08
- **Entrada (consulta):** `data` `AAAA-MM-DD` (obrigatório, dia civil PR-04); `sala_id` inteiro (opcional).
- **Sucesso:** 200 `[<reserva>, ...]` com reservas ATIVAS e CANCELADAS que tocam o dia (`inicio < fim_do_dia` e `fim > inicio_do_dia`), ordenadas por início e id.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | (validação) | data ausente ou inválida |

### GET /api/reservas/{reserva_id} · RF-04, RF-09
- **Entrada:** `reserva_id` inteiro.
- **Sucesso:** 200 `<reserva>`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | RESERVA_NAO_ENCONTRADA | RF-05 |

### POST /api/reservas/{reserva_id}/cancelar · RF-05
- **Entrada:** `reserva_id` inteiro; sem corpo.
- **Sucesso:** 200 `<reserva>` com `status` `CANCELADA` e `cancelada_em` preenchido.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | RESERVA_NAO_ENCONTRADA | RF-05 |
  | 409 | RESERVA_JA_CANCELADA | RN-05 |
  | 422 | CANCELAMENTO_NAO_PERMITIDO | RN-05 (início <= agora) |

### GET /api/relatorios/ocupacao · RF-07
- **Entrada (consulta):** `data` `AAAA-MM-DD` (obrigatório).
- **Sucesso:** 200 `{"data": "2030-01-08", "janela_inicio": "08:00", "janela_fim": "18:00", "minutos_janela": 600, "salas": [{"sala_id": 1, "nome": "Sala Paulista", "local": "SAO_PAULO", "minutos_ocupados": 60, "taxa_ocupacao": 10.0}, ...]}`. Todas as salas aparecem, ordem PR-06. `taxa_ocupacao` em percentual, 1 casa decimal (PR-05).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | (validação) | data ausente ou inválida |

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `reservas.verificar_conflito(existentes, inicio, fim)` (usa `reservas.sobrepoe`) | 409 CONFLITO_HORARIO |
| RN-02 | `reservas.validar_duracao(inicio, fim)` | 422 DURACAO_INVALIDA |
| RN-03 | `reservas.validar_inicio_futuro(inicio, agora)` | 422 INICIO_NO_PASSADO |
| RN-04 | `reservas.validar_participantes(participantes, capacidade)` | 422 CAPACIDADE_EXCEDIDA (abaixo de 1: 422 validação) |
| RN-05 | `reservas.validar_cancelamento(status, inicio, agora)` | 409 RESERVA_JA_CANCELADA; 422 CANCELAMENTO_NAO_PERMITIDO |
| RN-06 | `reservas.bloqueia_horario(status)`, usada por RN-01, RN-07 e RN-08 | (sem erro) |
| RN-07 | `salas.filtrar_livres(salas, ocupadas, local, capacidade_minima)` | (sem erro) |
| RN-08 | `ocupacao.calcular(salas, reservas, dia)` | (sem erro) |
| RN-09 | `reservas.validar_intervalo(inicio, fim)` | 422 INTERVALO_INVALIDO |
| RN-10 | modelo Pydantic `SalaEntrada` + `salas.validar_nome_unico(ja_existe, nome)` | 422 validação; 409 SALA_NOME_DUPLICADO |
| RN-11 | modelo Pydantic `ReservaEntrada` (padrão de e-mail, `min_length=1`) | 422 validação |

`app/dominio/` não importa FastAPI nem `sqlite3`; recebe `agora` como parâmetro.

## Tela
Página única em `/` (`app/estatico/index.html`):
- **Agenda do dia:** campo de data (padrão hoje) e, para cada sala (`GET /api/salas`), a lista das reservas do dia (`GET /api/reservas?data=`) com horário, título, responsável, participantes e status; reservas ATIVAS têm botão "Cancelar" (`POST /api/reservas/{id}/cancelar`).
- **Nova reserva:** formulário com sala (lista), responsável, e-mail, título, participantes, data, hora de início e hora de fim; envia `POST /api/reservas` com offset `-03:00` (PR-01) e recarrega a agenda.
- **Salas livres:** data, hora de início e fim, local e capacidade mínima opcionais; chama `GET /api/salas/livres`.
- **Ocupação do dia:** tabela de `GET /api/relatorios/ocupacao?data=` para a data da agenda.
- Mensagens de erro da API (`mensagem` ou `detail`) aparecem numa área de aviso. Dados da API só com `textContent`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/salas` |
| RF-02 | `GET /api/salas`, `GET /api/salas/{sala_id}` |
| RF-03 | carga inicial em `banco.carga_inicial` |
| RF-04 | `POST /api/reservas`, `GET /api/reservas/{reserva_id}` |
| RF-05 | `POST /api/reservas/{reserva_id}/cancelar` |
| RF-06 | `GET /api/salas/livres` |
| RF-07 | `GET /api/relatorios/ocupacao` |
| RF-08 | `GET /api/reservas?data=` |
| RF-09 | todos os endpoints acima em `/api` |
| RF-10 | tela em `/` |
| RF-11 | SQLite local em `dados/app.db`; nenhum endpoint exige autenticação |
| RN-01..RN-11 | tabela "Regras de negócio" |

## Plano de testes
Relógio padrão dos testes: `2030-01-07 09:00 -03:00` (segunda). "D+1" = 2030-01-08. Sala 1 = Sala Paulista (cap. 8), sala 2 = Sala Ibirapuera (cap. 4).

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_reserva_criada_ativa | CA-01, RF-04 | padrão | sala 1, D+1 10:00–11:00, 4 participantes | 201, `status` ATIVA, campos ecoados |
| test_ca_02_recusa_conflito | CA-02, RN-01 | padrão | sala 1 D+1 10:00–11:00, depois 10:30–11:30 | 409, `erro` CONFLITO_HORARIO, mensagem cita conflito |
| test_ca_03_encostar_permitido | CA-03, RN-01 | padrão | sala 1 D+1 10:00–11:00, depois 11:00–12:00 | 201, `status` ATIVA |
| test_ca_04_recusa_duracao | CA-04, RN-02 | padrão | D+1 10:00–10:10 e 10:00–14:01 | 422, `erro` DURACAO_INVALIDA nos dois |
| test_ca_05_recusa_inicio_passado | CA-05, RN-03 | padrão | 2030-01-07 08:00–09:30 | 422, `erro` INICIO_NO_PASSADO |
| test_ca_06_recusa_participantes_acima_capacidade | CA-06, RN-04 | padrão | sala 2 (cap. 4), 5 participantes | 422, `erro` CAPACIDADE_EXCEDIDA |
| test_ca_07_cancelar_reserva_futura | CA-07, RF-05, RN-06 | padrão | criar D+1 10:00–11:00, cancelar, criar de novo 10:00–11:00 | 200 `status` CANCELADA; nova reserva 201; GET da cancelada mantém CANCELADA |
| test_ca_08_recusa_cancelar_reserva_passada | CA-08, RN-05 | padrão, depois `avancar(days=2)` | reserva D+1 10:00–11:00 | 422, `erro` CANCELAMENTO_NAO_PERMITIDO; status segue ATIVA |
| test_ca_09_salas_livres_com_filtros | CA-09, RF-06, RN-07 | padrão | sala 1 ocupada D+1 10–11; livres SAO_PAULO cap>=4 10–11; cap>=5 10–11; cap>=5 11–12; sem filtro | só [Ibirapuera]; []; [Paulista]; 6 salas menos a ocupada |
| test_ca_10_ocupacao_ignora_canceladas | CA-10, RF-07, RN-06, RN-08 | padrão | sala 1 D+1 10–11 ativa e 14–16 cancelada | sala 1: 60 min, 10.0; demais 0 |
| test_rn_01_sobreposicao_bordas | RN-01 | padrão | base 10:00–11:00; 09:00–10:01, 10:59–12:00, 10:15–10:45, 09:00–12:00 | 409 em todos; 09:00–10:00 e 11:00–12:00 201; outra sala 10–11 201 |
| test_rn_02_duracao_bordas | RN-02 | padrão | 14, 15, 16, 239, 240, 241 min | 422, 201, 201, 201, 201, 422 |
| test_rn_03_inicio_bordas | RN-03 | padrão | início 08:59, 09:00, 09:01 do dia do relógio | 422 INICIO_NO_PASSADO, 201, 201 |
| test_rn_04_participantes_bordas | RN-04 | padrão | sala 2 (cap. 4): 3, 4, 5, 0 | 201, 201, 422 CAPACIDADE_EXCEDIDA, 422 validação |
| test_rn_05_cancelamento_bordas | RN-05 | padrão e avançado | início em 09:01 cancelado às 09:00; início 09:01 com relógio 09:01; em andamento; já cancelada | 200; 422; 422; 409 RESERVA_JA_CANCELADA |
| test_rn_05_cancelar_inexistente | RF-05 | padrão | id 999 | 404 RESERVA_NAO_ENCONTRADA |
| test_rn_08_ocupacao_janela_bordas | RN-08, PR-04, PR-05 | padrão | sala 1: 07:00–09:00, 17:30–19:00; sala 2: 18:00–19:00; sala 3: 08:00–08:20 | 90 min 15.0; 0 min 0.0; 20 min 3.3 |
| test_rn_09_intervalo_invalido | RN-09 | padrão | fim = início; fim antes do início; idem em salas livres | 422 INTERVALO_INVALIDO |
| test_rn_10_sala_cadastro_bordas | RN-10, RF-01 | padrão | capacidade 0, 1, 500, 501; nome repetido com outra caixa; recursos repetidos; local inválido; nome vazio | 422, 201, 201, 422; 409 SALA_NOME_DUPLICADO; 422; 422; 422 |
| test_rn_11_validacao_reserva | RN-11 | padrão | e-mail sem @, título vazio, data sem fuso, sala inexistente | 422, 422, 422, 404 SALA_NAO_ENCONTRADA |
| test_rf_02_consultar_sala | RF-02 | padrão | GET sala 1; GET sala 999 | 200 nome Sala Paulista; 404 SALA_NAO_ENCONTRADA |
| test_rf_03_carga_inicial | RF-03 | padrão | GET /api/salas; reiniciar app no mesmo banco | 6 salas, 2 por local; continua 6 |
| test_rf_08_agenda_do_dia | RF-08, RF-05 | padrão | reservas em D+1 (uma cancelada) e D+2; filtro por sala | só D+1, cancelada com status CANCELADA, ordenado por início |
| test_robustez_parametros_fora_da_faixa | limites comuns, PR-10 | padrão | ids acima de 2^63-1, `sala_id` não numérico, datas no ano 1 e 9999 | 422 |
| test_robustez_corpo_invalido | limites comuns, PR-10 | padrão | `sala_id` enorme ou texto, datas no ano 9999, participantes texto | 422 |
| test_robustez_campo_faltando | RF-04 | padrão | corpo sem `titulo` | 422 com `loc` do campo |
