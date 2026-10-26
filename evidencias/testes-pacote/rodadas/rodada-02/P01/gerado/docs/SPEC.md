# SPEC · Empréstimo de equipamentos

Stack padrão: FastAPI + SQLite (`dados/app.db`) + pytest, tela única em `/`. Datas de empréstimo são dias de calendário (`AAAA-MM-DD`, tipo `Data`), gravadas como texto, sem conversão para UTC (PR-01). "Hoje" = `agora.date()` com `agora` vindo de `obter_agora` (fuso America/Sao_Paulo).

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS equipamentos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patrimonio TEXT NOT NULL UNIQUE CHECK (patrimonio GLOB 'EQ-[0-9][0-9][0-9][0-9]'),
  tipo TEXT NOT NULL CHECK (tipo IN ('NOTEBOOK', 'PROJETOR', 'HEADSET')),
  descricao TEXT NOT NULL,
  situacao TEXT NOT NULL DEFAULT 'DISPONIVEL' CHECK (situacao IN ('DISPONIVEL', 'EMPRESTADO', 'MANUTENCAO'))
);

CREATE TABLE IF NOT EXISTS emprestimos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  equipamento_id INTEGER NOT NULL REFERENCES equipamentos(id),
  nome TEXT NOT NULL,
  email TEXT NOT NULL,
  data_retirada TEXT NOT NULL,
  data_prevista TEXT NOT NULL,
  data_devolucao TEXT,
  defeito INTEGER CHECK (defeito IN (0, 1)),
  status TEXT NOT NULL DEFAULT 'ABERTO' CHECK (status IN ('ABERTO', 'DEVOLVIDO')),
  CHECK (data_prevista >= data_retirada)
);

