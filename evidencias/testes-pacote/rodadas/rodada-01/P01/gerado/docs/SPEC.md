# SPEC · Empréstimo de equipamentos

Stack: a padrão da fábrica (Python 3.11, FastAPI, SQLite via `sqlite3`, pytest, tela única em `app/estatico/index.html`).

## Modelo de dados

Datas de empréstimo (PR-02) são datas de calendário no fuso America/Sao_Paulo, gravadas em `TEXT` no formato `YYYY-MM-DD`. Não há hora, então não há conversão para UTC; o único carimbo com hora (`criado_em`) é gravado em UTC com `relogio.para_banco`.

```sql
CREATE TABLE IF NOT EXISTS equipamentos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patrimonio TEXT NOT NULL UNIQUE CHECK (patrimonio GLOB 'EQ-[0-9][0-9][0-9][0-9]'),
  tipo TEXT NOT NULL CHECK (tipo IN ('NOTEBOOK', 'PROJETOR', 'HEADSET')),
  descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 200),
  situacao TEXT NOT NULL DEFAULT 'DISPONIVEL' CHECK (situacao IN ('DISPONIVEL', 'EMPRESTADO', 'MANUTENCAO'))
);

CREATE TABLE IF NOT EXISTS emprestimos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  equipamento_id INTEGER NOT NULL REFERENCES equipamentos(id),
  nome TEXT NOT NULL CHECK (length(nome) BETWEEN 1 AND 200),
  email TEXT NOT NULL CHECK (length(email) BETWEEN 3 AND 200),
  data_retirada TEXT NOT NULL,
  data_prevista TEXT NOT NULL CHECK (data_prevista >= data_retirada),
  data_devolucao TEXT,
  defeito INTEGER CHECK (defeito IN (0, 1)),
  status TEXT NOT NULL DEFAULT 'ABERTO' CHECK (status IN ('ABERTO', 'DEVOLVIDO')),
  criado_em TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_emprestimo_aberto_por_equipamento
  ON emprestimos(equipamento_id) WHERE status = 'ABERTO';

CREATE INDEX IF NOT EXISTS ix_emprestimos_email_status ON emprestimos(email, status);
```

`email` é gravado em minúsculas, sem espaços nas pontas (PR-04).

## Carga inicial

Executada por `banco.carga_inicial` só quando `equipamentos` está vazia (RF-12).

| patrimonio | tipo | descricao | situacao |
|---|---|---|---|
| EQ-0001 | NOTEBOOK | Notebook 14 polegadas - unidade 1 | DISPONIVEL |
| EQ-0002 | NOTEBOOK | Notebook 14 polegadas - unidade 2 | DISPONIVEL |
| EQ-0003 | NOTEBOOK | Notebook 15 polegadas - unidade 3 | DISPONIVEL |
| EQ-0004 | PROJETOR | Projetor multimídia - sala A | DISPONIVEL |
| EQ-0005 | PROJETOR | Projetor portátil - sala B | DISPONIVEL |
| EQ-0006 | HEADSET | Headset USB - unidade 1 | DISPONIVEL |
| EQ-0007 | HEADSET | Headset USB - unidade 2 | DISPONIVEL |
| EQ-0008 | HEADSET | Headset sem fio - unidade 3 | MANUTENCAO |

## Formatos

- Datas de empréstimo: `YYYY-MM-DD` (ISO 8601 de data), só como texto. Número, data com hora ou data inexistente: `422` do framework.
- Ids no caminho: inteiros de 1 a 2^63−1 (limite do SQLite); fora disso, `422` do framework.
- "Hoje" = `agora` (relógio injetável) convertido para America/Sao_Paulo, parte de data (RN-03, PR-01).
- Dias de atraso: inteiro, dias de calendário (RN-11).
- Mês do relatório: `YYYY-MM`.

## Endpoints

