# SPEC · Reembolso de despesas

Stack: a padrão da fábrica (Python 3.11, FastAPI, SQLite `sqlite3`, pytest, `index.html` com `fetch`).

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS despesas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  colaborador_nome TEXT NOT NULL CHECK (length(colaborador_nome) BETWEEN 1 AND 200),
  colaborador_email TEXT NOT NULL CHECK (length(colaborador_email) BETWEEN 3 AND 200),
  data_despesa TEXT NOT NULL,              -- data sem hora, 'YYYY-MM-DD' (PR-02)
  categoria TEXT NOT NULL CHECK (categoria IN ('TRANSPORTE','HOSPEDAGEM','ALIMENTACAO','OUTROS')),
  valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
  descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 200),
  numero_comprovante TEXT NOT NULL CHECK (length(numero_comprovante) BETWEEN 1 AND 200),
  situacao TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (situacao IN ('PENDENTE','APROVADA','RECUSADA','PAGA')),
  motivo_recusa TEXT,
  criada_em TEXT NOT NULL,                 -- UTC
  atualizada_em TEXT NOT NULL,             -- UTC
  UNIQUE (colaborador_email, numero_comprovante)
);
```

- `colaborador_email` é gravado em minúsculas e sem espaços nas pontas (PR-03). `numero_comprovante` é gravado sem espaços nas pontas.
- Valor em centavos inteiros: sem erro de ponto flutuante nas somas (PR-07).
- `data_despesa` é uma data civil, não um instante; por isso não vai para UTC. `criada_em` e `atualizada_em` são instantes e vão em UTC com `relogio.para_banco`.

## Carga inicial

Executada por `banco.carga_inicial` só quando `despesas` está vazia. `hoje` é a data de `relogio.agora()` no momento em que a aplicação inicia (PR-11), o que respeita `APP_AGORA`.

| colaborador_nome | colaborador_email | data_despesa | categoria | valor | descricao | numero_comprovante | situacao | motivo_recusa |
|---|---|---|---|---|---|---|---|---|
| Ana Ficticia | ana.ficticia@empresa.example | hoje − 2 | ALIMENTACAO | 45,90 | Almoço com cliente | NF-1001 | PENDENTE | |
| Bruno Exemplo | bruno.exemplo@empresa.example | hoje − 5 | TRANSPORTE | 230,00 | Passagem de ônibus | NF-2001 | PENDENTE | |
| Ana Ficticia | ana.ficticia@empresa.example | hoje − 10 | HOSPEDAGEM | 380,00 | Hotel, uma diária | NF-1002 | APROVADA | |
| Carla Modelo | carla.modelo@empresa.example | hoje − 12 | OUTROS | 75,50 | Material de apresentação | NF-3001 | RECUSADA | Despesa sem relação com a viagem |
| Bruno Exemplo | bruno.exemplo@empresa.example | hoje − 20 | ALIMENTACAO | 98,00 | Jantar | NF-2002 | PAGA | |

## Formatos

- `data_despesa`: data ISO 8601 `YYYY-MM-DD` (só dia, PR-02). Datas com hora são recusadas com 422 do framework.
- `valor`: número em reais com até 2 casas decimais (ex.: `120.01`). Mais casas ou texto não numérico → 422 do framework. Na saída, `valor` é número com 2 casas.
- `criada_em`, `atualizada_em` na saída: ISO 8601 com offset de America/Sao_Paulo.
- `mes`: `YYYY-MM`, ano entre 1900 e 2999 (fora disso, 422).
- `{id}` nos caminhos: inteiro de 1 a 2^63−1 (fora disso, 422).
- E-mail: expressão regular `^[^@\s]+@[^@\s]+\.[^@\s]+$`, até 200 caracteres.
- Textos (`colaborador_nome`, `descricao`, `numero_comprovante`): obrigatórios, 1 a 200 caracteres, e não podem ser só espaços. `motivo`: até 500 caracteres.

### Corpo de uma despesa (saída)

```json
{"id": 6, "colaborador_nome": "Diego Teste", "colaborador_email": "diego.teste@empresa.example",
 "data_despesa": "2030-01-05", "categoria": "TRANSPORTE", "valor": 150.0, "descricao": "Táxi",
 "numero_comprovante": "NF-9001", "situacao": "PENDENTE", "motivo_recusa": null,
 "criada_em": "2030-01-07T09:00:00-03:00", "atualizada_em": "2030-01-07T09:00:00-03:00"}
