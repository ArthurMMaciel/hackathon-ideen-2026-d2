# Revisão de qualidade

Revisão de `gerado/` contra `gerado/docs/PRD.md` e `gerado/docs/SPEC.md`.

- **Testes antes da revisão:** `58 passed, 1 warning`
- **Testes depois da revisão:** `58 passed, 1 warning` (nenhuma correção alterou código)

## Checklist

**Aderência**
- [x] Rastreabilidade da SPEC conferida linha a linha: RF-01 `POST /api/colaboradores` (`rotas/colaboradores.cadastrar`); RF-02 `GET /api/colaboradores[/{id}]` com `saldo_disponivel` (SQL `_COLABORADOR_COLUNAS`); RF-03 `banco.carga_inicial` (9, 3 por equipe, saldo 30); RF-04 a RF-08 `rotas/solicitacoes.py`; RF-09 `rotas/calendario.py` + `ferias.montar_calendario`; RF-10 todos em `/api`; RF-11 `estatico/index.html`; RF-12 SQLite sem autenticação.
- [x] RN-01 a RN-10 em `app/dominio/ferias.py` com comentário `# RN-xx` e o erro da SPEC; RN-11 no modelo `ColaboradorEntrada` + `dominio/colaboradores.validar_email_livre`.
- [x] Enums exatamente como no pedido: `DADOS`, `PRODUTO`, `SUPORTE`; `SOLICITADA`, `APROVADA`, `REPROVADA`, `CANCELADA` (DDL `CHECK`, `Literal`, constantes do domínio).
- [x] Carga inicial cria exatamente 9 colaboradores, 3 por equipe (`test_rf_03_...`).

**Testes**
- [x] Todo `test_ca_XX` confere status e o campo do corpo (`situacao`, `dias`, `erro`, `saldo`, nomes do calendário).
- [x] Bordas: RN-02 4/5/30/31; RN-03 29/30/31; RN-04 disponível+1 / igual ao disponível; RN-07 um dia em comum / dia seguinte (CA-08); RN-09 véspera / dia do início / dia seguinte; RN-11 −1/0/365/366.
- [x] Regras de tempo usam a fixture `relogio` (`test_rn_09_bordas_do_cancelamento` usa `relogio.avancar`); nenhum teste lê a hora real.

**Erros e valores extremos** — sondagem com `gerado/.tmp/sonda.py` (TestClient, `raise_server_exceptions=False`), 43 requisições, **nenhum 5xx**:

| Sonda | Resultado |
|---|---|
| id `99999999999999999999`, `0`, `-1`, `abc`, `１２` em GET e nas ações aprovar/reprovar/cancelar | 422 |
| nome só com espaços, nome com 5000 caracteres, e-mail com 5000 caracteres, nome `null` | 422 |
| saldo `-5`, `１２`, `10^20`, `1.5`; equipe `dados` | 422 |
| corpo ausente, JSON inválido | 422 sem stack trace |
| `colaborador_id` gigante, negativo, `１２` | 422 |
| datas `9999-01-01`, `0001-01-01`, `9999-12-31`, com horário, `16/02/2030`, dígitos Unicode | 422 |
| período 2030-02-16 a 2100-12-31; início 2000-01-01 | 422 `DURACAO_INVALIDA` |
| calendário `9999-01`, `0001-01`, `１２`, `2030-02-01`, vazio, ausente | 422 |
| calendário `2100-12`, `2000-01` (limites da faixa) | 200 |
| ids inexistentes válidos (`999999`) | 404 `COLABORADOR_NAO_ENCONTRADO` / `SOLICITACAO_NAO_ENCONTRADA` (`test_rf_02_e_rf_05_inexistente_404`) |

- [x] Erros de negócio em `{"erro", "mensagem"}`, mensagem em português; 409 para estado (SOBREPOSICAO, SALDO_INSUFICIENTE, TRANSICAO_INVALIDA, LIMITE_EQUIPE, EMAIL_DUPLICADO), 422 para regra fixa ou prazo (PERIODO_INVALIDO, DURACAO_INVALIDA, ANTECEDENCIA_INSUFICIENTE, CANCELAMENTO_FORA_DO_PRAZO).

**Estrutura**
- [x] `app/dominio/` importa só `calendar`, `datetime` e `app.dominio.erros` (sem `fastapi`/`sqlite3`).
- [x] SQL só em `app/repositorio/ferias.py` e DDL/carga em `app/banco.py` (grep por `execute|SELECT|INSERT|UPDATE` fora deles: vazio).
- [x] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py`.
- [x] Escritas dependentes de leitura (cadastrar, solicitar, aprovar, reprovar, cancelar) dentro de `banco.transacao`.
- [x] Carga inicial não usa datas (não há datas relativas a calcular).

**Tela**
- [x] Ações da SPEC: solicitar (form), aprovar/reprovar/cancelar (botões por linha), calendário (form `month`), colaboradores e saldo (tabela). Erros da API exibidos com `mostrarMensagem(..., "erro")`.
- [x] Todo `getElementById` aponta para elemento existente: `mensagem`, `select-colaborador`, `lista-colaboradores`, `lista-solicitacoes`, `calendario`, `campo-mes`, `form-solicitar`, `form-calendario`. Sem `querySelector`.
- [x] `node --check` no script extraído: OK.
- [x] Endpoints chamados pela tela com os parâmetros que ela envia (`colaborador_id` numérico, datas `AAAA-MM-DD` de `input type=date`, `mes` `AAAA-MM` de `input type=month`) respondem: exercitados pelos testes e por `verificar_ca.py` com os mesmos formatos.

## Achados

| # | Gravidade | Descrição | Arquivo | Regra | Status |
|---|---|---|---|---|---|
| 1 | Baixo | Erros de validação de formato (422 do framework) vêm com `msg` em inglês e a tela os mostra como estão. As regras transversais mandam usar o 422 padrão do framework; na tela os campos são `required`/`type=date`/`select`, então o caso é raro. | `app/estatico/index.html` | Idioma | ACEITO: segue a regra transversal de formato de erro de validação |
| 2 | Baixo | A aprovação não reconfere o saldo. A invariante se mantém porque o saldo disponível já desconta os pendentes na solicitação (RN-04) e o `CHECK (saldo BETWEEN 0 AND 365)` impede valor negativo. | `app/rotas/solicitacoes.py` | RN-04, RN-08 | ACEITO: invariante garantida por RN-04 e pelo DDL |
| 3 | Baixo | Aprovar ou reprovar uma solicitação cujo início já passou é permitido; o pedido não restringe. | `app/dominio/ferias.py` | RN-06 | ACEITO: fora do pedido |
| 4 | Baixo | Após solicitar, `form.reset()` volta o seletor de colaborador para o primeiro da lista. | `app/estatico/index.html` | RF-11 | ACEITO: cosmético |

Nenhum achado alto ou médio.