CREATE INDEX IF NOT EXISTS ix_emprestimos_email_status ON emprestimos (email, status);
CREATE INDEX IF NOT EXISTS ix_emprestimos_retirada ON emprestimos (data_retirada);
```

## Carga inicial
Roda ao iniciar, só se `equipamentos` estiver vazia (RF-03, PR-09). Não há datas.

| patrimonio | tipo | descricao | situacao |
|---|---|---|---|
| EQ-0001 | NOTEBOOK | Notebook 14 polegadas (unidade 1) | DISPONIVEL |
| EQ-0002 | NOTEBOOK | Notebook 14 polegadas (unidade 2) | DISPONIVEL |
| EQ-0003 | NOTEBOOK | Notebook 15 polegadas | DISPONIVEL |
| EQ-0004 | PROJETOR | Projetor sala de reunião | DISPONIVEL |
| EQ-0005 | PROJETOR | Projetor portátil | DISPONIVEL |
| EQ-0006 | HEADSET | Headset com microfone (unidade 1) | DISPONIVEL |
| EQ-0007 | HEADSET | Headset com microfone (unidade 2) | DISPONIVEL |
| EQ-0008 | HEADSET | Headset sem fio | MANUTENCAO |

## Endpoints

Corpo de erro de negócio: `{"erro": "<CODIGO>", "mensagem": "<texto>"}`. Erro de formato: 422 padrão do FastAPI.

Equipamento (saída): `{"id": 1, "patrimonio": "EQ-0001", "tipo": "NOTEBOOK", "descricao": "...", "situacao": "DISPONIVEL"}`.

Empréstimo (saída): `{"id": 1, "equipamento_id": 1, "patrimonio": "EQ-0001", "tipo": "NOTEBOOK", "nome": "Ana Teste", "email": "ana@exemplo.com", "data_retirada": "2030-01-07", "data_prevista": "2030-01-10", "data_devolucao": null, "defeito": null, "status": "ABERTO"}`.

### POST /api/equipamentos · RF-01
- **Entrada:** `patrimonio` (str, obrigatório, padrão `^EQ-[0-9]{4}$`), `tipo` (enum `NOTEBOOK|PROJETOR|HEADSET`, obrigatório), `descricao` (`Texto`, obrigatório).
- **Sucesso:** 201, equipamento com `situacao: "DISPONIVEL"`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | (validação) | RN-01 formato, tipo inválido, texto vazio |
  | 409 | PATRIMONIO_DUPLICADO | RN-01 unicidade |

### GET /api/equipamentos · RF-02
- **Entrada:** nenhuma.
- **Sucesso:** 200, lista de equipamentos ordenada por patrimônio (PR-07).
- **Erros:** nenhum.

### GET /api/equipamentos/disponiveis · RF-06
- **Entrada:** consulta `tipo` (enum, opcional).
- **Sucesso:** 200, lista de equipamentos com `situacao = DISPONIVEL`, filtrada por tipo se informado, ordenada por patrimônio.
- **Erros:** 422 (validação) para tipo fora do enum.

### GET /api/equipamentos/{id} · RF-02
- **Entrada:** caminho `id` (`Id`).
- **Sucesso:** 200, equipamento.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | EQUIPAMENTO_NAO_ENCONTRADO | — |
  | 422 | (validação) | id fora da faixa |

### POST /api/emprestimos · RF-04
- **Entrada:** `equipamento_id` (`Id`, obrigatório), `nome` (`Texto`, obrigatório), `email` (`Email`, obrigatório; gravado em minúsculas, PR-04), `data_prevista` (`Data`, obrigatório).
- **Sucesso:** 201, empréstimo com `status: "ABERTO"`, `data_retirada` = hoje; o equipamento passa a `EMPRESTADO`.
- **Erros** (ordem de verificação: equipamento existe → RN-02 → RN-05 → RN-04 → RN-06):
  | Status | Código | Regra |
  |---|---|---|
  | 404 | EQUIPAMENTO_NAO_ENCONTRADO | — |
  | 409 | EQUIPAMENTO_INDISPONIVEL | RN-02 |
  | 422 | DATA_PREVISTA_ANTERIOR | RN-05 |
  | 422 | PRAZO_EXCEDIDO | RN-04 |
  | 409 | LIMITE_EMPRESTIMOS | RN-06 |
  | 422 | (validação) | formato de campos |

### GET /api/emprestimos · RF-08
- **Entrada:** consulta `status` (enum `ABERTO|DEVOLVIDO`, opcional).
- **Sucesso:** 200, lista de empréstimos ordenada por id.
- **Erros:** 422 (validação) para status fora do enum.

### GET /api/emprestimos/atrasados · RF-07
- **Entrada:** nenhuma.
- **Sucesso:** 200, lista de empréstimos `ABERTO` com `data_prevista < hoje`, cada um com o campo extra `dias_atraso` (int, `hoje − data_prevista` em dias), ordenada por `dias_atraso` decrescente e id.
- **Erros:** nenhum.

### POST /api/emprestimos/{id}/devolver · RF-05
- **Entrada:** caminho `id` (`Id`); corpo `defeito` (bool, opcional, padrão `false`).
- **Sucesso:** 200, empréstimo com `status: "DEVOLVIDO"`, `data_devolucao` = hoje, `defeito`; equipamento vai a `MANUTENCAO` (defeito) ou `DISPONIVEL`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | EMPRESTIMO_NAO_ENCONTRADO | — |
  | 409 | EMPRESTIMO_JA_DEVOLVIDO | RN-07 |
  | 422 | (validação) | id fora da faixa, `defeito` não booleano |

### GET /api/relatorios/emprestimos-por-tipo · RF-09
- **Entrada:** consulta `mes` (str obrigatório, `AAAA-MM`, ano 2000–2100, mês 01–12).
- **Sucesso:** 200 `{"mes": "2030-01", "itens": [{"tipo": "NOTEBOOK", "quantidade": 2}, {"tipo": "PROJETOR", "quantidade": 0}, {"tipo": "HEADSET", "quantidade": 1}]}` — sempre os 3 tipos, nessa ordem.
- **Erros:** 422 (validação) para mês em formato ou faixa inválidos.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | formato: tipo `Patrimonio` em `app/rotas/equipamentos.py`; unicidade: `equipamentos.validar_patrimonio_unico` | 422 (validação) / 409 PATRIMONIO_DUPLICADO |
| RN-02 | `emprestimos.validar_disponivel` | 409 EQUIPAMENTO_INDISPONIVEL |
| RN-03 | `emprestimos.data_hoje` | — |
| RN-04 | `emprestimos.validar_prazo` (`PRAZO_MAXIMO_DIAS = {NOTEBOOK: 14, PROJETOR: 3, HEADSET: 3}`) | 422 PRAZO_EXCEDIDO |
| RN-05 | `emprestimos.validar_prazo` | 422 DATA_PREVISTA_ANTERIOR |
| RN-06 | `emprestimos.validar_limite_pessoa` (`LIMITE_ABERTOS = 2`) | 409 LIMITE_EMPRESTIMOS |
| RN-07 | `emprestimos.validar_devolucao` | 409 EMPRESTIMO_JA_DEVOLVIDO |
| RN-08 | `emprestimos.situacao_apos_devolucao` | — |
| RN-09 | `emprestimos.dias_atraso` | — |
| RN-10 | `relatorio.periodo_do_mes` + `relatorio.montar_relatorio` | — |

## Tela
Página única em `/`, título "Empréstimo de equipamentos":
- **Emprestar:** formulário com seletor de equipamento disponível (de `GET /api/equipamentos/disponiveis`), nome, e-mail e data prevista; envia `POST /api/emprestimos`.
- **Empréstimos em aberto:** tabela de `GET /api/emprestimos?status=ABERTO` com caixa "com defeito" e botão "Devolver" por linha, que chama `POST /api/emprestimos/{id}/devolver`.
- **Atrasados:** tabela de `GET /api/emprestimos/atrasados` com dias de atraso.
- **Disponíveis:** tabela de `GET /api/equipamentos/disponiveis` com filtro por tipo.
- Toda ação mostra sucesso ou a `mensagem` de erro da API (`mostrarMensagem`) e recarrega as listas. Dados entram só por `textContent`/`desenharTabela`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/equipamentos` |
| RF-02 | `GET /api/equipamentos`, `GET /api/equipamentos/{id}` |
| RF-03 | `banco.carga_inicial` |
| RF-04 | `POST /api/emprestimos`; tela "Emprestar" |
| RF-05 | `POST /api/emprestimos/{id}/devolver`; tela "Empréstimos em aberto" |
| RF-06 | `GET /api/equipamentos/disponiveis`; tela "Disponíveis" |
| RF-07 | `GET /api/emprestimos/atrasados`; tela "Atrasados" |
| RF-08 | `GET /api/emprestimos` |
| RF-09 | `GET /api/relatorios/emprestimos-por-tipo` |
| RF-10 | todos os endpoints `/api` |
| RF-11 | tela em `/` |
| RF-12 | SQLite em `dados/app.db`, sem autenticação |

