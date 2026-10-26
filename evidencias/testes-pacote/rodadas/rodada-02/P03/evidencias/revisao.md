# Revisão de qualidade

Revisão feita contra `gerado/docs/PRD.md` e `gerado/docs/SPEC.md`, abrindo os arquivos.

## Testes

- **Antes:** `71 passed, 1 warning in 9.62s`
- **Depois das correções:** `80 passed, 1 warning in 7.62s` (9 casos novos de tipo errado)

## Achados

| # | Gravidade | Descrição | Arquivo | Regra | Status |
|---|---|---|---|---|---|
| 1 | Médio | Inteiros do corpo aceitavam `true`/`false`, `1.5` e `"10"` por coerção do Pydantic: `vagas: true` criava turma com 1 vaga (201). Tipo errado precisa ser 4xx. | `app/rotas/modelos.py:12-13` | RN-01, RN-02, formato | CORRIGIDO: `strict=True` em `InteiroLimitado` e novo `IdNoCorpo` para `turma_id`; testes `test_turma_formato_invalido` (4 casos novos) e `test_inscricao_turma_id_tipo_errado` |
| 2 | Baixo | Filtro de turma futura feito no SQL (`inicio > ?`) e repetido no domínio (`eh_futura`). | `app/rotas/turmas.py:57-60` | RN-14 | ACEITO: o SQL evita carregar turmas passadas; o domínio mantém a regra explícita e testável |
| 3 | Baixo | SQL da carga inicial fica em `app/banco.py`, não em `app/repositorio/`. | `app/banco.py:45-48` | estrutura | ACEITO: o modelo de projeto define `carga_inicial` em `banco.py`; SQL parametrizado em constantes |
| 4 | Baixo | `GET /api/saude` existe sem constar na SPEC. | `app/main.py:34` | SPEC | ACEITO: endpoint do modelo, usado pelo harness da verificação |
| 5 | Baixo | Mensagens de validação de formato (422 do framework) saem em inglês. | `app/main.py` | idioma | ACEITO: as regras transversais mandam usar o 422 padrão do framework para formato; erros de negócio estão em português |
| 6 | Baixo | A tela oferece no seletor turmas cujas inscrições já fecharam (menos de 24h); a recusa só aparece ao enviar. | `app/estatico/index.html` | RN-06 | ACEITO: a mensagem da API é mostrada ao usuário |

## Checklist

**Aderência**
- [x] Cada RF e RN conferido contra a tabela de rastreabilidade da SPEC: 8 endpoints, `carga_inicial`, funções de domínio com `# RN-xx`.
- [x] Enums exatamente como o pedido: `PRESENCIAL`, `ONLINE`, `CONFIRMADA`, `ESPERA`, `CANCELADA`, `PRESENTE`, `AUSENTE` (CHECK no DDL e `Literal` nos modelos).
- [x] Carga inicial cria 3 turmas futuras (7, 14 e 21 dias depois de `agora`), testada em `test_rf_03_carga_inicial_tres_turmas_futuras`.

**Testes**
- [x] Todo `test_ca_XX` confere status e campo do corpo (`situacao`, `posicao_espera`, `erro`, `vagas_restantes`, `taxa_presenca_percentual`).
- [x] Limites: RN-01 (0/1/50/51), RN-02 (0/1/1440/1441), RN-06 (24h01/24h/23h59), RN-07 (−1 min/início), RN-10 (−1 min/início).
- [x] Testes de tempo usam o `relogio` de teste (`ir_para`); nenhum depende da hora real.

**Erros e valores extremos** (sonda via TestClient, `gerado/.tmp/sonda.py`; 34 requisições, nenhuma 5xx)

| Sonda | Status |
|---|---|
| id `99999999999999999999` em `GET /api/turmas/{id}`, `/inscricoes`, `/relatorio-presenca`, `POST /api/inscricoes/{id}/cancelar`, `/presenca` | 422 |
| id `-1`, `abc`, `１２` no caminho | 422 |
| `inicio` com ano `9999` e `0001` | 422 |
| `titulo`/`nome` só com espaços; com 5000 caracteres | 422 |
| `vagas` −3, `duracao_minutos` −10, `vagas` `１２`, `vagas` 1.5, `vagas` null, `vagas` gigante | 422 |
| `modalidade` `online` (minúscula) | 422 |
| `turma_id` gigante, −1, `１２`; `email` com 5000 caracteres, só espaços, null | 422 |
| corpo ausente e JSON inválido | 422 |
| `situacao` de presença com 5000 caracteres | 422 |
| `vagas: true` (antes da correção) | 201 → achado 1; depois: 422 |

- [x] Erros de negócio no formato `{"erro", "mensagem"}`, em português; 409 para estado (INSCRICAO_DUPLICADA, SITUACAO_NAO_CANCELAVEL, SITUACAO_SEM_PRESENCA), 422 para prazo/valor (VAGAS_INVALIDAS, DURACAO_INVALIDA, INICIO_NO_PASSADO, INSCRICOES_ENCERRADAS, CANCELAMENTO_ENCERRADO, TURMA_NAO_INICIADA), 404 para inexistente.

**Estrutura**
- [x] `app/dominio/` importa só `datetime` e `app.dominio.erros` (sem `fastapi`, sem `sqlite3`).
- [x] SQL só em `app/repositorio/` e em `app/banco.py` (DDL e carga inicial; achado 3).
- [x] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py`.
- [x] Inscrever, cancelar (com promoção) e marcar presença rodam em `banco.transacao`.
- [x] Carga inicial usa o `agora` recebido.

**Tela**
- [x] Executa as ações da SPEC (listar turmas futuras, inscrever, ver inscritos) e mostra o erro da API com `mostrarMensagem(..., "erro")`.
- [x] Todo `getElementById` aponta para id existente: `form-inscricao`, `inscritos`, `mensagem`, `titulo-inscritos`, `turmas`, `turma-select` (6 de 6). Sem `querySelector`.
- [x] Script extraído passa em `node --check` (Node v22.23.2).
- [x] Endpoints chamados pela tela respondem com os parâmetros que ela envia (`gerado/.tmp/sonda_tela.py`): `GET /` 200, `GET /api/turmas` 200 (3), `POST /api/inscricoes` com `turma_id` numérico 201 CONFIRMADA, repetido 409 com mensagem, `GET /api/turmas/{id}/inscricoes` 200.
