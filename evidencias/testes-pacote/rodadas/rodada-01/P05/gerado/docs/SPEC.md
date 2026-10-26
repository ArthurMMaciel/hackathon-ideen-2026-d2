# SPEC · Chamados de suporte com prazo

Stack: a de `skills/fabrica/referencias/stack-padrao.md` (FastAPI + SQLite + pytest). Datas e horas na API em ISO 8601 com offset `-03:00` (fuso America/Sao_Paulo, PR-01); no banco em UTC (`relogio.para_banco`). Datas do relatório em `YYYY-MM-DD`.

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS chamados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
  descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 2000),
  solicitante_nome TEXT NOT NULL CHECK (length(solicitante_nome) BETWEEN 1 AND 100),
  solicitante_email TEXT NOT NULL CHECK (length(solicitante_email) BETWEEN 3 AND 200),
  categoria TEXT NOT NULL CHECK (categoria IN ('ACESSO','HARDWARE','SOFTWARE')),
  prioridade TEXT NOT NULL CHECK (prioridade IN ('BAIXA','MEDIA','ALTA','CRITICA')),
  situacao TEXT NOT NULL CHECK (situacao IN ('ABERTO','EM_ATENDIMENTO','RESOLVIDO','FECHADO')),
  aberto_em TEXT NOT NULL,
  prazo TEXT NOT NULL,
  responsavel TEXT,
  solucao TEXT,
  resolvido_em TEXT
);
```

Índice: `CREATE INDEX IF NOT EXISTS ix_chamados_situacao_prazo ON chamados (situacao, prazo);`

## Carga inicial

Inserida só com a tabela vazia. `T` = `relogio.agora()` no momento da carga (PR-09). Prazo calculado por RN-01. Pessoas e e-mails fictícios (`example.com`).

| # | titulo | categoria | prioridade | situacao | aberto_em | responsavel | resolvido_em | solicitante |
|---|---|---|---|---|---|---|---|---|
| 1 | Sem acesso à pasta compartilhada do financeiro | ACESSO | ALTA | ABERTO | T-2h | — | — | Ana Exemplo, ana.exemplo@example.com |
| 2 | Impressora do 2º andar não imprime | HARDWARE | BAIXA | ABERTO | T-80h (já atrasado) | — | — | Bruno Ficticio, bruno.ficticio@example.com |
| 3 | Erro ao abrir o sistema de folha | SOFTWARE | CRITICA | EM_ATENDIMENTO | T-1h | Carla Suporte | — | Diego Modelo, diego.modelo@example.com |
| 4 | Instalar leitor de PDF | SOFTWARE | MEDIA | RESOLVIDO | T-3d | Carla Suporte | T-3d+10h (dentro) | Elisa Teste, elisa.teste@example.com |
| 5 | Senha do e-mail bloqueada | ACESSO | CRITICA | RESOLVIDO | T-2d | Fabio Suporte | T-2d+5h (fora) | Gabriel Amostra, gabriel.amostra@example.com |
| 6 | Trocar mouse com defeito | HARDWARE | ALTA | FECHADO | T-5d | Fabio Suporte | T-5d+6h (dentro) | Helena Demo, helena.demo@example.com |

Chamados 4 a 6 têm `solucao` preenchida com texto fictício.

## Representação do chamado (saída)

```json
{"id": 7, "titulo": "Sem VPN", "descricao": "Não conecta", "solicitante_nome": "Ana Exemplo",
 "solicitante_email": "ana@example.com", "categoria": "ACESSO", "prioridade": "ALTA",
 "situacao": "ABERTO", "aberto_em": "2030-01-07T09:00:00-03:00", "prazo": "2030-01-07T17:00:00-03:00",
 "responsavel": null, "solucao": null, "resolvido_em": null, "dentro_do_prazo": null}