Representação de equipamento (`Equipamento`):
`{"id": 1, "patrimonio": "EQ-0001", "tipo": "NOTEBOOK", "descricao": "Notebook 14 polegadas - unidade 1", "situacao": "DISPONIVEL"}`

Representação de empréstimo (`Emprestimo`):
`{"id": 1, "equipamento_id": 1, "patrimonio": "EQ-0001", "tipo": "NOTEBOOK", "nome": "Ana Exemplo", "email": "ana@exemplo.test", "data_retirada": "2030-01-07", "data_prevista": "2030-01-10", "data_devolucao": null, "defeito": null, "status": "ABERTO", "situacao_equipamento": "EMPRESTADO"}`

### POST /api/equipamentos · RF-01
- **Entrada (JSON):** `patrimonio` texto obrigatório (máx. 20); `tipo` enum `NOTEBOOK|PROJETOR|HEADSET` obrigatório; `descricao` texto obrigatório, 1 a 200.
- **Sucesso:** 201 `Equipamento` com `situacao: "DISPONIVEL"`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | PATRIMONIO_INVALIDO | RN-01 (formato) |
  | 409 | PATRIMONIO_DUPLICADO | RN-01 (unicidade) |
  | 422 | (framework) | campo faltando, tipo fora do enum, texto vazio ou longo |

### GET /api/equipamentos · RF-02, RF-05
- **Entrada (consulta):** `tipo` opcional (enum); `situacao` opcional (enum `DISPONIVEL|EMPRESTADO|MANUTENCAO`). Disponíveis por tipo: `?situacao=DISPONIVEL&tipo=PROJETOR`.
- **Sucesso:** 200 lista de `Equipamento`, ordenada por patrimônio (PR-08).
- **Erros:** 422 (framework) para enum inválido.

### GET /api/equipamentos/{id} · RF-02
- **Entrada:** `id` inteiro no caminho.
- **Sucesso:** 200 `Equipamento`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | EQUIPAMENTO_NAO_ENCONTRADO | — |

### POST /api/emprestimos · RF-03
- **Entrada (JSON):** `equipamento_id` inteiro de 1 a 2^63−1 obrigatório; `nome` texto 1 a 200 obrigatório; `email` texto até 200, formato `texto@texto.texto` obrigatório; `data_prevista` data `YYYY-MM-DD` obrigatória. A data de retirada não é informada (RN-03, PR-06).
- **Sucesso:** 201 `Emprestimo` com `status: "ABERTO"`, `data_retirada` = hoje e `situacao_equipamento: "EMPRESTADO"` (RN-07).
- **Erros** (avaliados nesta ordem):
  | Status | Código | Regra |
  |---|---|---|
  | 404 | EQUIPAMENTO_NAO_ENCONTRADO | — |
  | 409 | EQUIPAMENTO_INDISPONIVEL | RN-02 |
  | 422 | DATA_PREVISTA_ANTERIOR | RN-05 |
  | 422 | PRAZO_EXCEDIDO | RN-04 |
  | 422 | LIMITE_EMPRESTIMOS | RN-06 |
  | 422 | (framework) | campo faltando, e-mail inválido, data inválida |

### GET /api/emprestimos · RF-08
- **Entrada (consulta):** `status` opcional (`ABERTO|DEVOLVIDO`).
- **Sucesso:** 200 lista de `Emprestimo`, por `data_retirada` e `id` (PR-08).
- **Erros:** 422 (framework) para status inválido.

### GET /api/emprestimos/atrasados · RF-06
- **Entrada:** nenhuma.
- **Sucesso:** 200 lista de `Emprestimo` com o campo extra `dias_atraso` (inteiro ≥ 1), do maior atraso para o menor, empate por `id` (RN-11, PR-08).
- **Erros:** nenhum específico.

