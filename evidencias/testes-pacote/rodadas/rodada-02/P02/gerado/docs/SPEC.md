# SPEC · Reembolso de despesas

Stack: a da `stack-padrao` (Python 3.11, FastAPI, SQLite `dados/app.db`, pytest, tela única em `/`).

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS despesas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colaborador_nome TEXT NOT NULL CHECK (length(colaborador_nome) BETWEEN 1 AND 200),
  colaborador_email TEXT NOT NULL CHECK (length(colaborador_email) BETWEEN 3 AND 254),
  data TEXT NOT NULL CHECK (length(data) = 10),
  categoria TEXT NOT NULL CHECK (categoria IN ('TRANSPORTE', 'HOSPEDAGEM', 'ALIMENTACAO', 'OUTROS')),
  valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
  descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 200),
  comprovante TEXT NOT NULL CHECK (length(comprovante) BETWEEN 1 AND 200),
  situacao TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (situacao IN ('PENDENTE', 'APROVADA', 'RECUSADA', 'PAGA')),
  motivo_recusa TEXT,
  UNIQUE (colaborador_email, comprovante)
);
CREATE INDEX IF NOT EXISTS ix_despesas_data ON despesas (data);
```

- `data`: texto `AAAA-MM-DD` (data de calendário, sem horário e sem conversão para UTC; PR-02).
- `colaborador_email`: gravado em minúsculas (PR-03). `comprovante`: sem espaços nas pontas (PR-04).
- Não há coluna de data e hora: nenhum requisito pede momento de lançamento.

## Carga inicial

Só quando `despesas` está vazia (RF-08). `hoje` = `agora.date()` no fuso America/Sao_Paulo. E-mails no domínio reservado `.example`.

| # | colaborador_nome | colaborador_email | data | categoria | valor_centavos | descricao | comprovante | situacao | motivo_recusa |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Ana Souza | ana.souza@empresa.example | hoje − 1 | TRANSPORTE | 8550 | Táxi do aeroporto ao hotel | NF-1001 | PENDENTE | |
| 2 | Bruno Lima | bruno.lima@empresa.example | hoje − 3 | HOSPEDAGEM | 38000 | Hotel, uma diária | NF-2001 | APROVADA | |
| 3 | Carla Mendes | carla.mendes@empresa.example | hoje − 6 | ALIMENTACAO | 9500 | Jantar fora do roteiro | NF-3001 | RECUSADA | Despesa fora do período da viagem |
| 4 | Ana Souza | ana.souza@empresa.example | hoje − 10 | OUTROS | 4500 | Estacionamento | NF-1002 | PAGA | |
| 5 | Bruno Lima | bruno.lima@empresa.example | hoje − 20 | ALIMENTACAO | 6000 | Almoço durante a viagem | NF-2002 | PENDENTE | |

## Formato da despesa (saída)

```json
{"id": 1, "colaborador_nome": "Ana Souza", "colaborador_email": "ana.souza@empresa.example",
 "data": "2030-01-06", "categoria": "TRANSPORTE", "valor_centavos": 8550,
 "descricao": "Táxi do aeroporto ao hotel", "comprovante": "NF-1001",
 "situacao": "PENDENTE", "motivo_recusa": null}
