# Revisão de qualidade

Revisão contra `gerado/docs/PRD.md` e `gerado/docs/SPEC.md`, abrindo os arquivos.

- **Testes antes da revisão:** `67 passed, 1 warning in 9.64s`
- **Testes depois das correções:** `68 passed, 1 warning in 9.94s`

## Achados

| # | Gravidade | Descrição | Arquivo | Regra | Status |
|---|---|---|---|---|---|
| 1 | Baixo | Percentual arredondado com `round()` de float (arredondamento bancário e erro binário: 6,25 → 6,2). PR-05 não dizia a regra de meio. Trocado por `Decimal` com `ROUND_HALF_UP`; PR-05 e plano de testes atualizados; teste `test_pr_05_percentual_arredonda_meio_para_cima`. | `app/dominio/relatorio.py:22` | PR-05 | CORRIGIDO |
| 2 | Baixo | Dicionário `_NOMES_ACAO` mapeava cada ação para ela mesma (código morto). Removido. | `app/dominio/chamados.py` | — | CORRIGIDO |
| 3 | Baixo | Campos extras no corpo de `POST /api/chamados` (ex.: `aberto_em`) são ignorados em silêncio, e não recusados. Comportamento previsto na SPEC (PR-02); a abertura sempre usa o relógio. | `app/rotas/chamados.py` | PR-02 | ACEITO (conforme SPEC) |
| 4 | Baixo | O `GET /api/saude` do modelo não estava na SPEC. Incluído na SPEC durante a construção. | `docs/SPEC.md` | — | CORRIGIDO (na etapa 3) |

Nenhum achado alto ou médio.

## Checklist

**Aderência**
- [x] Cada RF/RN conferido linha a linha na rastreabilidade da SPEC: RF-01 `abrir_chamado`; RF-02 `listar_chamados`/`consultar_chamado`; RF-03..RF-06 rotas de ação + `dominio.chamados.assumir/resolver/fechar/reabrir`; RF-07 `consultar_fila` (SQL `situacao IN ('ABERTO','EM_ATENDIMENTO') ORDER BY prazo_em, id`); RF-08 `emitir_relatorio`; RF-10 `index.html`; RF-11 SQLite sem autenticação; RF-12 `banco.carga_inicial`. RN-01..RN-09 nas funções da tabela da SPEC, cada uma com comentário `# RN-xx`.
- [x] Enums exatamente como no pedido: `ACESSO, HARDWARE, SOFTWARE`; `BAIXA, MEDIA, ALTA, CRITICA`; `ABERTO, EM_ATENDIMENTO, RESOLVIDO, FECHADO`; indicação `ATRASADO`.
- [x] Carga inicial: 6 chamados, 4 situações, 4 prioridades, 2 atrasados na fila (`test_rf_12_carga_inicial_seis_chamados`, `..._idempotente`).

**Testes**
- [x] Todo CA confere status e campo do corpo (`situacao`, `erro`, `prazo_em`, `dentro_do_prazo`, `indicacao`), e as recusas conferem também que a situação não mudou.
- [x] Bordas: RN-01 (4 prioridades), RN-03 (239/240/241 min), RN-06 (7d−1min/7d/7d+1min), RN-08 (239/240/241 min), RN-09 (último dia 23:59, meia-noite do dia seguinte, dia anterior, período invertido).
- [x] Testes de tempo usam `relogio` (fixture) ou `AGORA_INICIAL`; nenhum depende da hora real.

**Erros e valores extremos** (sonda em `gerado/.tmp/sondas.py`, saída em `gerado/.tmp/sondas.txt`; 0 respostas 5xx)

| Sonda | Resultado |
|---|---|
| id `99999999999999999999`, `-1`, `0`, `１２`, `abc` em `GET /api/chamados/{id}` e nas 4 ações | 422 em todos |
| `titulo`, `descricao`, `solicitante_nome`, `solicitante_email` só com espaços / 5000 caracteres / número negativo | 422 em todos |
| `prioridade=-1` | 422 |
| JSON inválido; corpo lista | 422 |
| `responsavel` com 5000 caracteres / número; corpo string | 422 |
| `solucao` com 5000 caracteres | 422 |
| relatório com ano 9999, ano 0001, dígitos `２０３０`, data com hora, vazio, sem parâmetros | 422 |
| relatório 2100-12-31..2100-12-31 e 2000-01-01..2100-12-31 | 200 |
| id inexistente `999999` | 404 `CHAMADO_NAO_ENCONTRADO` (teste `test_rf_02_consultar_e_listar`) |

- [x] Erros de negócio no formato `{"erro","mensagem"}` em português; 409 para transição inválida e reabertura fora da janela (estado), 422 para responsável, solução e período (requisição inválida em qualquer estado).

**Estrutura**
- [x] `app/dominio/` importa só `datetime`, `decimal` e `app.dominio.*` (sem `fastapi`, sem `sqlite3`).
- [x] SQL só em `app/repositorio/chamados.py`; `app/banco.py` só DDL, PRAGMA e controle de transação.
- [x] `datetime.now` só em `app/relogio.py`.
- [x] Abrir e as 4 ações gravam dentro de `banco.transacao` (`_mudar_situacao` confere e grava na mesma transação).
- [x] Carga inicial usa o `agora` recebido.

**Tela**
- [x] Ações da SPEC: abrir, fila com etiqueta ATRASADO, lista com Assumir/Resolver/Fechar/Reabrir, relatório. Erros via `mostrarMensagem(..., "erro")`.
- [x] Todos os `getElementById` (`atualizar`, `chamados`, `fila`, `form-abrir`, `form-relatorio`, `mensagem`, `relatorio`) existem no HTML.
- [x] Script extraído passa em `node --check` (Node v22.23.2).
- [x] Endpoints chamados pela tela respondem via HTTP com os parâmetros que ela envia: `GET /api/fila`, `GET /api/chamados`, `POST /api/chamados` (campos do formulário), ações com `{responsavel}`/`{solucao}`/`{}`, `GET /api/relatorio?data_inicial&data_final` (AAAA-MM-DD do `input type=date`) — cobertos pelos testes e pelo ensaio de `verificar_ca.py`.
