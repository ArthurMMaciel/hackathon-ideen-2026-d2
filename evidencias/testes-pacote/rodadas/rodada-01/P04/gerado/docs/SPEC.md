# SPEC · Férias da equipe

Stack padrão da fábrica (FastAPI + SQLite + pytest). Datas de férias são datas sem hora (`YYYY-MM-DD`, PR-02), gravadas como `TEXT` nesse formato; a ordem lexicográfica coincide com a cronológica. Momentos com hora (`criado_em`) seguem a regra transversal: ISO 8601 com offset na API, UTC no banco. "Hoje" = `agora.date()` no fuso America/Sao_Paulo (PR-01), com `agora` vindo de `relogio.obter_agora`.

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS colaboradores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 120),
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  equipe TEXT NOT NULL CHECK (equipe IN ('DADOS', 'PRODUTO', 'SUPORTE')),
  saldo INTEGER NOT NULL DEFAULT 30 CHECK (saldo >= 0)
);

CREATE TABLE IF NOT EXISTS solicitacoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colaborador_id INTEGER NOT NULL REFERENCES colaboradores(id),
  inicio TEXT NOT NULL,
  fim TEXT NOT NULL,
  dias INTEGER NOT NULL CHECK (dias BETWEEN 5 AND 30),
  situacao TEXT NOT NULL CHECK (situacao IN ('SOLICITADA', 'APROVADA', 'REPROVADA', 'CANCELADA')),
  criado_em TEXT NOT NULL,
  CHECK (fim >= inicio)
);

