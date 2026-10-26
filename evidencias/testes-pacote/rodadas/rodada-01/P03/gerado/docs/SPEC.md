# SPEC · Inscrição em treinamentos

Stack padrão da fábrica: Python 3.11, FastAPI + uvicorn, SQLite (`sqlite3`) em `dados/app.db`, pytest, tela única em `/`.

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS turmas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
  inicio TEXT NOT NULL,                       -- UTC, 'YYYY-MM-DDTHH:MM:SS+00:00'
  duracao_minutos INTEGER NOT NULL CHECK (duracao_minutos BETWEEN 1 AND 1440),
  modalidade TEXT NOT NULL CHECK (modalidade IN ('PRESENCIAL', 'ONLINE')),
  vagas INTEGER NOT NULL CHECK (vagas BETWEEN 1 AND 50)
);
```

```sql
CREATE TABLE IF NOT EXISTS inscricoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  turma_id INTEGER NOT NULL REFERENCES turmas(id),
  nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
  email TEXT NOT NULL CHECK (length(email) BETWEEN 3 AND 254),  -- sempre em minúsculas (PR-04)
  situacao TEXT NOT NULL CHECK (situacao IN ('CONFIRMADA', 'ESPERA', 'CANCELADA', 'PRESENTE', 'AUSENTE')),
  criada_em TEXT NOT NULL                     -- UTC; ordem de chegada = (criada_em, id)
);
```

```sql
-- RN-07: no máximo uma inscrição ativa por e-mail e turma (defesa no banco, além da regra de domínio)
CREATE UNIQUE INDEX IF NOT EXISTS ux_inscricao_ativa
  ON inscricoes (turma_id, email) WHERE situacao IN ('CONFIRMADA', 'ESPERA');
