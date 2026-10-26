# SPEC · Reserva de salas

## Modelo de dados
Datas com hora são `TEXT` UTC; recursos são JSON em `TEXT`.

```sql
CREATE TABLE IF NOT EXISTS salas (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 nome TEXT NOT NULL CHECK(length(trim(nome)) BETWEEN 1 AND 200),
 local TEXT NOT NULL CHECK(local IN ('SAO_PAULO','ARARAQUARA','COWORKING')),
 capacidade INTEGER NOT NULL CHECK(capacidade BETWEEN 1 AND 2147483647),
 recursos TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservas (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 sala_id INTEGER NOT NULL REFERENCES salas(id),
 responsavel_nome TEXT NOT NULL,
 responsavel_email TEXT NOT NULL,
 titulo TEXT NOT NULL,
 participantes INTEGER NOT NULL CHECK(participantes > 0),
 inicio TEXT NOT NULL,
 fim TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('ATIVA','CANCELADA'))
);
CREATE INDEX IF NOT EXISTS idx_reservas_sala_intervalo ON reservas(sala_id,status,inicio,fim);
```

## Carga inicial
| Nome | Local | Capacidade | Recursos |
|---|---|---:|---|
| Paulista | SAO_PAULO | 8 | TV, VIDEOCONFERENCIA |
| Ibirapuera | SAO_PAULO | 4 | QUADRO |
| Centro | ARARAQUARA | 6 | TV, QUADRO |
| Jardim | ARARAQUARA | 10 | VIDEOCONFERENCIA |
| Hub A | COWORKING | 3 | TV |
| Hub B | COWORKING | 12 | TV, VIDEOCONFERENCIA, QUADRO |

## Endpoints

### POST /api/salas · RF-01
- **Entrada:** JSON `nome: Texto`, `local: enum`, `capacidade: Id`, `recursos: lista de enum` (obrigatórios, lista sem duplicatas).
- **Sucesso:** 201 `{"id":7,"nome":"Nova","local":"SAO_PAULO","capacidade":5,"recursos":["TV"]}`.
- **Erros:** 422 validação de campos (RN-07, PR-03).

### GET /api/salas · RF-01, RF-02
- **Entrada:** nenhuma.
- **Sucesso:** 200, lista de objetos de sala como acima, ordenada por local, nome, id.
- **Erros:** nenhum de negócio.

### POST /api/reservas · RF-03
- **Entrada:** JSON `sala_id: Id`, `responsavel_nome: Texto`, `responsavel_email: Email`, `titulo: Texto`, `participantes: Id`, `inicio: DataHora`, `fim: DataHora` obrigatórios.
- **Sucesso:** 201 `{"id":1,"sala_id":1,"responsavel_nome":"Ana","responsavel_email":"ana@example.test","titulo":"Reunião","participantes":2,"inicio":"2030-01-07T10:00:00-03:00","fim":"2030-01-07T11:00:00-03:00","status":"ATIVA"}`.
- **Erros:** 404 SALA_NAO_ENCONTRADA; 409 CONFLITO_HORARIO (RN-01); 422 DURACAO_INVALIDA (RN-02), INICIO_PASSADO (RN-03), CAPACIDADE_EXCEDIDA (RN-04), validação de campos.

### GET /api/reservas · RF-03, RF-08
- **Entrada:** consulta opcional `sala_id: Id`, `dia: Data`.
- **Sucesso:** 200, lista de objetos de reserva como acima, ordenada por início, id; `dia` é a data civil no fuso padrão e inclui reservas que cruzam o dia.
- **Erros:** 422 validação de consulta.

### GET /api/reservas/{id} · RF-03
- **Entrada:** caminho `id: Id`.
- **Sucesso:** 200, objeto de reserva como acima.
- **Erros:** 404 RESERVA_NAO_ENCONTRADA; 422 id inválido.

### POST /api/reservas/{id}/cancelar · RF-04
- **Entrada:** caminho `id: Id`, corpo vazio.
- **Sucesso:** 200, objeto de reserva com `status: "CANCELADA"`.
- **Erros:** 404 RESERVA_NAO_ENCONTRADA; 409 RESERVA_JA_CANCELADA; 422 CANCELAMENTO_FORA_DO_PRAZO (RN-05), id inválido.

### GET /api/salas/livres · RF-05
- **Entrada:** consulta obrigatória `inicio: DataHora`, `fim: DataHora`; opcionais `local: enum`, `capacidade_minima: Id`.
- **Sucesso:** 200, lista de objetos de sala, apenas sem reserva ATIVA sobreposta, ordenada por local, nome, id.
- **Erros:** 422 INTERVALO_INVALIDO (PR-06), validação de campos.

