# SPEC · Inscrição em treinamentos

Stack padrão da fábrica (FastAPI + SQLite + página única). Datas e horas na API em ISO 8601 com offset; sem offset → 422. No banco, texto UTC (`relogio.para_banco`). Fuso `America/Sao_Paulo` (PR-01).

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS turmas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
  inicio TEXT NOT NULL,
  duracao_minutos INTEGER NOT NULL CHECK (duracao_minutos BETWEEN 1 AND 1440),
  modalidade TEXT NOT NULL CHECK (modalidade IN ('PRESENCIAL', 'ONLINE')),
  vagas INTEGER NOT NULL CHECK (vagas BETWEEN 1 AND 50)
);

CREATE TABLE IF NOT EXISTS inscricoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  turma_id INTEGER NOT NULL REFERENCES turmas(id),
  nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
  email TEXT NOT NULL CHECK (length(email) BETWEEN 3 AND 254),
  situacao TEXT NOT NULL CHECK (situacao IN ('CONFIRMADA', 'ESPERA', 'CANCELADA', 'PRESENTE', 'AUSENTE')),
  criada_em TEXT NOT NULL,
  atualizada_em TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_inscricoes_turma ON inscricoes (turma_id, id);

-- RN-05: no máximo uma inscrição ativa por e-mail e turma (defesa no banco, além do domínio).
CREATE UNIQUE INDEX IF NOT EXISTS ux_inscricao_ativa ON inscricoes (turma_id, email)
  WHERE situacao IN ('CONFIRMADA', 'ESPERA');
