# SPEC · Férias da equipe

Stack: a padrão da fábrica (Python 3.11, FastAPI, SQLite em `dados/app.db`, pytest, tela `index.html` servida em `/`).
Datas de férias são `Data` (`AAAA-MM-DD`, sem horário nem fuso), gravadas como texto `AAAA-MM-DD`. "Hoje" = `agora.date()` no fuso America/Sao_Paulo (PR-01). Períodos fechados `[inicio, fim]` (PR-02).

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS colaboradores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
  email TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(email) BETWEEN 3 AND 254),
  equipe TEXT NOT NULL CHECK (equipe IN ('DADOS', 'PRODUTO', 'SUPORTE')),
  saldo INTEGER NOT NULL DEFAULT 30 CHECK (saldo BETWEEN 0 AND 365)
);

CREATE TABLE IF NOT EXISTS solicitacoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colaborador_id INTEGER NOT NULL REFERENCES colaboradores(id),
  inicio TEXT NOT NULL,
  fim TEXT NOT NULL,
  dias INTEGER NOT NULL CHECK (dias BETWEEN 5 AND 30),
  situacao TEXT NOT NULL CHECK (situacao IN ('SOLICITADA', 'APROVADA', 'REPROVADA', 'CANCELADA')),
  criada_em TEXT NOT NULL,
  CHECK (fim >= inicio)
);