```

## Endpoints

Erros de negócio: `{"erro": "<CODIGO>", "mensagem": "<texto>"}`. Validação de formato: 422 padrão do framework.

### POST /api/despesas · RF-01
- **Entrada (JSON):** `colaborador_nome` (texto, obrigatório), `colaborador_email` (e-mail, obrigatório), `data_despesa` (data, obrigatória), `categoria` (enum, obrigatória), `valor` (decimal, até 2 casas, obrigatório), `descricao` (texto, obrigatório), `numero_comprovante` (texto, obrigatório).
- **Sucesso:** 201, corpo da despesa com `situacao: "PENDENTE"` (RN-06).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | VALOR_INVALIDO | RN-01 |
  | 422 | LIMITE_EXCEDIDO | RN-02 |
  | 422 | DATA_FUTURA | RN-03 |
  | 422 | DATA_ANTIGA | RN-04 |
  | 409 | COMPROVANTE_DUPLICADO | RN-05 |
  | 422 | (framework) | formato inválido |

### GET /api/despesas · RF-06
- **Entrada (consulta):** `email` (opcional, comparado sem diferenciar maiúsculas), `situacao` (opcional, enum).
- **Sucesso:** 200, lista de despesas ordenada por `data_despesa` desc, `id` desc (PR-09).
- **Erros:** 422 (framework) para `situacao` fora do enum.

### GET /api/despesas/{id} · RF-06
- **Sucesso:** 200, corpo da despesa.
- **Erros:** 404 DESPESA_NAO_ENCONTRADA.

### POST /api/despesas/{id}/aprovar · RF-02
- **Entrada:** nenhuma.
- **Sucesso:** 200, despesa com `situacao: "APROVADA"`.
- **Erros:** 404 DESPESA_NAO_ENCONTRADA; 409 TRANSICAO_INVALIDA (RN-07).

### POST /api/despesas/{id}/recusar · RF-03
- **Entrada (JSON):** `motivo` (texto, até 500; o corpo pode vir vazio `{}`).
- **Sucesso:** 200, despesa com `situacao: "RECUSADA"` e `motivo_recusa`.
- **Erros:** 422 MOTIVO_OBRIGATORIO (RN-08), 404 DESPESA_NAO_ENCONTRADA, 409 TRANSICAO_INVALIDA (RN-07).

### POST /api/despesas/{id}/pagar · RF-04
- **Entrada:** nenhuma.
- **Sucesso:** 200, despesa com `situacao: "PAGA"`.
- **Erros:** 404 DESPESA_NAO_ENCONTRADA; 409 TRANSICAO_INVALIDA (RN-07).

### DELETE /api/despesas/{id} · RF-05
- **Sucesso:** 204 sem corpo.
- **Erros:** 404 DESPESA_NAO_ENCONTRADA; 409 EXCLUSAO_NAO_PERMITIDA (RN-09).

### GET /api/relatorios/mensal · RF-07
- **Entrada (consulta):** `mes` (obrigatório, `YYYY-MM`).
- **Sucesso:** 200
  ```json
  {"mes": "2030-01", "situacoes_consideradas": ["APROVADA", "PAGA"],
   "totais_por_categoria": {"TRANSPORTE": 150.0, "HOSPEDAGEM": 0.0, "ALIMENTACAO": 0.0, "OUTROS": 0.0},
   "total_geral": 150.0, "quantidade": 1}
  ```
- **Erros:** 422 (framework) para `mes` ausente ou fora do formato.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `despesas.validar_valor` | 422 VALOR_INVALIDO |
| RN-02 | `despesas.validar_limite` | 422 LIMITE_EXCEDIDO |
| RN-03 | `despesas.validar_data` (recebe `agora`) | 422 DATA_FUTURA |
| RN-04 | `despesas.validar_data` (recebe `agora`) | 422 DATA_ANTIGA |
| RN-05 | `despesas.validar_comprovante_unico` (recebe se já existe) | 409 COMPROVANTE_DUPLICADO |
| RN-06 | `despesas.SITUACAO_INICIAL` usada na criação | — |
| RN-07 | `despesas.validar_transicao` | 409 TRANSICAO_INVALIDA |
| RN-08 | `despesas.validar_motivo` | 422 MOTIVO_OBRIGATORIO |
| RN-09 | `despesas.validar_exclusao` | 409 EXCLUSAO_NAO_PERMITIDA |
| RN-10 | `despesas.resumir_mes` e `despesas.intervalo_do_mes` | — |

Limites de RN-02 em centavos: `ALIMENTACAO` 12000, `HOSPEDAGEM` 45000, `TRANSPORTE` 100000, `OUTROS` 100000, comparação `valor <= limite`.
RN-03/RN-04: `hoje = agora.date()` no fuso America/Sao_Paulo; aceito se `hoje − 60 dias <= data <= hoje`.

## Tela
- Página única em `/`, com quatro áreas:
  1. **Lançar despesa:** formulário com todos os campos de `POST /api/despesas`; mostra sucesso ou a mensagem de erro da API.
  2. **Despesas:** filtros por e-mail e situação (`GET /api/despesas`); tabela com data, colaborador, categoria, valor, descrição, comprovante, situação e motivo; por linha, botões conforme a situação: Aprovar e Recusar (PENDENTE, recusa pede o motivo num campo da linha), Pagar (APROVADA), Excluir (PENDENTE). Chamam os endpoints de ação e `DELETE`.
  3. **Resumo do mês:** campo de mês (`<input type="month">`) e tabela com totais por categoria e total geral (`GET /api/relatorios/mensal`).
  4. Área de mensagem que mostra o texto de erro da API em vermelho.
- Dados da API sempre exibidos com `textContent`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/despesas`, tela área 1 |
| RF-02 | `POST /api/despesas/{id}/aprovar`, tela área 2 |
| RF-03 | `POST /api/despesas/{id}/recusar`, tela área 2 |
| RF-04 | `POST /api/despesas/{id}/pagar`, tela área 2 |
| RF-05 | `DELETE /api/despesas/{id}`, tela área 2 |
| RF-06 | `GET /api/despesas`, `GET /api/despesas/{id}`, tela área 2 |
| RF-07 | `GET /api/relatorios/mensal`, tela área 3 |
| RF-08 | todos os endpoints acima |
| RF-09 | `app/estatico/index.html` em `/` |
| RF-10 | SQLite em `dados/app.db`, sem autenticação |
| RF-11 | `banco.carga_inicial` |