```

- Ordem de chegada (RN-04, PR-10) = `id` crescente da inscrição (autoincremento é monotônico; `criada_em` pode empatar com relógio fixo).
- E-mail guardado em minúsculas (PR-05).

## Carga inicial
Só quando `turmas` está vazia. `D(n, h)` = data de `agora + n dias` no fuso padrão, às `h`:00 (sempre futura, RF-03).

| titulo | inicio | duracao_minutos | modalidade | vagas |
|---|---|---|---|---|
| Integração de novos colaboradores | D(7, 9) | 120 | PRESENCIAL | 20 |
| Segurança da informação no dia a dia | D(14, 14) | 90 | ONLINE | 50 |
| Planilhas: fórmulas e tabelas dinâmicas | D(21, 10) | 240 | PRESENCIAL | 12 |

Nenhuma inscrição inicial.

## Formatos de saída

- **Turma:** `{"id": 1, "titulo": "...", "inicio": "2030-01-10T09:00:00-03:00", "duracao_minutos": 60, "modalidade": "ONLINE", "vagas": 2, "vagas_restantes": 2}`. `vagas_restantes` = `max(0, vagas − ocupadas)`, ocupadas = CONFIRMADA + PRESENTE + AUSENTE (RN-13).
- **Inscrição:** `{"id": 1, "turma_id": 1, "nome": "...", "email": "...", "situacao": "ESPERA", "criada_em": "...-03:00", "posicao_espera": 1}`. `posicao_espera` = posição na fila (1 = primeira) quando `ESPERA`; `null` nas demais situações (RN-04).

## Endpoints

### POST /api/turmas · RF-01
- **Entrada (JSON):** `titulo` Texto (1–200, obrigatório); `inicio` DataHora (obrigatório, com offset); `duracao_minutos` inteiro (obrigatório; faixa de formato −1.000.000 a 1.000.000, regra 1–1440 no domínio); `modalidade` `PRESENCIAL`|`ONLINE` (obrigatório); `vagas` inteiro (obrigatório; faixa de formato −1.000.000 a 1.000.000, regra 1–50 no domínio).
- **Sucesso:** 201 Turma.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | VAGAS_INVALIDAS | RN-01 |
  | 422 | DURACAO_INVALIDA | RN-02 |
  | 422 | INICIO_NO_PASSADO | PR-04 |
  | 422 | (padrão do framework) | formato |

### GET /api/turmas · RF-09
- **Entrada:** nenhuma.
- **Sucesso:** 200 lista de Turma com `inicio > agora` (RN-14), ordenada por `inicio`, depois `id` (PR-10).
- **Erros:** nenhum de negócio.

### GET /api/turmas/{id} · RF-02
- **Entrada:** `id` Id no caminho.
- **Sucesso:** 200 Turma (qualquer data).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | TURMA_NAO_ENCONTRADA | — |
  | 422 | (padrão) | formato do id |

### GET /api/turmas/{id}/inscricoes · RF-05
- **Entrada:** `id` Id no caminho.
- **Sucesso:** 200 lista de Inscrição da turma, todas as situações, por `id` crescente.
- **Erros:** 404 TURMA_NAO_ENCONTRADA; 422 formato.

### GET /api/turmas/{id}/relatorio-presenca · RF-10
- **Entrada:** `id` Id no caminho.
- **Sucesso:** 200 `{"turma_id": 1, "presentes": 3, "ausentes": 1, "taxa_presenca_percentual": 75.0}`. Taxa arredondada a 2 casas; `null` se presentes + ausentes = 0 (RN-12, PR-08).
- **Erros:** 404 TURMA_NAO_ENCONTRADA; 422 formato.

### POST /api/inscricoes · RF-04
- **Entrada (JSON):** `turma_id` Id (obrigatório); `nome` Texto (obrigatório); `email` Email (obrigatório; guardado em minúsculas).
- **Sucesso:** 201 Inscrição com `situacao` `CONFIRMADA` ou `ESPERA` (RN-03) e `posicao_espera`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | TURMA_NAO_ENCONTRADA | — |
  | 422 | INSCRICOES_ENCERRADAS | RN-06 |
  | 409 | INSCRICAO_DUPLICADA | RN-05 |
  | 422 | (padrão) | formato |

### POST /api/inscricoes/{id}/cancelar · RF-06, RF-07
- **Entrada:** `id` Id no caminho; sem corpo.
- **Sucesso:** 200 `{"inscricao": Inscrição (CANCELADA), "promovida": Inscrição (CONFIRMADA) | null}` (RN-09).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | INSCRICAO_NAO_ENCONTRADA | — |
  | 422 | CANCELAMENTO_ENCERRADO | RN-07 |
  | 409 | SITUACAO_NAO_CANCELAVEL | RN-08 |

### POST /api/inscricoes/{id}/presenca · RF-08
- **Entrada:** `id` Id no caminho; JSON `situacao` `PRESENTE`|`AUSENTE` (obrigatório).
- **Sucesso:** 200 Inscrição com a nova situação.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | INSCRICAO_NAO_ENCONTRADA | — |
  | 422 | TURMA_NAO_INICIADA | RN-10 |
  | 409 | SITUACAO_SEM_PRESENCA | RN-11, PR-09 |
  | 422 | (padrão) | valor fora de PRESENTE/AUSENTE |

Ordem de checagem quando várias regras falham: existência (404) → regras de tempo (422) → regras de estado (409). Em `POST /api/inscricoes`: RN-06 antes de RN-05.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `turmas.validar_nova_turma` | 422 VAGAS_INVALIDAS |
| RN-02 | `turmas.validar_nova_turma` | 422 DURACAO_INVALIDA |
| PR-04 | `turmas.validar_nova_turma` | 422 INICIO_NO_PASSADO |
| RN-13 | `turmas.vagas_restantes` | — (cálculo) |
| RN-14 | `turmas.eh_futura` (filtro também no SQL `inicio > agora`) | — |
| RN-06 | `inscricoes.validar_janela_inscricao` | 422 INSCRICOES_ENCERRADAS |
| RN-05 | `inscricoes.validar_email_unico` | 409 INSCRICAO_DUPLICADA |
| RN-03 | `inscricoes.situacao_inicial` | — (decide CONFIRMADA/ESPERA) |
| RN-04 | `inscricoes.primeira_da_espera`, `inscricoes.posicoes_espera` | — |
| RN-07 | `inscricoes.validar_cancelamento` | 422 CANCELAMENTO_ENCERRADO |
| RN-08 | `inscricoes.validar_cancelamento` | 409 SITUACAO_NAO_CANCELAVEL |
| RN-09 | `inscricoes.deve_promover` + `primeira_da_espera` | — |
| RN-10 | `inscricoes.validar_presenca` | 422 TURMA_NAO_INICIADA |
| RN-11 | `inscricoes.validar_presenca` | 409 SITUACAO_SEM_PRESENCA |
| RN-12 | `relatorio.taxa_presenca` | — (cálculo) |

Operações que leem e gravam (inscrever, cancelar com promoção, marcar presença) rodam em `banco.transacao`.

## Tela
Página única em `/`, título "Inscrição em treinamentos":
- **Turmas futuras:** tabela de `GET /api/turmas` (título, início em horário local, duração, modalidade, vagas, vagas restantes) com botão "Ver inscritos" por linha.
- **Inscrever-se:** formulário com `turma_id` (select preenchido pelas turmas futuras), `nome`, `email`; envia `POST /api/inscricoes`; mostra "Inscrição CONFIRMADA" ou "Inscrição em ESPERA (posição N)"; recarrega turmas e inscritos.
- **Inscritos da turma:** tabela de `GET /api/turmas/{id}/inscricoes` (nome, e-mail, situação, posição na espera) da turma escolhida.
- Erros da API aparecem com `mostrarMensagem(..., "erro")`. Dados só por `textContent`/`desenharTabela`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/turmas` |
| RF-02 | `GET /api/turmas/{id}` |
| RF-03 | `banco.carga_inicial` |
| RF-04 | `POST /api/inscricoes`; tela "Inscrever-se" |
| RF-05 | `GET /api/turmas/{id}/inscricoes`; tela "Inscritos da turma" |
| RF-06 | `POST /api/inscricoes/{id}/cancelar` |
| RF-07 | `POST /api/inscricoes/{id}/cancelar` (campo `promovida`) |
| RF-08 | `POST /api/inscricoes/{id}/presenca` |
| RF-09 | `GET /api/turmas`; tela "Turmas futuras" |
| RF-10 | `GET /api/turmas/{id}/relatorio-presenca` |
| RF-11 | todos os endpoints acima |
| RF-12 | `GET /` (tela) |
| RF-13 | SQLite em `dados/app.db`; nenhum endpoint de login |