## Plano de testes
Relógio padrão: 2030-01-07 09:00 -03:00 (hoje = 2030-01-07). Cada teste cria o que confere; equipamentos novos são criados via `POST /api/equipamentos`.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_emprestar_disponivel_dentro_do_prazo | CA-01 | 2030-01-07 | notebook novo, prevista 2030-01-14 | 201 status ABERTO, retirada 2030-01-07; equipamento EMPRESTADO |
| test_ca_02_recusa_equipamento_ja_emprestado | CA-02 | 2030-01-07 | 2º empréstimo do mesmo equipamento | 409 EQUIPAMENTO_INDISPONIVEL |
| test_ca_03_recusa_equipamento_em_manutencao | CA-03 | 2030-01-07 | equipamento devolvido com defeito, novo empréstimo | 409 EQUIPAMENTO_INDISPONIVEL |
| test_ca_03_recusa_headset_inicial_em_manutencao | CA-03, RF-03 | 2030-01-07 | EQ-0008 da carga inicial | 409 EQUIPAMENTO_INDISPONIVEL |
| test_ca_04_recusa_notebook_15_dias | CA-04 | 2030-01-07 | notebook, prevista 2030-01-22 | 422 PRAZO_EXCEDIDO; equipamento DISPONIVEL |
| test_ca_05_projetor_3_dias_criado | CA-05 | 2030-01-07 | projetor, prevista 2030-01-10 | 201 status ABERTO |
| test_ca_06_recusa_terceiro_emprestimo_aberto | CA-06 | 2030-01-07 | 3 empréstimos com o mesmo e-mail | 3º: 409 LIMITE_EMPRESTIMOS |
| test_ca_07_devolver_sem_defeito | CA-07 | 2030-01-07 → +2 dias | devolver `defeito=false` | 200 DEVOLVIDO, devolução 2030-01-09; equipamento DISPONIVEL |
| test_ca_08_devolver_com_defeito | CA-08 | 2030-01-07 | devolver `defeito=true` | 200 DEVOLVIDO; equipamento MANUTENCAO |
| test_ca_09_atrasado_um_dia | CA-09 | 2030-01-07 → +2 dias | prevista 2030-01-08, consulta em 2030-01-09 | item com dias_atraso=1 |
| test_ca_10_recusa_devolver_ja_devolvido | CA-10 | 2030-01-07 | devolver duas vezes | 2ª: 409 EMPRESTIMO_JA_DEVOLVIDO |
| test_rn_01_patrimonio_formato_invalido | RN-01 | — | `EQ-123`, `EQ-12345`, `eq-0001`, `XX-0001` | 422 |
| test_rn_01_patrimonio_duplicado | RN-01 | — | EQ-0001 (já existe) | 409 PATRIMONIO_DUPLICADO |
| test_rn_04_notebook_borda_13_14_15 | RN-04 | 2030-01-07 | prevista +13, +14, +15 dias | 201, 201, 422 PRAZO_EXCEDIDO |
| test_rn_04_projetor_borda_2_3_4 | RN-04 | 2030-01-07 | prevista +2, +3, +4 dias | 201, 201, 422 |
| test_rn_04_headset_borda_2_3_4 | RN-04 | 2030-01-07 | prevista +2, +3, +4 dias | 201, 201, 422 |
| test_rn_05_prevista_igual_retirada_aceita_ontem_recusada | RN-05 | 2030-01-07 | prevista 2030-01-07 / 2030-01-06 | 201 / 422 DATA_PREVISTA_ANTERIOR |
| test_rn_06_limite_por_email_sem_diferenca_de_caixa | RN-06, PR-04 | 2030-01-07 | 2 com `ana@exemplo.com`, 3º com `ANA@Exemplo.com` | 409 LIMITE_EMPRESTIMOS |
| test_rn_06_devolucao_libera_limite | RN-06 | 2030-01-07 | 2 abertos, devolve 1, pede outro | 201 |
| test_rn_09_borda_prevista_hoje_nao_atrasa | RN-09 | 2030-01-07 → +1 dia | prevista 2030-01-08, consulta em 2030-01-08 e 2030-01-10 | ausente; depois dias_atraso=2 |
| test_rn_09_devolvido_nao_aparece_nos_atrasados | RN-09 | 2030-01-07 → +3 dias | devolvido em atraso | ausente dos atrasados |
| test_rn_10_relatorio_por_tipo_no_mes | RN-10 | 2030-01-31 → 2030-02-01 | 2 notebooks e 1 headset em jan; 1 projetor em 1º/fev | jan: 2/0/1; fev: 0/1/0 |
| test_rn_10_mes_invalido | RN-10 | — | `2030-13`, `2030-1`, `1999-12`, `abc` | 422 |
| test_rf_03_carga_inicial | RF-03 | — | `GET /api/equipamentos` | 8 itens: 3/2/3, um HEADSET MANUTENCAO |
| test_rf_06_disponiveis_filtro_tipo | RF-06 | — | `?tipo=HEADSET` | 2 headsets (EQ-0008 fora) |
| test_rf_08_lista_por_status | RF-08 | 2030-01-07 | 1 aberto e 1 devolvido | filtro retorna 1 de cada |
| test_equipamento_e_emprestimo_inexistentes | 404 | — | ids 999999 | 404 EQUIPAMENTO_NAO_ENCONTRADO / EMPRESTIMO_NAO_ENCONTRADO |
