# SPEC · Chamados de suporte com prazo

Stack: a de `skills/fabrica/referencias/stack-padrao.md` (FastAPI, SQLite, pytest, tela única em `/`). Datas e horas na API em ISO 8601 com offset de America/Sao_Paulo (PR-01); no banco, texto UTC via `relogio.para_banco`.

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS chamados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
  descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 2000),
  solicitante_nome TEXT NOT NULL CHECK (length(solicitante_nome) BETWEEN 1 AND 200),
  solicitante_email TEXT NOT NULL CHECK (length(solicitante_email) BETWEEN 3 AND 254),
  categoria TEXT NOT NULL CHECK (categoria IN ('ACESSO', 'HARDWARE', 'SOFTWARE')),
  prioridade TEXT NOT NULL CHECK (prioridade IN ('BAIXA', 'MEDIA', 'ALTA', 'CRITICA')),
  situacao TEXT NOT NULL CHECK (situacao IN ('ABERTO', 'EM_ATENDIMENTO', 'RESOLVIDO', 'FECHADO')),
  aberto_em TEXT NOT NULL,
  prazo_em TEXT NOT NULL,
  responsavel TEXT CHECK (responsavel IS NULL OR length(responsavel) BETWEEN 1 AND 200),
  solucao TEXT CHECK (solucao IS NULL OR length(solucao) BETWEEN 1 AND 2000),
  resolvido_em TEXT
);
```

```sql
CREATE INDEX IF NOT EXISTS ix_chamados_situacao_prazo ON chamados (situacao, prazo_em);
```

```sql
CREATE INDEX IF NOT EXISTS ix_chamados_resolvido_em ON chamados (resolvido_em);
```

`prazo_em` é gravado na abertura e nenhuma operação o altera (RN-02).

## Carga inicial

RF-12, PR-10. Só insere com a tabela vazia. `A` = `agora` recebido por `carga_inicial`. Prazo sempre pela RN-01.

| # | titulo | categoria | prioridade | situacao | aberto_em | prazo_em | responsavel | resolvido_em | solicitante |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Sem acesso à pasta compartilhada do financeiro | ACESSO | CRITICA | ABERTO | A − 6h | A − 2h (ATRASADO) | — | — | Ana Souza, ana.souza@empresa.example |
| 2 | Notebook não liga após atualização | HARDWARE | ALTA | EM_ATENDIMENTO | A − 2h | A + 6h | Carla Mendes | — | Diego Ramos, diego.ramos@empresa.example |
| 3 | Instalar editor de planilhas | SOFTWARE | BAIXA | ABERTO | A − 1h | A + 71h | — | — | Elisa Prado, elisa.prado@empresa.example |
| 4 | Impressora do segundo andar travando papel | HARDWARE | MEDIA | EM_ATENDIMENTO | A − 30h | A − 6h (ATRASADO) | Bruno Lima | — | Fabio Nunes, fabio.nunes@empresa.example |
| 5 | Liberar acesso ao sistema de compras | ACESSO | ALTA | RESOLVIDO | A − 26h | A − 18h | Carla Mendes | A − 20h (no prazo) | Gabriela Reis, gabriela.reis@empresa.example |
| 6 | Erro ao abrir o sistema de ponto | SOFTWARE | MEDIA | FECHADO | A − 72h | A − 48h | Bruno Lima | A − 46h (fora do prazo) | Hugo Alves, hugo.alves@empresa.example |

Chamados 5 e 6 têm `solucao` preenchida com texto fictício. Descrições são frases curtas fictícias.

## Endpoints

Representação de chamado (`Chamado`), usada nas saídas:

```json
{"id": 7, "titulo": "Sem acesso à VPN", "descricao": "Erro de certificado", "solicitante_nome": "Ana Souza",
 "solicitante_email": "ana.souza@empresa.example", "categoria": "ACESSO", "prioridade": "ALTA",
 "situacao": "ABERTO", "aberto_em": "2030-01-07T09:00:00-03:00", "prazo_em": "2030-01-07T17:00:00-03:00",
 "responsavel": null, "solucao": null, "resolvido_em": null}