```

Valores em centavos inteiros (PR-05): R$ 120,01 = `12001`.

## Endpoints

Erros de negócio: `{"erro": "<CODIGO>", "mensagem": "<texto>"}`. Erros de formato: 422 padrão do FastAPI.

### POST /api/despesas · RF-01, RF-09
- **Entrada (JSON):** `colaborador_nome` `Texto` (obrigatório, 1–200); `colaborador_email` `Email` (obrigatório); `data` `Data` (obrigatório, `AAAA-MM-DD`, ano 2000–2100); `categoria` enum `TRANSPORTE|HOSPEDAGEM|ALIMENTACAO|OUTROS` (obrigatório); `valor_centavos` `Centavos` (obrigatório, inteiro 0–100.000.000); `descricao` `Texto`; `comprovante` `Texto`.
- **Sucesso:** 201, despesa com `situacao: "PENDENTE"` e `motivo_recusa: null` (RN-06).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | VALOR_INVALIDO | RN-01 (valor 0) |
  | 422 | VALOR_ACIMA_DO_LIMITE | RN-02 |
  | 422 | DATA_FUTURA | RN-03 |
  | 422 | DATA_MUITO_ANTIGA | RN-04 |
  | 409 | COMPROVANTE_DUPLICADO | RN-05 |
  | 422 | (padrão) | formato: campo faltando, tipo errado, fora da faixa, valor negativo |

### GET /api/despesas · RF-06, RF-09
- **Entrada (consulta):** `email` `Email` opcional (comparado em minúsculas); `situacao` enum opcional `PENDENTE|APROVADA|RECUSADA|PAGA`.
- **Sucesso:** 200, lista de despesas ordenada por `data` desc, `id` desc (PR-07). `[]` quando nada casa.
- **Erros:** 422 padrão para e-mail ou situação inválidos.

### POST /api/despesas/{id}/aprovar · RF-02
- **Entrada:** `id` `Id` no caminho; sem corpo.
- **Sucesso:** 200, despesa com `situacao: "APROVADA"`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | DESPESA_NAO_ENCONTRADA | — |
  | 409 | TRANSICAO_INVALIDA | RN-07 |

### POST /api/despesas/{id}/recusar · RF-03
- **Entrada:** `id` `Id`; corpo JSON opcional `{"motivo": string | null}`, `max_length` 200 (opcional no modelo, exigido no domínio).
- **Sucesso:** 200, despesa com `situacao: "RECUSADA"` e `motivo_recusa` sem espaços nas pontas.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | DESPESA_NAO_ENCONTRADA | — |
  | 422 | MOTIVO_OBRIGATORIO | RN-08 (ausente, nulo, vazio ou só espaços; conferido antes de RN-07, PR-12) |
  | 409 | TRANSICAO_INVALIDA | RN-07 |

### POST /api/despesas/{id}/pagar · RF-04
- **Entrada:** `id` `Id`; sem corpo.
- **Sucesso:** 200, despesa com `situacao: "PAGA"`.
- **Erros:** 404 DESPESA_NAO_ENCONTRADA; 409 TRANSICAO_INVALIDA (RN-07).

### DELETE /api/despesas/{id} · RF-05
- **Entrada:** `id` `Id`.
- **Sucesso:** 204, sem corpo.
- **Erros:** 404 DESPESA_NAO_ENCONTRADA; 409 EXCLUSAO_NAO_PERMITIDA (RN-09).

### GET /api/saude · RF-09 (vem do modelo de projeto)
- **Entrada:** nenhuma.
- **Sucesso:** 200 `{"status": "ok"}`. Usado pela verificação para saber que o servidor subiu.
- **Erros:** nenhum.

### GET /api/relatorios/mensal · RF-07
- **Entrada (consulta):** `mes` obrigatório, tipo `Mes` (novo em `app/tipos.py`): `AAAA-MM`, ano 2000–2100, mês 01–12.
- **Sucesso:** 200 `{"mes": "2030-01", "totais_centavos": {"TRANSPORTE": 0, "HOSPEDAGEM": 38000, "ALIMENTACAO": 0, "OUTROS": 0}, "total_geral_centavos": 38000}`. Soma só APROVADA e PAGA com `data` entre o dia 1 e o último dia do mês, inclusive (RN-10, PR-08). As 4 categorias sempre presentes.
- **Erros:** 422 padrão para `mes` ausente ou fora do formato.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `despesas.validar_valor` | 422 VALOR_INVALIDO |
| RN-02 | `despesas.validar_valor` (tabela `LIMITES_CENTAVOS`: ALIMENTACAO 12000, HOSPEDAGEM 45000, TRANSPORTE 100000, OUTROS 100000) | 422 VALOR_ACIMA_DO_LIMITE |
| RN-03 | `despesas.validar_data(data, agora)` | 422 DATA_FUTURA |
| RN-04 | `despesas.validar_data(data, agora)` (`data < hoje − 60 dias` recusa) | 422 DATA_MUITO_ANTIGA |
| RN-05 | `despesas.verificar_duplicidade(ja_existe)` | 409 COMPROVANTE_DUPLICADO |
| RN-06 | `despesas.SITUACAO_INICIAL` | — |
| RN-07 | `despesas.validar_transicao(atual, nova)` (tabela `TRANSICOES`) | 409 TRANSICAO_INVALIDA |
| RN-08 | `despesas.validar_motivo(motivo)` | 422 MOTIVO_OBRIGATORIO |
| RN-09 | `despesas.validar_exclusao(situacao)` | 409 EXCLUSAO_NAO_PERMITIDA |
| RN-10 | `despesas.SITUACOES_NO_RESUMO`, `despesas.intervalo_do_mes(mes)`, `despesas.montar_resumo(mes, somas)` | — |

Também em `despesas`: `normalizar_email` (PR-03). Conferir e gravar (duplicidade + inserção; leitura de situação + mudança; leitura + exclusão) roda dentro de `banco.transacao`.

## Tela
Página única em `/`, título "Reembolso de despesas":
- **Lançar despesa:** formulário com nome, e-mail, data (`type=date`), categoria (select), valor em reais (`type=number`, `step=0.01`, convertido para centavos com `Math.round(valor*100)`), descrição, comprovante. Chama `POST /api/despesas`.
- **Despesas:** filtros por e-mail e situação, botão Filtrar (`GET /api/despesas?email=&situacao=`); tabela com colaborador, e-mail, data, categoria, valor (R$), descrição, comprovante, situação, motivo e ações: Aprovar (`POST .../aprovar`), Recusar com campo de motivo na linha (`POST .../recusar`), Pagar (`POST .../pagar`), Excluir (`DELETE ...`). Botões só aparecem nas situações em que a ação é permitida.
- **Resumo do mês:** campo `type=month` (padrão: mês atual do navegador) e botão; tabela com total por categoria e total geral em R$ (`GET /api/relatorios/mensal?mes=`).
- Toda resposta de erro da API aparece com `mostrarMensagem(..., "erro")`. Dados só por `textContent`/`desenharTabela`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/despesas`, tela "Lançar despesa" |
| RF-02 | `POST /api/despesas/{id}/aprovar`, botão Aprovar |
| RF-03 | `POST /api/despesas/{id}/recusar`, botão Recusar com motivo |
| RF-04 | `POST /api/despesas/{id}/pagar`, botão Pagar |
| RF-05 | `DELETE /api/despesas/{id}`, botão Excluir |
| RF-06 | `GET /api/despesas?email=&situacao=`, filtros da tela |
| RF-07 | `GET /api/relatorios/mensal?mes=`, tela "Resumo do mês" |
| RF-08 | `banco.carga_inicial` (tabela da Carga inicial) |
| RF-09 | todos os endpoints acima |
| RF-10 | `app/estatico/index.html` servido em `/` |
| RF-11 | SQLite local `dados/app.db`; nenhum endpoint de login; colaborador informado no corpo |