## Plano de testes

Relógio de teste: `2030-01-07 09:00 -03:00` (hoje = 2030-01-07). Despesa base válida: Diego Teste, `diego.teste@empresa.example`, `2030-01-05`, TRANSPORTE, 150.00, "Táxi", NF-9001.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_lancar_despesa_valida_pendente | CA-01, RF-01, RN-06 | 2030-01-07 09:00 | despesa base | 201, `situacao` PENDENTE, `id` presente |
| test_ca_02_alimentacao_acima_do_limite_recusada | CA-02, RN-02 | idem | ALIMENTACAO 120.01 | 422 `erro` LIMITE_EXCEDIDO |
| test_ca_03_hospedagem_no_limite_criada | CA-03, RN-02 | idem | HOSPEDAGEM 450.00 | 201, `valor` 450.0, PENDENTE |
| test_ca_04_data_61_dias_atras_recusada | CA-04, RN-04 | idem | data 2029-11-07 | 422 DATA_ANTIGA |
| test_ca_05_data_de_amanha_recusada | CA-05, RN-03 | idem | data 2030-01-08 | 422 DATA_FUTURA |
| test_ca_06_comprovante_duplicado_mesmo_colaborador | CA-06, RN-05 | idem | despesa base duas vezes (2ª com e-mail em maiúsculas) | 1ª 201; 2ª 409 COMPROVANTE_DUPLICADO |
| test_ca_07_recusar_sem_motivo | CA-07, RN-08 | idem | recusar com `{}`, com `motivo: "   "` | 422 MOTIVO_OBRIGATORIO; despesa segue PENDENTE |
| test_ca_08_pagar_despesa_pendente_recusada | CA-08, RN-07 | idem | pagar despesa PENDENTE | 409 TRANSICAO_INVALIDA; segue PENDENTE |
| test_ca_09_aprovar_e_pagar | CA-09, RN-07 | idem | aprovar, depois pagar | 200 APROVADA; 200 PAGA |
| test_ca_10_resumo_ignora_recusada_e_pendente | CA-10, RN-10 | idem | 4 despesas jan/2030: PAGA 100, APROVADA 50, RECUSADA 70, PENDENTE 30 | `total_geral` 150.0; categorias corretas |
| test_rn_01_valor_zero_e_negativo_recusados | RN-01 | idem | valor 0, -1, 0.01 | 422 VALOR_INVALIDO; 422 VALOR_INVALIDO; 201 |
| test_rn_01_valor_com_tres_casas_recusado | RN-01 | idem | valor 10.001 | 422 (framework) |
| test_rn_02_limites_por_categoria_bordas | RN-02 | idem | por categoria: limite − 0,01, limite, limite + 0,01 | 201, 201, 422 LIMITE_EXCEDIDO |
| test_rn_03_data_hoje_aceita_amanha_recusada | RN-03 | idem | 2030-01-07, 2030-01-08 | 201; 422 DATA_FUTURA |
| test_rn_03_hoje_respeita_fuso_sao_paulo | RN-03 | 2030-01-07 23:30 -03:00 | 2030-01-08 | 422 DATA_FUTURA (em UTC já seria dia 8) |
| test_rn_04_data_60_dias_aceita_61_recusada | RN-04 | idem | 2029-11-09 (59), 2029-11-08 (60), 2029-11-07 (61) | 201, 201, 422 DATA_ANTIGA |
| test_rn_04_data_passa_a_ser_antiga_com_o_tempo | RN-04 | avança 1 dia | 2029-11-08 após avançar | 422 DATA_ANTIGA |
| test_rn_05_mesmo_comprovante_outro_colaborador_aceito | RN-05 | idem | NF-9001 com outro e-mail | 201 |
| test_rn_07_transicoes_invalidas | RN-07 | idem | aprovar APROVADA, recusar PAGA, aprovar RECUSADA, pagar RECUSADA | 409 TRANSICAO_INVALIDA |
| test_rn_08_recusar_com_motivo | RN-08, RF-03 | idem | motivo "Fora da política" | 200 RECUSADA, `motivo_recusa` |
| test_rn_09_excluir_pendente_e_nao_pendente | RN-09, RF-05 | idem | excluir PENDENTE; excluir APROVADA | 204 e GET 404; 409 EXCLUSAO_NAO_PERMITIDA |
| test_rf_06_filtros_por_email_e_situacao | RF-06 | idem | lista por e-mail, por situação, ambos | só as despesas que batem, ordem PR-09 |
| test_rf_06_despesa_inexistente_404 | RF-06 | idem | GET/aprovar/excluir id 9999 | 404 DESPESA_NAO_ENCONTRADA |
| test_rf_07_resumo_considera_mes_pela_data_da_despesa | RF-07, PR-08 | idem | APROVADA 2029-12-31 e 2030-01-01 | mês 2030-01 só a de 01/01 |
| test_rf_11_carga_inicial_cinco_despesas | RF-11 | real | banco novo | 5 despesas; situações PENDENTE×2, APROVADA, RECUSADA, PAGA; reinício não duplica |
| test_revisao_entradas_fora_da_faixa_retornam_4xx | formatos (revisão R-01, R-02) | idem | id 2^63+, id 0, mês 0000-01 e 9999-12, data 2030-02-30 | 422 |
| test_validacao_formato_422 | formatos | idem | campo faltando, categoria inválida, e-mail inválido, data com hora, `mes` inválido | 422 |