### GET /api/relatorios/ocupacao · RF-06
- **Entrada:** consulta obrigatória `dia: Data`.
- **Sucesso:** 200 `[{"sala_id":1,"sala_nome":"Paulista","dia":"2030-01-07","minutos_ocupados":60,"percentual":10.0}]`, todas as salas por local, nome, id.
- **Erros:** 422 validação de data.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `reservas.verificar_conflito` | 409 CONFLITO_HORARIO |
| RN-02 | `reservas.validar_duracao` | 422 DURACAO_INVALIDA |
| RN-03 | `reservas.validar_inicio` | 422 INICIO_PASSADO |
| RN-04 | `reservas.validar_participantes` | 422 CAPACIDADE_EXCEDIDA |
| RN-05 | `reservas.validar_cancelamento` | 409 RESERVA_JA_CANCELADA / 422 CANCELAMENTO_FORA_DO_PRAZO |
| RN-06 | `relatorios.ocupacao` | sem erro de negócio |
| RN-07 | `salas.validar_sala` | 422 validação de entrada |

## Tela
- Formulário para criar reserva: lista de salas, responsável, e-mail, título, participantes, início e fim; chama `GET /api/salas` e `POST /api/reservas`.
- Agenda do dia por sala, com seletor de data, sala e botão de cancelamento para reserva futura; chama `GET /api/reservas` e `POST /api/reservas/{id}/cancelar`.
- Exibe mensagens de sucesso e de erro da API.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | POST/GET `/api/salas` |
| RF-02 | carga inicial |
| RF-03 | POST/GET `/api/reservas`, GET `/api/reservas/{id}` |
| RF-04 | POST `/api/reservas/{id}/cancelar` |
| RF-05 | GET `/api/salas/livres` |
| RF-06 | GET `/api/relatorios/ocupacao` |
| RF-07 | todos endpoints `/api` |
| RF-08 | tela `/` |
| RF-09 | tabelas SQLite |

## Plano de testes
Relógio de teste: 2030-01-07 09:00-03:00, salvo indicação. Dados de reserva padrão: sala 1, 2 participantes, 10h–11h.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_cria_reserva | CA-01 | padrão | reserva padrão | 201, ATIVA |
| test_ca_02_recusa_conflito | CA-02 | padrão | 10h–11h e 10h30–11h30 | 409, CONFLITO_HORARIO |
| test_ca_03_permite_encostar | CA-03 | padrão | 10h–11h e 11h–12h | 201, ATIVA |
| test_ca_04_recusa_duracao | CA-04 | padrão | 10min e 241min | 422, DURACAO_INVALIDA |
| test_ca_05_recusa_passado | CA-05 | padrão | início 08h59 | 422, INICIO_PASSADO |
| test_ca_06_recusa_capacidade | CA-06 | padrão | 9 participantes sala 1 | 422, CAPACIDADE_EXCEDIDA |
| test_ca_07_cancela_e_libera | CA-07 | padrão | cancelar e recriar | 200 CANCELADA, 201 ATIVA |
| test_ca_08_recusa_cancelar_passado | CA-08 | avançado 3h | cancelar reserva 10h | 422 CANCELAMENTO_FORA_DO_PRAZO |
| test_ca_09_filtra_livres | CA-09 | padrão | local SAO_PAULO, capacidade 5, sala 1 ocupada | 200, lista vazia; após cancelamento, sala 1 |
| test_ca_10_ignora_canceladas | CA-10 | padrão | reserva 60min cancelada e 30min ativa | 200, 5% |
| test_rn_02_bordas_duracao | RN-02 | padrão | 14,15,240,241min | 422,201,201,422 |
| test_rn_03_borda_inicio | RN-03 | padrão | 08h59,09h,09h01 | 422,201,201 |
| test_rn_04_borda_capacidade | RN-04 | padrão | 0,8,9 participantes | 422,201,422 |
| test_rn_05_borda_cancelamento | RN-05 | 09h/10h | antes/no início/após início | 200/422/422 |
| test_rn_06_bordas_ocupacao | RN-06 | padrão | 07h–08h,08h–12h,18h–19h | 0%,40%,0% |
| test_rn_07_borda_capacidade_sala | RN-07 | padrão | capacidade 0,1,2 | 422,201,201 |