## Plano de testes

Relógio padrão: 2030-01-07 09:00 −03:00 (hoje = 2030-01-07). Base de despesa válida: `TRANSPORTE`, 5000 centavos, data 2030-01-05.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_lancar_despesa_valida_fica_pendente | CA-01, RN-06 | padrão | despesa válida | 201, `situacao=PENDENTE`, campos ecoados |
| test_ca_02_alimentacao_120_01_recusada_por_limite | CA-02, RN-02 | padrão | ALIMENTACAO 12001 | 422 `VALOR_ACIMA_DO_LIMITE` |
| test_ca_03_hospedagem_450_00_criada | CA-03, RN-02 | padrão | HOSPEDAGEM 45000 | 201, `situacao=PENDENTE`, `valor_centavos=45000` |
| test_ca_04_data_61_dias_atras_recusada | CA-04, RN-04 | padrão | data 2029-11-07 | 422 `DATA_MUITO_ANTIGA` |
| test_ca_05_data_de_amanha_recusada | CA-05, RN-03 | padrão | data 2030-01-08 | 422 `DATA_FUTURA` |
| test_ca_06_mesmo_comprovante_mesmo_colaborador_recusado | CA-06, RN-05 | padrão | dois POST iguais | 201 e depois 409 `COMPROVANTE_DUPLICADO` |
| test_ca_07_recusar_sem_motivo_recusado | CA-07, RN-08 | padrão | recusar sem corpo e com `{}` | 422 `MOTIVO_OBRIGATORIO`; despesa segue PENDENTE |
| test_ca_08_pagar_pendente_recusado | CA-08, RN-07 | padrão | pagar despesa nova | 409 `TRANSICAO_INVALIDA`; segue PENDENTE |
| test_ca_09_aprovar_e_pagar_fica_paga | CA-09, RN-07 | padrão | aprovar, pagar | 200 APROVADA, 200 PAGA; listagem mostra PAGA |
| test_ca_10_resumo_ignora_recusada_e_pendente | CA-10, RN-10 | padrão | mês 2029-12 com uma de cada situação em categorias distintas | totais só de APROVADA e PAGA (delta sobre o resumo antes do teste) |
| test_rn_01_valor_zero_recusado | RN-01 | padrão | 0 | 422 `VALOR_INVALIDO` |
| test_rn_01_valor_um_centavo_aceito | RN-01 | padrão | 1 | 201 |
| test_rn_01_valor_negativo_recusado | RN-01 | padrão | −1 | 422 (formato) |
| test_rn_02_limite_por_categoria (parametrizado nas 4 categorias) | RN-02 | padrão | limite − 1, limite, limite + 1 | 201, 201, 422 `VALOR_ACIMA_DO_LIMITE` |
| test_rn_03_data_de_hoje_aceita | RN-03 | padrão | 2030-01-07 | 201 |
| test_rn_03_virada_do_dia_libera_data | RN-03 | padrão, depois `avancar(days=1)` | 2030-01-08 | 422 antes, 201 depois |
| test_rn_04_borda_60_dias | RN-04 | padrão | 2029-11-09 (59), 2029-11-08 (60), 2029-11-07 (61) | 201, 201, 422 `DATA_MUITO_ANTIGA` |
| test_rn_05_mesmo_comprovante_outro_colaborador_aceito | RN-05 | padrão | outro e-mail | 201 |
| test_rn_05_email_com_maiusculas_conta_como_mesmo_colaborador | RN-05, PR-03 | padrão | e-mail em maiúsculas | 409 `COMPROVANTE_DUPLICADO` |
| test_rn_05_recusada_continua_bloqueando_e_excluida_libera | RN-05, PR-04 | padrão | recusar e relançar; excluir e relançar | 409; 201 |
| test_rn_07_transicoes_invalidas (parametrizado) | RN-07 | padrão | aprovar/recusar/pagar a partir de APROVADA, RECUSADA, PAGA fora da tabela | 409 `TRANSICAO_INVALIDA` |
| test_rn_08_motivo_so_espacos_recusado | RN-08 | padrão | `{"motivo": "   "}` | 422 `MOTIVO_OBRIGATORIO` |
| test_rn_08_recusar_com_motivo | RN-08, RF-03 | padrão | `{"motivo": " Sem nota "}` | 200 RECUSADA, `motivo_recusa="Sem nota"` |
| test_rn_09_excluir_pendente | RN-09, RF-05 | padrão | DELETE em PENDENTE | 204; some da listagem |
| test_rn_09_excluir_nao_pendente_recusado (parametrizado APROVADA, RECUSADA, PAGA) | RN-09 | padrão | DELETE | 409 `EXCLUSAO_NAO_PERMITIDA` |
| test_rn_10_resumo_bordas_do_mes | RN-10, PR-08 | padrão | APROVADA em 2029-12-01, 2029-12-31, 2029-11-30 | dezembro soma as duas primeiras; novembro recebe a terceira |
| test_rf_06_filtros_por_email_e_situacao | RF-06, PR-07 | padrão | despesas de dois colaboradores | filtros isolados e combinados; ordem por data desc |
| test_rf_08_carga_inicial_cinco_despesas_quatro_situacoes | RF-08 | padrão | banco novo | 5 despesas; situações = {PENDENTE, APROVADA, RECUSADA, PAGA}; datas dentro de 60 dias |
| test_despesa_inexistente_404 | — | padrão | aprovar/recusar/pagar/excluir id 999999 | 404 `DESPESA_NAO_ENCONTRADA` |
| test_mes_invalido_422 | RF-07 | padrão | `2030-13`, `1999-01`, ausente | 422 |