```

`dentro_do_prazo`: `true`/`false` quando há `resolvido_em` (RN-03), senão `null`.

## Endpoints

Erro 404 comum a todo endpoint com `{id}`: `404 CHAMADO_NAO_ENCONTRADO`. Erros de formato (campo faltando, tipo errado, enum inválido, e-mail inválido, texto vazio ou acima do limite): `422` padrão do framework (RN-09).

### POST /api/chamados · RF-01, RF-09
- **Entrada:** `titulo` str 1..200; `descricao` str 1..2000; `solicitante_nome` str 1..100; `solicitante_email` str 3..200, regex `^[^@\s]+@[^@\s]+\.[^@\s]+$`; `categoria` enum; `prioridade` enum. Todos obrigatórios; textos só com espaços são recusados.
- **Sucesso:** 201, chamado com `situacao` `ABERTO`, `aberto_em` = agora, `prazo` = RN-01.
- **Erros:** 422 (formato, RN-09).

### GET /api/chamados · RF-02
- **Entrada:** nenhuma.
- **Sucesso:** 200, lista de chamados ordenada por `id`.
- **Erros:** nenhum.

### GET /api/chamados/fila · RF-07
- **Entrada:** nenhuma.
- **Sucesso:** 200, lista dos chamados `ABERTO` e `EM_ATENDIMENTO`, ordenada por `prazo`, depois `aberto_em`, depois `id` (PR-03). Cada item é o chamado mais `"indicacao": "ATRASADO"` quando agora > prazo, senão `"indicacao": null` (RN-08).
- **Erros:** nenhum.

### GET /api/chamados/{id} · RF-02
- **Entrada:** `id` inteiro no caminho.
- **Sucesso:** 200, chamado.
- **Erros:** 404 CHAMADO_NAO_ENCONTRADO.

### POST /api/chamados/{id}/assumir · RF-03
- **Entrada:** `{"responsavel": str ≤100}`; campo opcional no formato, validado pela regra.
- **Sucesso:** 200, chamado `EM_ATENDIMENTO` com `responsavel`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | TRANSICAO_INVALIDA | RN-07 |
  | 422 | RESPONSAVEL_OBRIGATORIO | RN-04 |
  | 404 | CHAMADO_NAO_ENCONTRADO | — |

### POST /api/chamados/{id}/resolver · RF-04
- **Entrada:** `{"solucao": str ≤2000}`; campo opcional no formato, validado pela regra.
- **Sucesso:** 200, chamado `RESOLVIDO` com `solucao`, `resolvido_em` = agora e `dentro_do_prazo`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | TRANSICAO_INVALIDA | RN-07 |
  | 422 | SOLUCAO_OBRIGATORIA | RN-05 |
  | 404 | CHAMADO_NAO_ENCONTRADO | — |

A situação é conferida antes da solução: resolver um `ABERTO` sem solução dá `TRANSICAO_INVALIDA`.

### POST /api/chamados/{id}/fechar · RF-05
- **Entrada:** nenhuma.
- **Sucesso:** 200, chamado `FECHADO` (mantém solução e `resolvido_em`).
- **Erros:** 422 TRANSICAO_INVALIDA (RN-07); 404 CHAMADO_NAO_ENCONTRADO.

### POST /api/chamados/{id}/reabrir · RF-06
- **Entrada:** nenhuma.
- **Sucesso:** 200, chamado `EM_ATENDIMENTO`, `prazo` inalterado (RN-02), `solucao` e `resolvido_em` nulos, `responsavel` mantido (PR-06).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | TRANSICAO_INVALIDA | RN-07 |
  | 422 | REABERTURA_EXPIRADA | RN-06 |
  | 404 | CHAMADO_NAO_ENCONTRADO | — |

### GET /api/relatorios/prazo · RF-08
- **Entrada:** query `data_inicial` e `data_final`, datas `YYYY-MM-DD`, obrigatórias.
- **Sucesso:** 200
  ```json
  {"data_inicial": "2030-01-07", "data_final": "2030-01-07",
   "prioridades": [{"prioridade": "CRITICA", "resolvidos": 1, "dentro_do_prazo": 0, "percentual_dentro_do_prazo": 0.0},
                   {"prioridade": "ALTA", "resolvidos": 0, "dentro_do_prazo": 0, "percentual_dentro_do_prazo": null}, "..."]}
  ```
  Ordem fixa: CRITICA, ALTA, MEDIA, BAIXA. Conta chamados `RESOLVIDO` ou `FECHADO` com `resolvido_em` em `[data_inicial 00:00 local, (data_final + 1 dia) 00:00 local)` (RN-10, PR-04). Percentual = dentro/resolvidos × 100, arredondado a 1 casa (PR-05).
- **Erros:** 422 PERIODO_INVALIDO quando `data_final < data_inicial` (RN-10); 422 framework para data ausente ou mal formada.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `chamados.calcular_prazo(prioridade, aberto_em)` | — |
| RN-02 | `chamados.calcular_prazo` só é chamada na abertura; `reabrir` não altera `prazo` | — |
| RN-03 | `chamados.dentro_do_prazo(resolvido_em, prazo)` | — |
| RN-04 | `chamados.exigir_responsavel(texto)` | 422 RESPONSAVEL_OBRIGATORIO |
| RN-05 | `chamados.exigir_solucao(texto)` | 422 SOLUCAO_OBRIGATORIA |
| RN-06 | `chamados.verificar_reabertura(resolvido_em, agora)` | 422 REABERTURA_EXPIRADA |
| RN-07 | `chamados.validar_transicao(atual, acao)` (origem conferida por ação) | 422 TRANSICAO_INVALIDA |
| RN-08 | `chamados.indicacao_fila(prazo, agora)` | — |
| RN-09 | modelos Pydantic em `app/rotas/chamados.py` | 422 framework |
| RN-10 | `relatorio.periodo(data_inicial, data_final)` e `relatorio.montar(linhas)` | 422 PERIODO_INVALIDO |

## Tela
- Página única em `/`: formulário "Abrir chamado" (título, descrição, nome, e-mail, categoria, prioridade) → `POST /api/chamados`.
- Tabela "Fila" (`GET /api/chamados/fila`): id, título, prioridade, situação, prazo, responsável, indicação `ATRASADO` destacada; botões por linha: "Assumir" (pede responsável) → `/assumir`, "Resolver" (pede solução) → `/resolver`.
- Tabela "Todos os chamados" (`GET /api/chamados`) com botões "Fechar" → `/fechar` e "Reabrir" → `/reabrir` para chamados `RESOLVIDO`.
- Relatório: duas datas e botão → `GET /api/relatorios/prazo`, tabela por prioridade.
- Mensagens de erro da API exibidas numa área `#mensagem`. Dados exibidos com `textContent`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/chamados`; tela formulário |
| RF-02 | `GET /api/chamados`, `GET /api/chamados/{id}` |
| RF-03 | `POST /api/chamados/{id}/assumir`; tela botão Assumir |
| RF-04 | `POST /api/chamados/{id}/resolver`; tela botão Resolver |
| RF-05 | `POST /api/chamados/{id}/fechar`; tela botão Fechar |
| RF-06 | `POST /api/chamados/{id}/reabrir`; tela botão Reabrir |
| RF-07 | `GET /api/chamados/fila`; tela tabela Fila |
| RF-08 | `GET /api/relatorios/prazo`; tela Relatório |
| RF-09 | todos os endpoints `/api` |
| RF-10 | `GET /` (`app/estatico/index.html`) |
| RF-11 | SQLite `dados/app.db`; nenhum endpoint de login |
| RF-12 | `banco.carga_inicial` |