```

Erro comum a todos os endpoints com `{id}`: `404 CHAMADO_NAO_ENCONTRADO`. `id` é `Annotated[Id, Path()]` (fora de 1..2147483647 → 422 do framework).

### POST /api/chamados · RF-01
- **Entrada (corpo):** `titulo: Texto`, `descricao: TextoLongo`, `solicitante_nome: Texto`, `solicitante_email: Email`, `categoria: Literal["ACESSO","HARDWARE","SOFTWARE"]`, `prioridade: Literal["BAIXA","MEDIA","ALTA","CRITICA"]`. Todos obrigatórios. Campos extras ignorados; data de abertura não é aceita (PR-02).
- **Sucesso:** `201` `Chamado` com `situacao=ABERTO`, `aberto_em=agora`, `prazo_em=agora + horas(prioridade)` (RN-01).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | validação do framework | PR-08 |

### GET /api/chamados · RF-02
- **Entrada:** nenhuma.
- **Sucesso:** `200` lista de `Chamado`, por `id` decrescente (PR-09).
- **Erros:** nenhum de negócio.

### GET /api/chamados/{id} · RF-02
- **Entrada:** `id` no caminho.
- **Sucesso:** `200` `Chamado`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | CHAMADO_NAO_ENCONTRADO | RF-02 |

### POST /api/chamados/{id}/assumir · RF-03
- **Entrada (corpo opcional):** `responsavel: str | None` (sem espaços nas pontas, até 200 caracteres). Corpo ausente equivale a `{}`.
- **Sucesso:** `200` `Chamado` com `situacao=EM_ATENDIMENTO` e `responsavel`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | CHAMADO_NAO_ENCONTRADO | — |
  | 409 | TRANSICAO_INVALIDA | RN-07 (situação diferente de ABERTO) |
  | 422 | RESPONSAVEL_OBRIGATORIO | RN-04 (ausente, vazio ou só espaços) |

### POST /api/chamados/{id}/resolver · RF-04
- **Entrada (corpo opcional):** `solucao: str | None` (sem espaços nas pontas, até 2000 caracteres).
- **Sucesso:** `200` `Chamado` com `situacao=RESOLVIDO`, `solucao`, `resolvido_em=agora` (RN-05).
- **Erros:** (a transição é conferida antes da solução, PR-11)
  | Status | Código | Regra |
  |---|---|---|
  | 404 | CHAMADO_NAO_ENCONTRADO | — |
  | 409 | TRANSICAO_INVALIDA | RN-07 (situação diferente de EM_ATENDIMENTO) |
  | 422 | SOLUCAO_OBRIGATORIA | RN-05 |

### POST /api/chamados/{id}/fechar · RF-05
- **Entrada:** sem corpo.
- **Sucesso:** `200` `Chamado` com `situacao=FECHADO`.
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | CHAMADO_NAO_ENCONTRADO | — |
  | 409 | TRANSICAO_INVALIDA | RN-07 (situação diferente de RESOLVIDO) |

### POST /api/chamados/{id}/reabrir · RF-06
- **Entrada:** sem corpo.
- **Sucesso:** `200` `Chamado` com `situacao=EM_ATENDIMENTO`, mesmo `responsavel` e `prazo_em`, `solucao=null`, `resolvido_em=null` (RN-02, PR-06).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 404 | CHAMADO_NAO_ENCONTRADO | — |
  | 409 | TRANSICAO_INVALIDA | RN-07 (situação diferente de RESOLVIDO) |
  | 409 | PRAZO_REABERTURA_ENCERRADO | RN-06 (agora > resolvido_em + 7 dias) |

### GET /api/fila · RF-07
- **Entrada:** nenhuma.
- **Sucesso:** `200` lista de `Chamado` com o campo extra `indicacao` (`"ATRASADO"` se `agora > prazo_em`, senão `"NO_PRAZO"`), só `ABERTO` e `EM_ATENDIMENTO`, por `prazo_em` crescente e depois `id` (PR-03, RN-08).
- **Erros:** nenhum de negócio.

### GET /api/relatorio · RF-08
- **Entrada (consulta):** `data_inicial: Annotated[Data, Query()]`, `data_final: Annotated[Data, Query()]`, ambas obrigatórias (`AAAA-MM-DD`).
- **Sucesso:** `200`
  ```json
  {"data_inicial": "2030-01-07", "data_final": "2030-01-07", "prioridades": [
    {"prioridade": "CRITICA", "resolvidos": 1, "dentro_do_prazo": 0, "percentual_dentro_do_prazo": 0.0},
    {"prioridade": "ALTA", "resolvidos": 0, "dentro_do_prazo": 0, "percentual_dentro_do_prazo": null},
    {"prioridade": "MEDIA", "resolvidos": 1, "dentro_do_prazo": 1, "percentual_dentro_do_prazo": 100.0},
    {"prioridade": "BAIXA", "resolvidos": 0, "dentro_do_prazo": 0, "percentual_dentro_do_prazo": null}]}
  ```
  Conta chamados `RESOLVIDO` e `FECHADO` com `resolvido_em` em `[data_inicial 00:00, data_final + 1 dia 00:00)` no fuso America/Sao_Paulo (RN-09, PR-04). Dentro do prazo: `resolvido_em <= prazo_em` (RN-03). Percentual com 1 casa decimal (PR-05).
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 422 | PERIODO_INVALIDO | RN-09 (data_inicial > data_final) |
  | 422 | validação do framework | data ausente ou fora do formato |

### GET /api/saude · infraestrutura (vem do modelo de projeto)
- **Entrada:** nenhuma.
- **Sucesso:** `200` `{"status": "ok"}`. Usado pelo harness de verificação para saber que o servidor subiu.
- **Erros:** nenhum.

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `chamados.calcular_prazo(prioridade, aberto_em)` | — |
| RN-02 | `chamados.reabrir` não altera `prazo_em`; repositório não tem UPDATE de `prazo_em` | — |
| RN-03 | `chamados.dentro_do_prazo(resolvido_em, prazo_em)` e `relatorio.montar_relatorio` | — |
| RN-04 | `chamados.assumir(chamado, responsavel)` | 422 RESPONSAVEL_OBRIGATORIO |
| RN-05 | `chamados.resolver(chamado, solucao, agora)` | 422 SOLUCAO_OBRIGATORIA |
| RN-06 | `chamados.reabrir(chamado, agora)` | 409 PRAZO_REABERTURA_ENCERRADO |
| RN-07 | `chamados.exigir_situacao(chamado, esperada, acao)` usada por assumir/resolver/fechar/reabrir | 409 TRANSICAO_INVALIDA |
| RN-08 | `chamados.indicacao_fila(prazo_em, agora)` | — |
| RN-09 | `relatorio.validar_periodo(data_inicial, data_final)` e `relatorio.limites_periodo` | 422 PERIODO_INVALIDO |

Decisão de status (regras transversais, pergunta 409/422): reabrir após 7 dias seria aceito se a resolução guardada fosse mais recente, logo 409. Responsável e solução ausentes seriam recusados em qualquer estado, logo 422.

## Tela
Página única em `/`, título "Chamados de suporte":
- **Abrir chamado:** formulário (título, descrição, nome e e-mail do solicitante, categoria, prioridade) → `POST /api/chamados`; mostra o número e o prazo do chamado criado.
- **Fila:** tabela de `GET /api/fila` (número, título, prioridade, situação, responsável, prazo, indicação com etiqueta `ATRASADO`) e botão Atualizar.
- **Todos os chamados / mudar situação:** tabela de `GET /api/chamados` com botões por linha conforme a situação: Assumir (pede responsável num campo da linha) → `/assumir`; Resolver (pede solução) → `/resolver`; Fechar → `/fechar`; Reabrir → `/reabrir`. Depois de cada ação, recarrega fila e lista.
- **Relatório:** datas inicial e final → `GET /api/relatorio`; tabela por prioridade.
- Toda mensagem de erro da API aparece com `mostrarMensagem(..., "erro")`. Dados entram só por `textContent`/`desenharTabela`.

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/chamados`, tela "Abrir chamado" |
| RF-02 | `GET /api/chamados`, `GET /api/chamados/{id}`, tela "Todos os chamados" |
| RF-03 | `POST /api/chamados/{id}/assumir`, botão Assumir |
| RF-04 | `POST /api/chamados/{id}/resolver`, botão Resolver |
| RF-05 | `POST /api/chamados/{id}/fechar`, botão Fechar |
| RF-06 | `POST /api/chamados/{id}/reabrir`, botão Reabrir |
| RF-07 | `GET /api/fila`, tela "Fila" |
| RF-08 | `GET /api/relatorio`, tela "Relatório" |
| RF-09 | todos os endpoints `/api` acima |
| RF-10 | `GET /` (index.html) |
| RF-11 | SQLite em `gerado/dados/app.db`, sem autenticação |
| RF-12 | `banco.carga_inicial` (tabela "Carga inicial") |
| RN-01..RN-09 | tabela "Regras de negócio" |