CREATE INDEX IF NOT EXISTS ix_solicitacoes_colaborador ON solicitacoes (colaborador_id, situacao);
CREATE INDEX IF NOT EXISTS ix_solicitacoes_periodo ON solicitacoes (situacao, inicio, fim);
```

`criada_em` em UTC (`relogio.para_banco`). `saldo` é o saldo guardado, já sem os dias aprovados (PR-04).

## Carga inicial
Roda só com `colaboradores` vazia (RF-03). Saldo 30 para todos. Nomes e e-mails fictícios (domínio reservado `exemplo.com`).

| nome | email | equipe |
|---|---|---|
| Ana Ribeiro | ana.ribeiro@exemplo.com | DADOS |
| Bruno Carvalho | bruno.carvalho@exemplo.com | DADOS |
| Carla Mendes | carla.mendes@exemplo.com | DADOS |
| Diego Fontes | diego.fontes@exemplo.com | PRODUTO |
| Elisa Moraes | elisa.moraes@exemplo.com | PRODUTO |
| Fábio Teixeira | fabio.teixeira@exemplo.com | PRODUTO |
| Gabriela Nunes | gabriela.nunes@exemplo.com | SUPORTE |
| Hugo Pacheco | hugo.pacheco@exemplo.com | SUPORTE |
| Isabela Prado | isabela.prado@exemplo.com | SUPORTE |

Nenhuma data na carga inicial (não há solicitações iniciais).

## Endpoints

Corpo de erro de negócio: `{"erro": "<CODIGO>", "mensagem": "<texto>"}`. Validação de formato: 422 padrão do framework.

Objeto **Colaborador**: `{"id": 1, "nome": "Ana Ribeiro", "email": "ana.ribeiro@exemplo.com", "equipe": "DADOS", "saldo": 30, "saldo_disponivel": 20}` — `saldo_disponivel` = `saldo` − soma dos `dias` das `SOLICITADA` do colaborador (RN-04).

Objeto **Solicitação**: `{"id": 1, "colaborador_id": 1, "colaborador_nome": "Ana Ribeiro", "equipe": "DADOS", "inicio": "2030-02-16", "fim": "2030-02-25", "dias": 10, "situacao": "SOLICITADA"}`.

### GET /api/saude · infraestrutura (modelo de projeto)
- **Entrada:** nenhuma.
- **Sucesso:** 200 `{"status": "ok"}`. Usado pelo roteiro de verificação para saber que o servidor subiu.
- **Erros:** nenhum.

### POST /api/colaboradores · RF-01
- **Entrada:** `nome` (`Texto`, obrigatório), `email` (`Email`, obrigatório), `equipe` (`Literal["DADOS","PRODUTO","SUPORTE"]`, obrigatório), `saldo` (`int`, 0 a 365, opcional, padrão 30).
- **Sucesso:** 201 Colaborador.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | (framework) | RN-11 formato, faixa, equipe |
  | 409 | EMAIL_DUPLICADO | RN-11 / PR-11 |

### GET /api/colaboradores · RF-02
- **Entrada:** nenhuma.
- **Sucesso:** 200 lista de Colaborador, ordenada por equipe e nome (PR-09).
- **Erros:** nenhum de negócio.

### GET /api/colaboradores/{id} · RF-02
- **Entrada:** `id` (`Id`, caminho).
- **Sucesso:** 200 Colaborador.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | COLABORADOR_NAO_ENCONTRADO | — |
  | 422 | (framework) | id fora da faixa |

### POST /api/solicitacoes · RF-04
- **Entrada:** `colaborador_id` (`Id`), `inicio` (`Data`), `fim` (`Data`), todos obrigatórios.
- **Sucesso:** 201 Solicitação com `situacao` `SOLICITADA` e `dias` calculado.
- **Erros** (conferidos nesta ordem):
  | Status | Código | Regra |
  |---|---|---|
  | 404 | COLABORADOR_NAO_ENCONTRADO | — |
  | 422 | PERIODO_INVALIDO | RN-01 (fim antes do início) |
  | 422 | DURACAO_INVALIDA | RN-02 |
  | 422 | ANTECEDENCIA_INSUFICIENTE | RN-03 |
  | 409 | SOBREPOSICAO | RN-05 |
  | 409 | SALDO_INSUFICIENTE | RN-04 |

### GET /api/solicitacoes · RF-05
- **Entrada:** nenhuma.
- **Sucesso:** 200 lista de Solicitação, ordenada por `inicio` e `id` (PR-09).
- **Erros:** nenhum de negócio.

### GET /api/solicitacoes/{id} · RF-05
- **Entrada:** `id` (`Id`, caminho).
- **Sucesso:** 200 Solicitação.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SOLICITACAO_NAO_ENCONTRADA | — |

### POST /api/solicitacoes/{id}/aprovar · RF-06
- **Entrada:** `id` (`Id`, caminho). Sem corpo.
- **Sucesso:** 200 Solicitação com `situacao` `APROVADA`; `saldo` do colaborador reduzido em `dias` (RN-08).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SOLICITACAO_NAO_ENCONTRADA | — |
  | 409 | TRANSICAO_INVALIDA | RN-06 |
  | 409 | LIMITE_EQUIPE | RN-07 |

### POST /api/solicitacoes/{id}/reprovar · RF-07
- **Entrada:** `id` (`Id`, caminho). Sem corpo.
- **Sucesso:** 200 Solicitação com `situacao` `REPROVADA`; saldo inalterado (PR-06).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SOLICITACAO_NAO_ENCONTRADA | — |
  | 409 | TRANSICAO_INVALIDA | RN-06 |

### POST /api/solicitacoes/{id}/cancelar · RF-08
- **Entrada:** `id` (`Id`, caminho). Sem corpo.
- **Sucesso:** 200 Solicitação com `situacao` `CANCELADA`; se era `APROVADA`, `saldo` volta a somar `dias` (RN-10).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SOLICITACAO_NAO_ENCONTRADA | — |
  | 409 | TRANSICAO_INVALIDA | RN-09 (situação REPROVADA ou CANCELADA) |
  | 422 | CANCELAMENTO_FORA_DO_PRAZO | RN-09 (hoje ≥ início) |

### GET /api/calendario · RF-09
- **Entrada:** `mes` (consulta, obrigatório, tipo `Mes` novo em `app/tipos.py`: `AAAA-MM`, mês 01–12, ano 2000–2100).
- **Sucesso:** 200 `{"mes": "2030-02", "dias": [{"data": "2030-02-01", "equipes": {"DADOS": [{"colaborador_id": 1, "nome": "Ana Ribeiro", "solicitacao_id": 3}], "PRODUTO": [], "SUPORTE": []}}, ...]}` — um item por dia do mês (PR-08), só solicitações `APROVADA`; nomes ordenados.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | (framework) | formato de `mes` |

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `ferias.calcular_dias(inicio, fim)` | 422 PERIODO_INVALIDO |
| RN-02 | `ferias.validar_duracao(dias)` | 422 DURACAO_INVALIDA |
| RN-03 | `ferias.validar_antecedencia(inicio, agora)` | 422 ANTECEDENCIA_INSUFICIENTE |
| RN-04 | `ferias.validar_saldo(dias, saldo, dias_pendentes)` | 409 SALDO_INSUFICIENTE |
| RN-05 | `ferias.validar_sem_sobreposicao(inicio, fim, periodos_ativos)` | 409 SOBREPOSICAO |
| RN-06 | `ferias.validar_decisao(situacao)` | 409 TRANSICAO_INVALIDA |
| RN-07 | `ferias.validar_limite_equipe(inicio, fim, periodos_aprovados_equipe)` | 409 LIMITE_EQUIPE |
| RN-08 | `ferias.saldo_apos_aprovacao(saldo, dias)` | — |
| RN-09 | `ferias.validar_cancelamento(situacao, inicio, agora)` | 409 TRANSICAO_INVALIDA / 422 CANCELAMENTO_FORA_DO_PRAZO |
| RN-10 | `ferias.saldo_apos_cancelamento(saldo, dias, situacao)` | — |
| RN-11 | modelo Pydantic `ColaboradorEntrada` + `colaboradores.validar_email_livre(existe)` | 422 framework / 409 EMAIL_DUPLICADO |

Sobreposição (RN-05, RN-07): `a.inicio <= b.fim e b.inicio <= a.fim`. Calendário: `ferias.montar_calendario(ano, mes, aprovadas)`.
Aprovar, reprovar, cancelar e solicitar leem e gravam dentro de `banco.transacao(conn)`.

## Tela
Uma página (`/`), título "Férias da equipe", quatro blocos:
- **Colaboradores e saldo:** tabela (nome, equipe, e-mail, saldo, saldo disponível) — `GET /api/colaboradores`.
- **Solicitar férias:** formulário com colaborador (select preenchido por `GET /api/colaboradores`), início e fim (`type=date`) — `POST /api/solicitacoes`.
- **Solicitações:** tabela (código, colaborador, equipe, início, fim, dias, situação) com botões Aprovar e Reprovar (se `SOLICITADA`) e Cancelar (se `SOLICITADA` ou `APROVADA`) — `GET /api/solicitacoes`, `POST .../aprovar`, `.../reprovar`, `.../cancelar`.
- **Calendário do mês:** campo `type=month` e botão Ver; tabela com uma linha por dia e colunas DADOS, PRODUTO, SUPORTE com os nomes — `GET /api/calendario?mes=`.
Sucesso e erro aparecem em `mostrarMensagem` (mensagem da API). Dados exibidos só por `textContent`/`desenharTabela`. Após cada ação, recarrega colaboradores, solicitações e calendário.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/colaboradores` |
| RF-02 | `GET /api/colaboradores`, `GET /api/colaboradores/{id}`, tela (Colaboradores e saldo) |
| RF-03 | `banco.carga_inicial` |
| RF-04 | `POST /api/solicitacoes`, tela (Solicitar férias) |
| RF-05 | `GET /api/solicitacoes`, `GET /api/solicitacoes/{id}`, tela (Solicitações) |
| RF-06 | `POST /api/solicitacoes/{id}/aprovar`, tela |
| RF-07 | `POST /api/solicitacoes/{id}/reprovar`, tela |
| RF-08 | `POST /api/solicitacoes/{id}/cancelar`, tela |
| RF-09 | `GET /api/calendario`, tela (Calendário do mês) |
| RF-10 | Todos os endpoints `/api/...` |
| RF-11 | `GET /` (`app/estatico/index.html`) |
| RF-12 | SQLite local `dados/app.db`, sem autenticação |