### POST /api/emprestimos/{id}/devolver · RF-04
- **Entrada:** `id` no caminho; JSON `{"defeito": false}` (`defeito` booleano, opcional, padrão `false`; corpo pode ser omitido).
- **Sucesso:** 200 `Emprestimo` com `status: "DEVOLVIDO"`, `data_devolucao` = hoje, `defeito` e `situacao_equipamento` = `MANUTENCAO` se defeito, senão `DISPONIVEL` (RN-08, RN-09).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | EMPRESTIMO_NAO_ENCONTRADO | — |
  | 409 | EMPRESTIMO_JA_DEVOLVIDO | RN-10 |

### GET /api/relatorios/emprestimos-por-tipo · RF-07
- **Entrada (consulta):** `mes` obrigatório, `YYYY-MM` (mês 01 a 12).
- **Sucesso:** 200 `{"mes": "2030-01", "itens": [{"tipo": "NOTEBOOK", "quantidade": 2}, {"tipo": "PROJETOR", "quantidade": 1}, {"tipo": "HEADSET", "quantidade": 0}], "total": 3}` (RN-12, PR-07).
- **Erros:** 422 (framework) para `mes` ausente ou fora do formato; 422 `MES_INVALIDO` para mês 00 ou maior que 12.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `equipamentos.validar_patrimonio`, `equipamentos.garantir_patrimonio_unico` | 422 PATRIMONIO_INVALIDO, 409 PATRIMONIO_DUPLICADO |
| RN-02 | `emprestimos.validar_disponivel` | 409 EQUIPAMENTO_INDISPONIVEL |
| RN-03 | `emprestimos.hoje` | — |
| RN-04 | `emprestimos.validar_prazo` (`PRAZO_MAXIMO_DIAS`) | 422 PRAZO_EXCEDIDO |
| RN-05 | `emprestimos.validar_prazo` | 422 DATA_PREVISTA_ANTERIOR |
| RN-06 | `emprestimos.validar_limite_pessoa` (`MAXIMO_ABERTOS = 2`) | 422 LIMITE_EMPRESTIMOS |
| RN-07 | `emprestimos.situacao_ao_emprestar` | — |
| RN-08 | `emprestimos.validar_devolucao` + repositório grava data e status | — |
| RN-09 | `emprestimos.situacao_apos_devolucao` | — |
| RN-10 | `emprestimos.validar_devolucao` | 409 EMPRESTIMO_JA_DEVOLVIDO |
| RN-11 | `emprestimos.dias_atraso` | — |
| RN-12 | `emprestimos.intervalo_do_mes` | 422 MES_INVALIDO |

E-mail é normalizado por `emprestimos.normalizar_email` (PR-04). Registro de empréstimo e devolução rodam dentro de `banco.transacao` (conferir situação/limite e gravar).

## Tela
- Página única em `/`, com três blocos:
  - **Emprestar:** seletor de equipamento disponível (carregado de `GET /api/equipamentos?situacao=DISPONIVEL`, com filtro por tipo), nome, e-mail, data prevista; botão chama `POST /api/emprestimos`.
  - **Empréstimos em aberto:** tabela de `GET /api/emprestimos?status=ABERTO`, cada linha com caixa "com defeito" e botão "Devolver" que chama `POST /api/emprestimos/{id}/devolver`.
  - **Atrasados:** tabela de `GET /api/emprestimos/atrasados` com dias de atraso.