CREATE INDEX IF NOT EXISTS ix_solicitacoes_periodo ON solicitacoes (situacao, inicio, fim);
```

`saldo` é o saldo atual (RN-08/RN-10 o alteram). Saldo disponível é calculado (RN-04), não gravado.

## Carga inicial
Executada só quando `colaboradores` está vazia (RF-03). Todos com saldo 30. E-mails no domínio reservado `exemplo.test`.

| nome | email | equipe |
|---|---|---|
| Ana Ribeiro | ana.ribeiro@exemplo.test | DADOS |
| Bruno Tavares | bruno.tavares@exemplo.test | DADOS |
| Carla Nunes | carla.nunes@exemplo.test | DADOS |
| Diego Prates | diego.prates@exemplo.test | PRODUTO |
| Elisa Moura | elisa.moura@exemplo.test | PRODUTO |
| Fabio Lessa | fabio.lessa@exemplo.test | PRODUTO |
| Gabriela Souto | gabriela.souto@exemplo.test | SUPORTE |
| Heitor Vilela | heitor.vilela@exemplo.test | SUPORTE |
| Iris Campos | iris.campos@exemplo.test | SUPORTE |

## Endpoints

Corpo de erro de negócio: `{"erro": "<CODIGO>", "mensagem": "<texto>"}`. Validação de formato: 422 padrão do FastAPI.

Representação de colaborador:
`{"id": 1, "nome": "Ana Ribeiro", "email": "ana.ribeiro@exemplo.test", "equipe": "DADOS", "saldo": 30, "saldo_disponivel": 30}`

Representação de solicitação:
`{"id": 1, "colaborador_id": 1, "colaborador_nome": "Ana Ribeiro", "equipe": "DADOS", "inicio": "2030-02-16", "fim": "2030-02-25", "dias": 10, "situacao": "SOLICITADA", "criado_em": "2030-01-07T09:00:00-03:00"}`

### GET /api/colaboradores · RF-02
- **Entrada:** nenhuma.
- **Sucesso:** 200, lista de colaboradores ordenada por equipe e nome (PR-07).
- **Erros:** nenhum.

### GET /api/colaboradores/{id} · RF-02
- **Entrada:** `id` inteiro no caminho.
- **Sucesso:** 200, um colaborador (com `saldo` e `saldo_disponivel`).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | COLABORADOR_NAO_ENCONTRADO | — |

### POST /api/colaboradores · RF-01
- **Entrada:** `nome` texto 1..120 (obrigatório); `email` texto até 200, formato `x@y.z` (obrigatório); `equipe` `DADOS`|`PRODUTO`|`SUPORTE` (obrigatório); `saldo` inteiro 0..365 (opcional, padrão 30).
- **Sucesso:** 201, colaborador criado.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | (padrão do framework) | RN-11, RN-12 formato |
  | 409 | EMAIL_DUPLICADO | RN-12 |

### GET /api/solicitacoes · RF-05
- **Entrada:** consulta opcional `situacao` (um dos quatro valores) e `colaborador_id` (inteiro ≥ 1).
- **Sucesso:** 200, lista de solicitações ordenada por `inicio` e `id` (PR-07).
- **Erros:** 422 padrão para valores fora do formato.

### POST /api/solicitacoes · RF-04
- **Entrada:** `colaborador_id` inteiro ≥ 1; `inicio` e `fim` datas `YYYY-MM-DD` (obrigatórios).
- **Sucesso:** 201, solicitação com `situacao` `SOLICITADA`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | COLABORADOR_NAO_ENCONTRADO | — |
  | 422 | PERIODO_INVALIDO | RN-01 |
  | 422 | DURACAO_INVALIDA | RN-02 |
  | 422 | ANTECEDENCIA_INSUFICIENTE | RN-03 |
  | 422 | SALDO_INSUFICIENTE | RN-04 |
  | 409 | SOBREPOSICAO_COLABORADOR | RN-05 |

### POST /api/solicitacoes/{id}/aprovar · RF-06
- **Entrada:** `id` no caminho.
- **Sucesso:** 200, solicitação com `situacao` `APROVADA`; saldo do colaborador reduzido em `dias` (RN-08).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SOLICITACAO_NAO_ENCONTRADA | — |
  | 409 | SITUACAO_INVALIDA | RN-06 |
  | 409 | LIMITE_EQUIPE | RN-07 |

### POST /api/solicitacoes/{id}/reprovar · RF-07
- **Entrada:** `id` no caminho.
- **Sucesso:** 200, solicitação com `situacao` `REPROVADA`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SOLICITACAO_NAO_ENCONTRADA | — |
  | 409 | SITUACAO_INVALIDA | RN-06 |

### POST /api/solicitacoes/{id}/cancelar · RF-08
- **Entrada:** `id` no caminho.
- **Sucesso:** 200, solicitação com `situacao` `CANCELADA`; se estava `APROVADA`, saldo devolvido (RN-10).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | SOLICITACAO_NAO_ENCONTRADA | — |
  | 409 | SITUACAO_INVALIDA | RN-09 (só `SOLICITADA`/`APROVADA`) |
  | 422 | CANCELAMENTO_FORA_DO_PRAZO | RN-09 (hoje ≥ início) |

### GET /api/calendario · RF-09
- **Entrada:** consulta obrigatória `mes` no formato `YYYY-MM` (mês 01..12).
- **Sucesso:** 200, um item por dia do mês, só com solicitações `APROVADA` (PR-06):
  `{"mes": "2030-03", "dias": [{"data": "2030-03-01", "equipes": {"DADOS": [{"colaborador_id": 1, "nome": "Ana Ribeiro", "solicitacao_id": 3}], "PRODUTO": [], "SUPORTE": []}}, ...]}`
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | MES_INVALIDO | formato de `mes` |

### GET /api/saude · RF-10
- **Entrada:** nenhuma. **Sucesso:** 200 `{"status": "ok"}`. **Erros:** nenhum.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `ferias.contar_dias` | 422 PERIODO_INVALIDO |
| RN-02 | `ferias.validar_duracao` | 422 DURACAO_INVALIDA |
| RN-03 | `ferias.validar_antecedencia` | 422 ANTECEDENCIA_INSUFICIENTE |
| RN-04 | `ferias.validar_saldo` | 422 SALDO_INSUFICIENTE |
| RN-05 | `ferias.validar_sem_sobreposicao_colaborador` (usa `ferias.sobrepoe`) | 409 SOBREPOSICAO_COLABORADOR |
| RN-06 | `ferias.validar_pode_decidir` | 409 SITUACAO_INVALIDA |
| RN-07 | `ferias.validar_limite_equipe` (usa `ferias.sobrepoe`) | 409 LIMITE_EQUIPE |
| RN-08 | `ferias.saldo_apos_aprovar` | — |
| RN-09 | `ferias.validar_cancelamento` | 409 SITUACAO_INVALIDA / 422 CANCELAMENTO_FORA_DO_PRAZO |
| RN-10 | `ferias.saldo_apos_cancelar` | — |
| RN-11 | modelo Pydantic `ColaboradorEntrada.saldo` (`ge=0, le=365`) | 422 padrão |
| RN-12 | `colaboradores.validar_email_unico` + regex no modelo Pydantic | 409 EMAIL_DUPLICADO / 422 padrão |

Sobreposição de períodos fechados (PR-02): `a.inicio <= b.fim e b.inicio <= a.fim`. Equivale ao semiaberto `[inicio, fim + 1 dia)` da regra transversal; dias consecutivos não se sobrepõem (CA-08).

## Tela
Uma página (`/`), três blocos:
- **Solicitar férias:** seleção de colaborador (de `GET /api/colaboradores`), datas de início e fim, botão Solicitar (`POST /api/solicitacoes`).
- **Solicitações:** tabela com colaborador, equipe, início, fim, dias, situação e botões Aprovar, Reprovar, Cancelar conforme a situação (`GET /api/solicitacoes`, `POST .../aprovar|reprovar|cancelar`). Abaixo, tabela de colaboradores com saldo e saldo disponível.
- **Calendário:** seletor de mês e tabela dia × equipe com os nomes em férias aprovadas (`GET /api/calendario`).
- Mensagens de sucesso e a `mensagem` de erro da API aparecem numa área de status. Dados inseridos via `textContent`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/colaboradores` |
| RF-02 | `GET /api/colaboradores`, `GET /api/colaboradores/{id}` |
| RF-03 | `banco.carga_inicial` |
| RF-04 | `POST /api/solicitacoes`, tela (Solicitar) |
| RF-05 | `GET /api/solicitacoes`, tela (Solicitações) |
| RF-06 | `POST /api/solicitacoes/{id}/aprovar`, tela |
| RF-07 | `POST /api/solicitacoes/{id}/reprovar`, tela |
| RF-08 | `POST /api/solicitacoes/{id}/cancelar`, tela |
| RF-09 | `GET /api/calendario`, tela (Calendário) |
| RF-10 | todos os endpoints `/api` |
| RF-11 | `GET /` (`app/estatico/index.html`) |
| RF-12 | SQLite em `dados/app.db`, sem autenticação |