```

```sql
CREATE INDEX IF NOT EXISTS ix_inscricoes_turma ON inscricoes (turma_id, situacao);
```

## Carga inicial

Roda ao iniciar a aplicação, só se `turmas` estiver vazia (PR-11). `D` = data de `agora` no fuso America/Sao_Paulo no momento da carga (usa o relógio injetável, o mesmo que a API usa).

| titulo | inicio | duracao_minutos | modalidade | vagas |
|---|---|---|---|---|
| Boas práticas de segurança da informação | D + 7 dias, 09:00 -03:00 | 120 | PRESENCIAL | 20 |
| Introdução à análise de dados | D + 14 dias, 09:00 -03:00 | 180 | ONLINE | 30 |
| Comunicação não violenta | D + 21 dias, 09:00 -03:00 | 90 | PRESENCIAL | 10 |

Sem inscrições na carga inicial.

## Endpoints

Formatos comuns:
- **Turma:** `{"id": 1, "titulo": "Excel avançado", "inicio": "2030-01-10T09:00:00-03:00", "duracao_minutos": 120, "modalidade": "ONLINE", "vagas": 2, "vagas_restantes": 2}`
- **Inscrição:** `{"id": 7, "turma_id": 1, "nome": "Ana Teste", "email": "ana@exemplo.test", "situacao": "ESPERA", "criada_em": "2030-01-07T09:00:00-03:00", "posicao_espera": 1}` (`posicao_espera` só para ESPERA; nas demais, `null`).
- Datas na saída sempre no fuso America/Sao_Paulo com offset. Na entrada, ISO 8601 com offset; sem fuso → 422 do framework.
- Erros de negócio: `{"erro": "<CODIGO>", "mensagem": "<texto>"}`. Erros de formato: 422 padrão do framework.
- Identificadores no caminho (`{id}`): inteiro de 1 a 9223372036854775807; fora disso ou não numérico → 422 do framework. (Acrescentado na revisão.)

### POST /api/turmas · RF-01
- **Entrada:** `titulo` (texto, 1–200 após remover espaços das pontas, obrigatório); `inicio` (data e hora ISO com offset, ano de 2000 a 2999, obrigatório); `duracao_minutos` (inteiro 1–1440, obrigatório); `modalidade` (`PRESENCIAL` | `ONLINE`, obrigatório); `vagas` (inteiro 1–50, obrigatório).
- **Sucesso:** 201, Turma (com `vagas_restantes` = `vagas`).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | padrão do framework | RN-01, RN-02, RN-03, modalidade inválida, horário sem fuso |
  | 422 | INICIO_NO_PASSADO | RN-04 |

### GET /api/turmas · RF-08
- **Entrada:** nenhuma.
- **Sucesso:** 200, lista de Turma com `inicio > agora`, ordenada por `inicio` crescente (PR-09). `vagas_restantes` conforme RN-13.
- **Erros:** nenhum específico.

### GET /api/turmas/{id} · RF-02
- **Entrada:** `id` inteiro no caminho.
- **Sucesso:** 200, Turma (passada ou futura).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | TURMA_NAO_ENCONTRADA | id inexistente |

### POST /api/turmas/{id}/inscricoes · RF-04
- **Entrada:** `nome` (texto 1–200 após remover espaços das pontas, obrigatório); `email` (texto até 254, padrão `^[^@\s]+@[^@\s]+\.[^@\s]+$`, obrigatório; gravado em minúsculas).
- **Sucesso:** 201, Inscrição com `situacao` CONFIRMADA ou ESPERA (RN-05) e `posicao_espera` (RN-06).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | TURMA_NAO_ENCONTRADA | id inexistente |
  | 422 | padrão do framework | RN-03 |
  | 422 | INSCRICOES_ENCERRADAS | RN-08 |
  | 409 | INSCRICAO_DUPLICADA | RN-07 |

Ordem das conferências: turma existe → prazo (RN-08) → duplicidade (RN-07) → situação inicial (RN-05). Tudo dentro de `banco.transacao`.

### GET /api/turmas/{id}/inscricoes · RF-05
- **Entrada:** `id` no caminho.
- **Sucesso:** 200, lista de Inscrição da turma em ordem de chegada (todas as situações).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | TURMA_NAO_ENCONTRADA | id inexistente |

### POST /api/inscricoes/{id}/cancelar · RF-06
- **Entrada:** `id` no caminho; sem corpo.
- **Sucesso:** 200, `{"cancelada": Inscrição, "promovida": Inscrição | null}`. `promovida` é a inscrição que saiu da posição 1 da espera para CONFIRMADA (RN-10).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | INSCRICAO_NAO_ENCONTRADA | id inexistente |
  | 422 | CANCELAMENTO_ENCERRADO | RN-09 (agora ≥ início) |
  | 422 | SITUACAO_NAO_CANCELAVEL | RN-09 (situação não é CONFIRMADA nem ESPERA) |

### POST /api/inscricoes/{id}/presenca · RF-07
- **Entrada:** corpo `{"situacao": "PRESENTE" | "AUSENTE"}` (outro valor → 422 do framework).
- **Sucesso:** 200, Inscrição com a nova situação.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | INSCRICAO_NAO_ENCONTRADA | id inexistente |
  | 422 | PRESENCA_ANTES_DO_INICIO | RN-11 (agora < início) |
  | 422 | PRESENCA_SITUACAO_INVALIDA | RN-11 (situação não é CONFIRMADA) |

### GET /api/turmas/{id}/taxa-presenca · RF-09
- **Entrada:** `id` no caminho.
- **Sucesso:** 200, `{"turma_id": 1, "presentes": 3, "ausentes": 1, "taxa_presenca": 75.0}`. `taxa_presenca` em percentual com 1 casa (meio para cima); `null` quando presentes + ausentes = 0 (PR-10).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | TURMA_NAO_ENCONTRADA | id inexistente |

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | modelo Pydantic `TurmaEntrada.vagas` (`Field(ge=1, le=50)`) | 422 framework |
| RN-02 | modelo Pydantic `TurmaEntrada.duracao_minutos` (`Field(ge=1, le=1440)`) | 422 framework |
| RN-03 | modelos Pydantic `TurmaEntrada.titulo`, `InscricaoEntrada.nome/email` | 422 framework |
| RN-04 | `turmas.validar_inicio_futuro(inicio, agora)` | 422 INICIO_NO_PASSADO |
| RN-05 | `inscricoes.situacao_inicial(vagas, ocupadas)` | — |
| RN-06 | `inscricoes.posicao_na_espera(inscricao_id, ids_espera_em_ordem)` | — |
| RN-07 | `inscricoes.validar_nao_duplicada(existe_ativa)` | 409 INSCRICAO_DUPLICADA |
| RN-08 | `inscricoes.validar_prazo_inscricao(inicio, agora)` | 422 INSCRICOES_ENCERRADAS |
| RN-09 | `inscricoes.validar_cancelamento(situacao, inicio, agora)` | 422 CANCELAMENTO_ENCERRADO / SITUACAO_NAO_CANCELAVEL |
| RN-10 | `inscricoes.promove_espera(situacao_anterior)` | — |
| RN-11 | `inscricoes.validar_presenca(situacao, inicio, agora)` | 422 PRESENCA_ANTES_DO_INICIO / PRESENCA_SITUACAO_INVALIDA |
| RN-12 | `relatorios.taxa_presenca(presentes, ausentes)` | — |
| RN-13 | `turmas.vagas_restantes(vagas, ocupadas)` | — |

## Tela
- Página única em `/`.
- **Turmas futuras:** tabela com título, início (data e hora local), duração, modalidade, vagas e vagas restantes (`GET /api/turmas`). Cada linha tem o botão "Ver inscritos".
- **Inscrever-se:** formulário com seleção da turma (turmas futuras), nome e e-mail → `POST /api/turmas/{id}/inscricoes`. Mostra "Inscrição CONFIRMADA" ou "Inscrição em ESPERA, posição N" e recarrega a tabela. Erro da API aparece com a `mensagem`.
- **Inscritos da turma:** ao clicar "Ver inscritos", tabela com nome, e-mail, situação e posição na espera (`GET /api/turmas/{id}/inscricoes`).
- Dados da API exibidos só com `textContent`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/turmas` |
| RF-02 | `GET /api/turmas/{id}` |
| RF-03 | `banco.carga_inicial` |
| RF-04 | `POST /api/turmas/{id}/inscricoes`, tela (formulário) |
| RF-05 | `GET /api/turmas/{id}/inscricoes`, tela (inscritos) |
| RF-06 | `POST /api/inscricoes/{id}/cancelar` |
| RF-07 | `POST /api/inscricoes/{id}/presenca` |
| RF-08 | `GET /api/turmas`, tela (tabela de turmas) |
| RF-09 | `GET /api/turmas/{id}/taxa-presenca` |
| RF-10 | todos os endpoints `/api` |
| RF-11 | `GET /` (tela) |
| RF-12 | SQLite em `dados/app.db`; nenhum endpoint exige autenticação |