- Após cada ação, as três listas recarregam. Mensagem de erro da API (`mensagem` ou detalhe do 422) aparece em destaque; dados exibidos com `textContent`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/equipamentos` |
| RF-02 | `GET /api/equipamentos`, `GET /api/equipamentos/{id}` |
| RF-03 | `POST /api/emprestimos`; tela, bloco Emprestar |
| RF-04 | `POST /api/emprestimos/{id}/devolver`; tela, bloco Em aberto |
| RF-05 | `GET /api/equipamentos?situacao=DISPONIVEL&tipo=...`; tela, seletor |
| RF-06 | `GET /api/emprestimos/atrasados`; tela, bloco Atrasados |
| RF-07 | `GET /api/relatorios/emprestimos-por-tipo?mes=YYYY-MM` |
| RF-08 | `GET /api/emprestimos?status=...` |
| RF-09 | todos os endpoints acima |
| RF-10 | `GET /` (tela) |
| RF-11 | SQLite em `dados/app.db`; nenhum endpoint de login |
| RF-12 | `banco.carga_inicial` |

## Plano de testes

Relógio padrão: 2030-01-07 09:00 -03:00 (segunda-feira). "Equipamento N" = id N da carga inicial (1-3 NOTEBOOK, 4-5 PROJETOR, 6-8 HEADSET, 8 em MANUTENCAO).

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_emprestar_disponivel | CA-01 | 2030-01-07 09:00 | equip. 1, prevista 2030-01-10 | 201, status ABERTO, situacao_equipamento EMPRESTADO; GET equip. 1 → EMPRESTADO |
| test_ca_02_recusa_equipamento_emprestado | CA-02 | 2030-01-07 09:00 | equip. 1 emprestado, novo pedido de outra pessoa | 409 EQUIPAMENTO_INDISPONIVEL |
| test_ca_03_recusa_equipamento_em_manutencao | CA-03 | 2030-01-07 09:00 | equip. 8 | 409 EQUIPAMENTO_INDISPONIVEL |
| test_ca_04_recusa_notebook_15_dias | CA-04 | 2030-01-07 09:00 | equip. 1, prevista 2030-01-22 | 422 PRAZO_EXCEDIDO; equip. 1 segue DISPONIVEL |
| test_ca_05_projetor_3_dias_criado | CA-05 | 2030-01-07 09:00 | equip. 4, prevista 2030-01-10 | 201, status ABERTO |
| test_ca_06_recusa_terceiro_emprestimo | CA-06 | 2030-01-07 09:00 | mesmo e-mail em equip. 1, 2, 3 | 3º: 422 LIMITE_EMPRESTIMOS |
| test_ca_07_devolver_sem_defeito | CA-07 | 2030-01-07 → 2030-01-09 | empresta equip. 1, avança 2 dias, devolve `defeito=false` | 200, DEVOLVIDO, data_devolucao 2030-01-09, situacao DISPONIVEL |
| test_ca_08_devolver_com_defeito | CA-08 | 2030-01-07 09:00 | empresta equip. 6, devolve `defeito=true` | 200, situacao_equipamento MANUTENCAO |
| test_ca_09_atrasado_um_dia | CA-09 | 2030-01-07 → 2030-01-08 | empresta equip. 4 prevista 2030-01-07, avança 1 dia | atrasados contém o id com dias_atraso 1 |
| test_ca_10_recusa_devolver_ja_devolvido | CA-10 | 2030-01-07 09:00 | devolve duas vezes | 2ª: 409 EMPRESTIMO_JA_DEVOLVIDO |
| test_rn_04_notebook_13_dias_aceito | RN-04 | 2030-01-07 | equip. 1, prevista 2030-01-20 | 201 |
| test_rn_04_notebook_14_dias_aceito | RN-04 | 2030-01-07 | equip. 1, prevista 2030-01-21 | 201 |
| test_rn_04_projetor_2_dias_aceito | RN-04 | 2030-01-07 | equip. 4, prevista 2030-01-09 | 201 |
| test_rn_04_projetor_4_dias_recusado | RN-04 | 2030-01-07 | equip. 4, prevista 2030-01-11 | 422 PRAZO_EXCEDIDO |
| test_rn_04_headset_3_dias_aceito | RN-04 | 2030-01-07 | equip. 6, prevista 2030-01-10 | 201 |
| test_rn_04_headset_4_dias_recusado | RN-04 | 2030-01-07 | equip. 6, prevista 2030-01-11 | 422 PRAZO_EXCEDIDO |
| test_rn_05_prevista_ontem_recusada | RN-05 | 2030-01-07 | prevista 2030-01-06 | 422 DATA_PREVISTA_ANTERIOR |
| test_rn_05_prevista_hoje_aceita | RN-05 | 2030-01-07 | prevista 2030-01-07 | 201 |
| test_rn_06_segundo_emprestimo_aceito | RN-06 | 2030-01-07 | 2 empréstimos mesmo e-mail | ambos 201 |
| test_rn_06_email_com_maiusculas_mesma_pessoa | RN-06, PR-04 | 2030-01-07 | 2 abertos com e-mail minúsculo, 3º com maiúsculas | 422 LIMITE_EMPRESTIMOS |
| test_rn_06_devolucao_libera_novo_emprestimo | RN-06 | 2030-01-07 | 2 abertos, devolve 1, pede outro | 201 |
| test_rn_03_retirada_usa_data_local | RN-03, PR-01 | 2030-01-07 22:30 -03:00 (01:30 UTC do dia 8) | prevista 2030-01-07 | 201, data_retirada 2030-01-07 |
| test_rn_11_prevista_hoje_nao_atrasa | RN-11 | 2030-01-07 | prevista 2030-01-07, sem avançar | atrasados vazio |
| test_rn_11_tres_dias_de_atraso | RN-11 | 2030-01-07 → 2030-01-13 | projetor prevista 2030-01-10, avança 6 dias | dias_atraso 3 |
| test_rn_11_devolvido_nao_atrasa | RN-11 | 2030-01-07 → 2030-01-09 | prevista 07, devolve no dia 9 | atrasados vazio |
| test_rn_01_patrimonio_formato_invalido | RN-01 | — | `EQ-123`, `EQ-12345`, `eq-0001`, `XX-0001` | 422 PATRIMONIO_INVALIDO |
| test_rn_01_patrimonio_duplicado | RN-01 | — | `EQ-0001` | 409 PATRIMONIO_DUPLICADO |
| test_rf_01_cadastrar_equipamento | RF-01 | — | `EQ-0100`, HEADSET | 201, situacao DISPONIVEL |
| test_rf_02_consultar_equipamento_inexistente | RF-02 | — | GET /api/equipamentos/999 | 404 EQUIPAMENTO_NAO_ENCONTRADO |
| test_rf_12_carga_inicial | RF-12 | — | GET /api/equipamentos | 8 itens; 3/2/3 por tipo; só EQ-0008 em MANUTENCAO |
| test_rf_05_disponiveis_filtro_tipo | RF-05 | 2030-01-07 | empresta equip. 1; GET ?situacao=DISPONIVEL&tipo=NOTEBOOK | EQ-0002, EQ-0003 |
| test_rf_07_relatorio_por_tipo_no_mes | RF-07, RN-12 | 2030-01-07 → 2030-02-01 | 2 notebooks + 1 projetor em jan (um devolvido), 1 headset em fev | jan: 2/1/0, total 3; fev: 0/0/1 |
| test_rf_07_mes_invalido | RF-07 | — | `mes=2030-13`, `mes=2030-1` | 422 |
| test_rf_08_listar_por_status | RF-08 | 2030-01-07 | 2 empréstimos, devolve 1 | ?status=ABERTO 1 item, ?status=DEVOLVIDO 1 item |
| test_erro_equipamento_inexistente_no_emprestimo | RF-03 | 2030-01-07 | equipamento_id 999 | 404 EQUIPAMENTO_NAO_ENCONTRADO |
| test_erro_emprestimo_inexistente_na_devolucao | RF-04 | — | id 999 | 404 EMPRESTIMO_NAO_ENCONTRADO |
| test_erro_validacao_entrada | RF-03 | — | sem e-mail; e-mail `sem-arroba`; data `amanha`; nome vazio | 422 |