## Plano de testes
Relógio inicial dos testes: 2030-01-07 09:00 -03:00 (`T0`). Turma padrão: início 2030-01-10 09:00 -03:00 (`T0 + 3 dias`), 60 min, ONLINE.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_inscricao_com_vaga_confirmada | CA-01 | T0 | turma 2 vagas; 1 inscrição | 201, situacao CONFIRMADA, posicao_espera null |
| test_ca_02_turma_lotada_entra_em_espera_primeira_da_fila | CA-02 | T0 | turma 1 vaga; 2 inscrições | 2ª: 201, situacao ESPERA, posicao_espera 1 |
| test_ca_03_cancelar_confirmada_promove_primeira_da_espera | CA-03 | T0 | turma 1 vaga; A confirmada, B e C espera; cancelar A | 200, inscricao CANCELADA, promovida.id = B, B CONFIRMADA, C posicao 1 |
| test_ca_04_mesmo_email_duas_vezes_recusado | CA-04 | T0 | mesmo e-mail 2x | 2ª: 409 INSCRICAO_DUPLICADA; 1 inscrito |
| test_ca_05_inscrever_23_horas_antes_recusado | CA-05 | início − 23h | 1 inscrição | 422 INSCRICOES_ENCERRADAS |
| test_ca_06_cancelar_depois_do_inicio_recusado | CA-06 | início + 1h | cancelar confirmada | 422 CANCELAMENTO_ENCERRADO; continua CONFIRMADA |
| test_ca_07_presenca_antes_do_inicio_recusada | CA-07 | início − 1h | presença PRESENTE | 422 TURMA_NAO_INICIADA |
| test_ca_08_presenca_de_inscricao_em_espera_recusada | CA-08 | início + 1h | presença em ESPERA | 409 SITUACAO_SEM_PRESENCA |
| test_ca_09_turma_lotada_aparece_com_zero_vagas | CA-09 | T0 | turma 2 vagas; 2 inscrições; GET /api/turmas | turma com vagas_restantes 0 |
| test_ca_10_taxa_presenca_3_presentes_1_ausente_75 | CA-10 | início + 1h | 4 confirmadas; 3 PRESENTE, 1 AUSENTE | 200, taxa_presenca_percentual 75.0 |
| test_rn_01_vagas_limites | RN-01 | T0 | vagas 0, 1, 50, 51 | 422 VAGAS_INVALIDAS, 201, 201, 422 VAGAS_INVALIDAS |
| test_rn_02_duracao_limites | RN-02 | T0 | duração 0, 1, 1440, 1441 | 422 DURACAO_INVALIDA, 201, 201, 422 DURACAO_INVALIDA |
| test_rn_06_janela_inscricao_bordas | RN-06 | início − 24h − 1min / − 24h / − 24h + 1min | 1 inscrição em cada | 201, 201, 422 INSCRICOES_ENCERRADAS |
| test_rn_07_cancelamento_bordas | RN-07 | início − 1min / início | cancelar | 200; 422 CANCELAMENTO_ENCERRADO |
| test_rn_10_presenca_bordas | RN-10 | início − 1min / início | presença | 422 TURMA_NAO_INICIADA; 200 PRESENTE |
| test_rn_04_fila_por_ordem_de_chegada | RN-04 | T0 | 1 vaga; 3 inscrições | posicao_espera 1 e 2; lista por id |
| test_rn_05_email_sem_diferenciar_maiusculas | RN-05, PR-05 | T0 | `Ana@X.com` e `ana@x.com` | 409 INSCRICAO_DUPLICADA |
| test_rn_05_reinscricao_apos_cancelar | RN-05, PR-06 | T0 | inscrever, cancelar, inscrever | 201 |
| test_rn_05_mesmo_email_outra_turma | RN-05 | T0 | mesmo e-mail em 2 turmas | 201, 201 |
| test_rn_08_cancelar_duas_vezes | RN-08 | T0 | cancelar 2x | 409 SITUACAO_NAO_CANCELAVEL |
| test_rn_09_cancelar_espera_nao_promove | RN-09 | T0 | 1 vaga; cancelar a ESPERA | promovida null; confirmada mantida |
| test_rn_09_promocao_dentro_das_24h | RN-09, PR-07 | início − 2h | cancelar confirmada com fila | promovida CONFIRMADA |
| test_rn_11_presenca_definitiva | RN-11, PR-09 | início + 1h | marcar PRESENTE 2x | 2ª: 409 SITUACAO_SEM_PRESENCA |
| test_rn_11_presenca_valor_invalido | RN-11 | início + 1h | situacao CANCELADA | 422 |
| test_rn_12_taxa_sem_marcacao_vazia | RN-12, PR-08 | T0 | turma sem presenças | taxa null, presentes 0 |
| test_rn_12_taxa_arredondada | RN-12 | início + 1h | 2 PRESENTE, 1 AUSENTE | 66.67 |
| test_rn_13_vagas_restantes_contam_presenca | RN-13 | início + 1h | 2 vagas, 2 confirmadas, 1 PRESENTE, 1 AUSENTE | GET turma: vagas_restantes 0 |
| test_rn_14_turma_passada_fora_da_lista | RN-14 | início + 1min | GET /api/turmas | turma ausente; GET /api/turmas/{id} 200 |
| test_pr_04_inicio_no_passado_recusado | PR-04 | T0 | início = T0 | 422 INICIO_NO_PASSADO |
| test_rf_03_carga_inicial_tres_turmas_futuras | RF-03 | T0 | GET /api/turmas | 3 turmas, todas com inicio > T0 |
| test_rf_05_lista_inscritos | RF-05 | T0 | 2 inscrições | 200, 2 itens em ordem |
| test_inexistentes_404 | 404 | T0 | ids inexistentes nos endpoints | 404 com código |
| test_inicio_sem_fuso_recusado | formato | T0 | `inicio` sem offset | 422 |