## Plano de testes
Relógio de teste inicial: `2030-01-07T09:00-03:00` (`R0`). `relogio.avancar()` simula o tempo.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_abrir_alta_prazo_8h | CA-01 | R0 | POST chamado ALTA | 201, situacao ABERTO, prazo = 2030-01-07T17:00-03:00 |
| test_ca_02_assumir_sem_responsavel_recusa | CA-02 | R0 | assumir `{}` e `{"responsavel":"  "}` | 422 RESPONSAVEL_OBRIGATORIO; situação segue ABERTO |
| test_ca_03_resolver_aberto_recusa | CA-03 | R0 | resolver ABERTO com solução | 422 TRANSICAO_INVALIDA; situação ABERTO |
| test_ca_04_resolver_sem_solucao_recusa | CA-04 | R0 | assumir, resolver `{}` | 422 SOLUCAO_OBRIGATORIA; situação EM_ATENDIMENTO |
| test_ca_05_resolvido_no_prazo_conta_dentro | CA-05 | R0 → +2h | MEDIA assumido e resolvido | relatório 2030-01-07: MEDIA resolvidos 1, dentro 1, 100.0 |
| test_ca_06_critica_4h01_fora_do_prazo | CA-06 | R0 → +4h01 | CRITICA resolvido | dentro_do_prazo false; relatório CRITICA dentro 0, 0.0 |
| test_ca_07_fila_prazo_vencido_atrasado | CA-07 | R0 → +4h01 | CRITICA aberto | fila: item com indicacao ATRASADO |
| test_ca_08_reabrir_6_dias | CA-08 | R0 → resolvido → +6d | reabrir | 200, EM_ATENDIMENTO |
| test_ca_09_reabrir_8_dias_recusa | CA-09 | R0 → resolvido → +8d | reabrir | 422 REABERTURA_EXPIRADA; situação RESOLVIDO |
| test_ca_10_fechar_aberto_recusa | CA-10 | R0 | fechar ABERTO | 422 TRANSICAO_INVALIDA |
| test_rn_01_prazo_por_prioridade | RN-01 | R0 | uma abertura por prioridade | prazo = R0 + 4h/8h/24h/72h |
| test_rn_02_prazo_nao_muda_ao_reabrir | RN-02 | R0 → +1h → +1d | resolver e reabrir | prazo igual ao original |
| test_rn_03_borda_prazo | RN-03 | R0 + 3h59 / 4h00 / 4h01 | CRITICA resolvido | true / true / false |
| test_rn_05_resolver_registra_data | RN-05 | R0 → +30min | resolver | resolvido_em = R0+30min, solução gravada |
| test_rn_06_borda_reabertura | RN-06 | resolvido + 6d23h59 / 7d / 7d+1min | reabrir | 200 / 200 / 422 REABERTURA_EXPIRADA |
| test_rn_07_transicoes_invalidas | RN-07 | R0 | assumir EM_ATENDIMENTO, fechar EM_ATENDIMENTO, reabrir ABERTO, assumir FECHADO, resolver FECHADO, reabrir FECHADO, assumir RESOLVIDO | 422 TRANSICAO_INVALIDA |
| test_rn_07_fechar_resolvido | RN-07, RF-05 | R0 | resolver e fechar | 200, FECHADO |
| test_rn_08_borda_atrasado | RN-08 | R0 + 3h59 / 4h00 / 4h01 | CRITICA aberto | null / null / ATRASADO |
| test_rn_08_fila_ordenada_pelo_prazo | RN-08, PR-03 | R0 | BAIXA, CRITICA, ALTA; um resolvido | ordem por prazo; resolvido fora da fila |
| test_rn_09_validacao_campos | RN-09 | R0 | e-mail inválido, prioridade inválida, título vazio, título com espaços | 422 |
| test_rn_09_limite_titulo | RN-09, PR-10 | R0 | título com 199, 200 e 201 caracteres | 201 / 201 / 422 |
| test_rn_10_periodo_invalido | RN-10 | R0 | final < inicial | 422 PERIODO_INVALIDO |
| test_rn_10_bordas_periodo | RN-10 | resoluções 00:00 do dia inicial, 23:59 do dia final, 00:00 do dia seguinte | relatório | conta 2, não conta o terceiro |
| test_rf_02_consultar_e_404 | RF-02 | R0 | GET por id existente e 999 | 200 / 404 CHAMADO_NAO_ENCONTRADO |
| test_rf_12_carga_inicial | RF-12 | — | GET /api/chamados | 6 chamados: 2 ABERTO, 1 EM_ATENDIMENTO, 2 RESOLVIDO, 1 FECHADO |