## Plano de testes

Relógio de teste inicial: `T0` = 2030-01-07 09:00 -03:00. Turma padrão dos testes: início 2030-01-10 09:00 -03:00 (3 dias depois), 60 min, ONLINE.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_inscricao_com_vaga_confirmada | CA-01 | T0 | turma 2 vagas; 1 inscrição | 201, situacao CONFIRMADA, posicao_espera null |
| test_ca_02_turma_lotada_entra_em_espera_primeira | CA-02 | T0 | turma 1 vaga; 2 inscrições | 2ª: 201, ESPERA, posicao_espera 1 |
| test_ca_03_cancelar_confirmada_promove_primeira_espera | CA-03 | T0 | turma 1 vaga; A confirmada, B e C em espera; cancelar A | 200, cancelada CANCELADA, promovida = B CONFIRMADA; C posição 1 |
| test_ca_04_mesmo_email_duas_vezes_recusado | CA-04 | T0 | mesmo e-mail 2× | 2ª: 409 INSCRICAO_DUPLICADA |
| test_ca_05_inscrever_23h_antes_recusado | CA-05 | T0 | turma com início T0 + 23 h | 422 INSCRICOES_ENCERRADAS |
| test_ca_06_cancelar_apos_inicio_recusado | CA-06 | T0 → início + 1 min | inscrição confirmada; cancelar | 422 CANCELAMENTO_ENCERRADO, situação segue CONFIRMADA |
| test_ca_07_presenca_antes_do_inicio_recusada | CA-07 | T0 | inscrição confirmada; PRESENTE | 422 PRESENCA_ANTES_DO_INICIO |
| test_ca_08_presenca_de_espera_recusada | CA-08 | T0 → início | inscrição em ESPERA; PRESENTE | 422 PRESENCA_SITUACAO_INVALIDA |
| test_ca_09_turma_lotada_aparece_com_zero_vagas | CA-09 | T0 | turma 2 vagas, 2 inscrições; GET /api/turmas | turma na lista com vagas_restantes 0 |
| test_ca_10_taxa_presenca_75 | CA-10 | T0 → início | 4 confirmadas; 3 PRESENTE, 1 AUSENTE | 200, taxa_presenca 75.0 |
| test_rn_01_vagas_limites | RN-01 | T0 | vagas 0, 1, 50, 51 | 422, 201, 201, 422 |
| test_rn_02_duracao_limites | RN-02 | T0 | duração 0, 1, 1440, 1441 | 422, 201, 201, 422 |
| test_rn_03_textos_e_email | RN-03 | T0 | título "", 200 e 201 chars; e-mail inválido; nome vazio | 422, 201, 422, 422, 422 |
| test_rn_04_inicio_no_passado | RN-04 | T0 | início = T0; T0 + 1 min | 422 INICIO_NO_PASSADO; 201 |
| test_rn_04_inicio_sem_fuso_recusado | RN-04 | T0 | início sem offset | 422 |
| test_rn_05_limite_de_ocupacao | RN-05 | T0 | turma 2 vagas; 3 inscrições | CONFIRMADA, CONFIRMADA, ESPERA |
| test_rn_06_fila_por_ordem_de_chegada | RN-06 | T0 | turma 1 vaga; 3 inscrições | posições 1 e 2 na listagem |
| test_rn_07_email_sem_diferenciar_maiusculas | RN-07 | T0 | `Ana@X.test` e `ana@x.test` | 409 INSCRICAO_DUPLICADA |
| test_rn_07_reinscricao_apos_cancelar | RN-07 | T0 | inscrever, cancelar, inscrever | 201 |
| test_rn_08_prazo_limites | RN-08 | T0 | início T0 + 24 h + 1 min; + 24 h; + 23 h 59 min | 201; 422; 422 |
| test_rn_09_cancelar_limites | RN-09 | início − 1 min; início | cancelar | 200; 422 CANCELAMENTO_ENCERRADO |
| test_rn_09_cancelar_ja_cancelada | RN-09 | T0 | cancelar 2× | 2ª: 422 SITUACAO_NAO_CANCELAVEL |
| test_rn_10_cancelar_espera_nao_promove | RN-10 | T0 | cancelar inscrição em ESPERA | promovida null |
| test_rn_10_cancelar_sem_fila_libera_vaga | RN-10 | T0 | cancelar única confirmada | promovida null, vagas_restantes volta a 1 |
| test_rn_11_presenca_limites | RN-11 | início − 1 min; início | PRESENTE | 422; 200 PRESENTE |
| test_rn_11_presenca_ja_marcada | RN-11 | início | AUSENTE depois de PRESENTE | 422 PRESENCA_SITUACAO_INVALIDA |
| test_rn_11_valor_invalido | RN-11 | início | situacao "CANCELADA" | 422 |
| test_rn_12_taxa_sem_marcacao_e_arredondamento | RN-12 | início | 0 marcações; 2 presentes 1 ausente | null; 66.7 |
| test_rn_13_vagas_restantes_e_turmas_futuras | RN-13 | T0 → após início | turma passada sai da lista | lista sem a turma |
| test_carga_inicial_tres_turmas_futuras | RF-03 | T0 | GET /api/turmas | 3 turmas futuras |
| test_entradas_invalidas_retornam_4xx | revisão | T0 | campo faltando, tipo errado, id enorme/0/não numérico, ano fora de 2000–2999 | 422 |
| test_rn_03_texto_so_com_espacos_recusado | RN-03 | T0 | título e nome só com espaços | 422 |
| test_erros_404 | RF-02, RF-05, RF-06, RF-07, RF-09 | T0 | ids inexistentes | 404 com código |