## Plano de testes
Relógio inicial dos testes: 2030-01-07 09:00 −03:00 (`AGORA_INICIAL`). "Abrir X" = `POST /api/chamados` com prioridade X; "assumir" com `responsavel="Carla Mendes"`.

| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_abrir_alta_prazo_8h | CA-01 | 09:00 | abrir ALTA | 201, situacao ABERTO, aberto_em 09:00, prazo_em 17:00 −03:00 |
| test_ca_02_assumir_sem_responsavel_recusa | CA-02 | 09:00 | abrir; assumir com `{}` e sem corpo | 422 RESPONSAVEL_OBRIGATORIO; chamado continua ABERTO |
| test_ca_03_resolver_aberto_recusa | CA-03 | 09:00 | abrir; resolver com solução | 409 TRANSICAO_INVALIDA; continua ABERTO |
| test_ca_04_resolver_sem_solucao_recusa | CA-04 | 09:00 | abrir; assumir; resolver `{}` | 422 SOLUCAO_OBRIGATORIA; continua EM_ATENDIMENTO |
| test_ca_05_resolvido_no_prazo_conta_no_relatorio | CA-05 | 09:00 → +2h | abrir MEDIA; assumir; resolver; relatório 2030-01-07 a 2030-01-07 | MEDIA resolvidos 1, dentro_do_prazo 1, percentual 100.0 |
| test_ca_06_critica_4h01_fora_do_prazo | CA-06 | 09:00 → +4h01 | abrir CRITICA; assumir; resolver; relatório do dia | CRITICA resolvidos 1, dentro_do_prazo 0, percentual 0.0 |
| test_ca_07_fila_mostra_atrasado | CA-07 | 09:00 → +4h01 | abrir CRITICA; fila | item com indicacao ATRASADO |
| test_ca_08_reabrir_resolvido_ha_6_dias | CA-08 | resolve 09:00 +1h; +6 dias | abrir, assumir, resolver, reabrir | 200, situacao EM_ATENDIMENTO, prazo_em igual ao original |
| test_ca_09_reabrir_resolvido_ha_8_dias_recusa | CA-09 | resolve; +8 dias | reabrir | 409 PRAZO_REABERTURA_ENCERRADO; continua RESOLVIDO |
| test_ca_10_fechar_aberto_recusa | CA-10 | 09:00 | abrir; fechar | 409 TRANSICAO_INVALIDA; continua ABERTO |
| test_rn_01_prazo_por_prioridade[4 casos] | RN-01 | 09:00 | abrir CRITICA/ALTA/MEDIA/BAIXA | prazo_em = +4h/+8h/+24h/+72h |
| test_rn_02_prazo_nao_muda_ao_reabrir | RN-02 | resolve; +1 dia | reabrir; resolver de novo | prazo_em inalterado; resolvido_em novo |
| test_rn_03_resolver_no_limite_do_prazo_conta_dentro | RN-03 | +4h exatas | CRITICA resolvida no prazo exato | dentro_do_prazo 1 |
| test_rn_03_resolver_um_minuto_antes_do_prazo_conta_dentro | RN-03 | +3h59 | CRITICA | dentro_do_prazo 1 |
| test_rn_03_resolver_um_minuto_depois_do_prazo_conta_fora | RN-03 | +4h01 | CRITICA | dentro_do_prazo 0 |
| test_rn_04_responsavel_so_espacos_recusa | RN-04 | 09:00 | assumir `"   "` e `""` | 422 RESPONSAVEL_OBRIGATORIO |
| test_rn_04_assumir_registra_responsavel | RN-04 | 09:00 | assumir | 200 EM_ATENDIMENTO, responsavel |
| test_rn_05_resolver_registra_solucao_e_resolucao | RN-05 | +1h | resolver | 200 RESOLVIDO, solucao, resolvido_em 10:00 −03:00 |
| test_rn_05_solucao_so_espacos_recusa | RN-05 | 09:00 | resolver `"  "` | 422 SOLUCAO_OBRIGATORIA |
| test_rn_06_reabrir_exatamente_7_dias_aceito | RN-06 | resolve; +7 dias | reabrir | 200 EM_ATENDIMENTO |
| test_rn_06_reabrir_7_dias_menos_1_minuto_aceito | RN-06 | +7d −1min | reabrir | 200 |
| test_rn_06_reabrir_7_dias_mais_1_minuto_recusa | RN-06 | +7d +1min | reabrir | 409 PRAZO_REABERTURA_ENCERRADO |
| test_rn_07_transicoes_invalidas[10 casos] | RN-07 | 09:00 | assumir EM_ATENDIMENTO/RESOLVIDO/FECHADO; resolver RESOLVIDO/FECHADO; fechar EM_ATENDIMENTO/FECHADO; reabrir ABERTO/EM_ATENDIMENTO/FECHADO | 409 TRANSICAO_INVALIDA |
| test_rn_07_fechar_resolvido | RN-07 | 09:00 | abrir, assumir, resolver, fechar | 200 FECHADO |
| test_rn_08_fila_no_instante_do_prazo_nao_atrasado | RN-08 | +4h exatas | CRITICA; fila | indicacao NO_PRAZO |
| test_rn_08_fila_um_minuto_antes_nao_atrasado | RN-08 | +3h59 | fila | NO_PRAZO |
| test_rn_08_fila_um_minuto_depois_atrasado | RN-08 | +4h01 | fila | ATRASADO |
| test_rf_07_fila_ordem_e_filtro | RF-07, PR-03 | 09:00 | abrir BAIXA, CRITICA, MEDIA; resolver um outro | ordem por prazo; resolvido fora da fila |
| test_rn_09_periodo_invertido_recusa | RN-09 | 09:00 | data_inicial 2030-01-08, data_final 2030-01-07 | 422 PERIODO_INVALIDO |
| test_rn_09_periodo_conta_primeiro_e_ultimo_dia | RN-09, PR-04 | resolução 2030-01-07 23:59 −03:00 | relatórios [01-07,01-07], [01-06,01-06], [01-08,01-08] | 1, 0, 0 |
| test_rn_09_resolucao_meia_noite_conta_no_dia_seguinte | RN-09 | resolução 2030-01-08 00:00 −03:00 | relatório [01-07,01-07] e [01-08,01-08] | 0 e 1 |
| test_pr_05_percentual_arredondado_e_vazio | PR-05 | vários | 3 ALTA, 2 no prazo | ALTA 66.7; BAIXA null; ordem CRITICA, ALTA, MEDIA, BAIXA |
| test_pr_05_percentual_arredonda_meio_para_cima | PR-05 | — | 16 CRITICA, 1 no prazo (função de domínio) | 6.3 |
| test_pr_04_relatorio_conta_fechado_e_ignora_reaberto | PR-04, PR-06 | — | um fechado, um reaberto | fechado conta, reaberto não |
| test_rf_02_consultar_e_listar | RF-02 | 09:00 | abrir 2; GET lista e GET id | ordem id decrescente; 404 CHAMADO_NAO_ENCONTRADO para id inexistente |
| test_rf_12_carga_inicial_seis_chamados | RF-12, PR-10 | 09:00 | GET /api/chamados com banco novo | 6 chamados, 4 situações, 4 prioridades, ≥1 ATRASADO na fila |
| test_rf_12_carga_inicial_idempotente | RF-12 | — | iniciar duas vezes o mesmo banco | continua com 6 |
| test_rf_01_validacao_entrada | RF-01, PR-08 | — | e-mail inválido, prioridade fora do enum, título vazio | 422 |