## Plano de testes
Relógio padrão: 2030-01-07 09:00 -03:00 (hoje = 2030-01-07; início mínimo = 2030-02-06). Colaboradores da carga: 1–3 DADOS, 4–6 PRODUTO, 7–9 SUPORTE.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_solicitar_10_dias_com_40_de_antecedencia | CA-01 | padrão | colab 1, 2030-02-16 a 2030-02-25 | 201, situacao SOLICITADA, dias 10 |
| test_ca_02_recusa_4_dias | CA-02 | padrão | colab 1, 2030-03-01 a 2030-03-04 | 422 DURACAO_INVALIDA |
| test_ca_03_recusa_inicio_em_29_dias | CA-03 | padrão | colab 1, 2030-02-05 a 2030-02-14 | 422 ANTECEDENCIA_INSUFICIENTE |
| test_ca_04_recusa_mais_dias_que_saldo_disponivel | CA-04 | padrão | colab 1: 20 dias (03-01..03-20) e depois 15 dias (04-01..04-15) | 2º: 422 SALDO_INSUFICIENTE |
| test_ca_05_aprovar_reduz_saldo | CA-05 | padrão | colab 1, 10 dias; aprovar | 200 APROVADA; saldo 20 |
| test_ca_06_recusa_segunda_aprovacao_mesma_equipe | CA-06 | padrão | colab 1 e 2 (DADOS) com dias em comum; aprovar ambos | 2º: 409 LIMITE_EQUIPE, continua SOLICITADA |
| test_ca_07_aprova_outra_equipe_mesmo_periodo | CA-07 | padrão | colab 1 (DADOS) e 4 (PRODUTO), mesmo período | ambos 200 APROVADA |
| test_ca_08_aprova_mesma_equipe_dia_seguinte_ao_fim | CA-08 | padrão | colab 1: 03-01..03-10; colab 2: 03-11..03-20 | ambos 200 APROVADA |
| test_ca_09_cancelar_aprovada_devolve_saldo | CA-09 | padrão | colab 1, 10 dias aprovada; cancelar | 200 CANCELADA; saldo 30 |
| test_ca_10_calendario_so_mostra_aprovadas | CA-10 | padrão | março/2030: 1 APROVADA, 1 SOLICITADA, 1 REPROVADA | só o nome da aprovada nos dias |
| test_rn_02_bordas_duracao | RN-02 | padrão | 4, 5, 30, 31 dias | 422, 201, 201, 422 |
| test_rn_03_bordas_antecedencia | RN-03 | padrão | início em 29, 30, 31 dias | 422, 201, 201 |
| test_rn_04_bordas_saldo | RN-04 | padrão | pedido de 10 dias para colaboradores novos com saldo 9, 10 e 11 | 422 SALDO_INSUFICIENTE, 201, 201 |
| test_rn_01_fim_antes_do_inicio | RN-01 | padrão | fim < início | 422 PERIODO_INVALIDO |
| test_rn_05_recusa_sobreposicao_mesmo_colaborador | RN-05 | padrão | colab 1 dois pedidos com 1 dia em comum; e um encostado | 409 SOBREPOSICAO_COLABORADOR; encostado 201 |
| test_rn_05_ignora_reprovada_e_cancelada | RN-05 | padrão | pedido reprovado, novo no mesmo período | 201 |
| test_rn_06_so_solicitada_pode_ser_decidida | RN-06 | padrão | aprovar/reprovar uma APROVADA e uma REPROVADA | 409 SITUACAO_INVALIDA |
| test_rn_07_um_dia_em_comum_conflita | RN-07 | padrão | colab 1 03-01..03-10 aprovada; colab 2 03-10..03-14 | 409 LIMITE_EQUIPE |
| test_rn_09_bordas_cancelamento | RN-09 | avança até início − 1 dia e até o início | cancelar | véspera 200; no dia 422 CANCELAMENTO_FORA_DO_PRAZO |
| test_rn_09_nao_cancela_reprovada | RN-09 | padrão | cancelar REPROVADA | 409 SITUACAO_INVALIDA |
| test_rn_09_cancelar_solicitada_nao_altera_saldo | RN-09/RN-10 | padrão | cancelar SOLICITADA | 200, saldo 30, disponível 30 |
| test_rn_11_bordas_saldo_cadastro | RN-11 | padrão | saldo −1, 0, 365, 366 | 422, 201, 201, 422 |
| test_rn_12_email_duplicado_e_invalido | RN-12 | padrão | e-mail da carga; e-mail sem @ | 409 EMAIL_DUPLICADO; 422 |
| test_rf_01_cadastro_saldo_padrao_30 | RF-01 | padrão | sem saldo | 201, saldo 30 |
| test_rf_03_carga_inicial_9_colaboradores | RF-03 | padrão | GET colaboradores | 9, 3 por equipe, saldo 30 |
| test_rf_05_filtros_listagem | RF-05 | padrão | filtro situacao e colaborador_id | só os correspondentes |
| test_rf_09_mes_invalido | RF-09 | padrão | `mes=2030-13`, `mes=abc` | 422 MES_INVALIDO |
| test_erros_404 | — | padrão | ids inexistentes | 404 com código |