## Plano de testes
Relógio de teste: `2030-01-07 09:00 -03:00` (hoje = 2030-01-07; +30 dias = 2030-02-06; +40 dias = 2030-02-16). Cada teste cria seus colaboradores via `POST /api/colaboradores`.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_solicitar_10_dias_com_40_de_antecedencia | CA-01 | 2030-01-07 | 2030-02-16 a 2030-02-25 | 201, situacao SOLICITADA, dias 10 |
| test_ca_02_solicitar_4_dias_recusado | CA-02 | 2030-01-07 | 2030-02-16 a 2030-02-19 | 422 DURACAO_INVALIDA |
| test_ca_03_inicio_em_29_dias_recusado | CA-03 | 2030-01-07 | 2030-02-05 a 2030-02-14 | 422 ANTECEDENCIA_INSUFICIENTE |
| test_ca_04_mais_dias_que_saldo_disponivel_recusado | CA-04 | 2030-01-07 | saldo 30, pendente 25 dias, novo pedido 10 dias | 409 SALDO_INSUFICIENTE |
| test_ca_05_aprovar_reduz_saldo | CA-05 | 2030-01-07 | aprovar pedido de 10 dias | 200 APROVADA; GET colaborador saldo 20 |
| test_ca_06_aprovar_segunda_pessoa_mesma_equipe_recusado | CA-06 | 2030-01-07 | A aprovada 02-16..02-25; B mesma equipe 02-20..03-01 | 409 LIMITE_EQUIPE; B segue SOLICITADA |
| test_ca_07_aprovar_outra_equipe_mesmo_periodo | CA-07 | 2030-01-07 | A DADOS aprovada; C PRODUTO mesmo período | 200 APROVADA |
| test_ca_08_mesma_equipe_comecando_no_dia_seguinte | CA-08 | 2030-01-07 | A 02-16..02-25 aprovada; B mesma equipe 02-26..03-07 | 200 APROVADA |
| test_ca_09_cancelar_aprovada_devolve_saldo | CA-09 | 2030-01-07 | aprovar e cancelar | 200 CANCELADA; saldo 30 |
| test_ca_10_calendario_mostra_so_aprovadas | CA-10 | 2030-01-07 | DADOS APROVADA, PRODUTO SOLICITADA, SUPORTE REPROVADA, mesmo período | 200; 28 dias; 2030-02-16 só a pessoa aprovada |
| test_rn_01_fim_antes_do_inicio_recusado | RN-01 | 2030-01-07 | 2030-02-20 a 2030-02-16 | 422 PERIODO_INVALIDO |
| test_rn_02_bordas_da_duracao | RN-02 | 2030-01-07 | 4, 5, 30, 31 dias | 422, 201, 201, 422 DURACAO_INVALIDA |
| test_rn_03_bordas_da_antecedencia | RN-03 | 2030-01-07 | início em +29, +30, +31 dias | 422 ANTECEDENCIA_INSUFICIENTE, 201, 201 |
| test_rn_04_bordas_do_saldo_disponivel | RN-04 | 2030-01-07 | saldo 12 com 5 dias pendentes (disponível 7): pede 8, depois 7 | 8 dias: 409 SALDO_INSUFICIENTE; 7 dias (igual ao disponível): 201 |
| test_rn_04_aprovada_descontada_uma_vez | RN-04, PR-04 | 2030-01-07 | saldo 30, aprova 10, pede 20 | 201; saldo_disponivel 0 |
| test_rn_05_sobreposicao_do_mesmo_colaborador | RN-05 | 2030-01-07 | 1 dia em comum; dia seguinte; após cancelar | 409 SOBREPOSICAO; 201; 201 |
| test_rn_06_so_solicitada_pode_ser_decidida | RN-06 | 2030-01-07 | reprovar, aprovar a reprovada, reprovar aprovada | 200 REPROVADA saldo igual; 409 TRANSICAO_INVALIDA; 409 |
| test_rn_07_limite_equipe_um_dia_em_comum | RN-07 | 2030-01-07 | B começa no último dia de A | 409 LIMITE_EQUIPE |
| test_rn_09_bordas_do_cancelamento | RN-09 | avança 39 e 40 dias | início 2030-02-16 | dia 02-15: 200; dia 02-16: 422 CANCELAMENTO_FORA_DO_PRAZO |
| test_rn_09_cancelar_finalizada_recusado | RN-09 | 2030-01-07 | cancelar CANCELADA e REPROVADA | 409 TRANSICAO_INVALIDA |
| test_rn_10_cancelar_solicitada_nao_mexe_no_saldo | RN-10 | 2030-01-07 | cancelar SOLICITADA | 200; saldo 30, disponível 30 |
| test_rn_11_bordas_do_saldo_inicial | RN-11 | — | saldo -1, 0, 365, 366, ausente | 422, 201, 201, 422, 201 com 30 |
| test_rn_11_email_duplicado_e_equipe_invalida | RN-11 | — | mesmo e-mail em maiúsculas; equipe "RH" | 409 EMAIL_DUPLICADO; 422 |
| test_rf_03_carga_inicial_9_colaboradores_3_por_equipe | RF-03 | 2030-01-07 | GET /api/colaboradores | 9 itens, 3 por equipe, saldo 30 |
| test_rf_02_e_rf_05_inexistente_404 | RF-02, RF-05 | — | ids inexistentes em GET e ações | 404 com código |
| test_rf_09_mes_invalido_recusado | RF-09 | — | `2030-13`, `2030-1`, `9999-01` | 422 |
