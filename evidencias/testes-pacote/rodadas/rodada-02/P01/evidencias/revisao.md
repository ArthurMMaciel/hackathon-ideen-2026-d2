# Revisão de qualidade

Revisão contra `gerado/docs/PRD.md` e `gerado/docs/SPEC.md`, abrindo os arquivos do sistema.

**Testes antes da revisão:** `62 passed, 1 warning in 9.17s`
**Testes depois das correções:** `62 passed, 1 warning in 6.35s`

## Achados

| # | Gravidade | Descrição | Arquivo | Regra | Status |
|---|---|---|---|---|---|
| 1 | Baixo | Sem equipamento disponível, o seletor fica vazio e o envio mandava `equipamento_id: null`, que voltava com mensagem de validação em inglês. A tela agora avisa em português antes de enviar. | `gerado/app/estatico/index.html` (submit de `form-emprestar`) | RF-11 | CORRIGIDO |
| 2 | Baixo | Erros de validação 422 do framework (formato) trazem `msg` em inglês, que a tela mostra como veio. Erros de negócio estão em português. | `gerado/app/main.py` | Regras transversais: 422 de formato é o padrão do framework | ACEITO (a regra manda usar o 422 padrão) |
| 3 | Baixo | Atrasados são ordenados no SQL (data prevista) e de novo em Python (dias de atraso); resultado idêntico, ordenação duplicada. | `gerado/app/repositorio/emprestimos.py`, `gerado/app/rotas/emprestimos.py` | PR-07 | ACEITO (inofensivo, deixa a regra explícita na rota) |
| 4 | Baixo | `normalizar_email` faz `strip()` que o tipo `Email` já faz. | `gerado/app/dominio/emprestimos.py` | PR-04 | ACEITO (mantém o domínio independente da camada de entrada) |
| 5 | Baixo | Equipamento em `MANUTENCAO` não tem como voltar a `DISPONIVEL` pela API. | — | PR-03, Fora de escopo | ACEITO (decisão registrada no PRD; o pedido não pede essa operação) |
| 6 | Baixo | O aviso `StarletteDeprecationWarning` do TestClient aparece na saída do pytest; o filtro do `pytest.ini` do modelo cobre só `DeprecationWarning`. | `gerado/pytest.ini` | — | ACEITO (vem do modelo; não afeta o sistema) |

Nenhum achado alto ou médio.

## Checklist

**Aderência**
- [x] Cada RF e RN conferido contra a rastreabilidade da SPEC: RF-01..RF-12 com endpoint/tela/carga; RN-01..RN-10 nas funções listadas, com comentário `# RN-xx`.
- [x] Enums exatamente como no pedido: `NOTEBOOK`, `PROJETOR`, `HEADSET`, `DISPONIVEL`, `EMPRESTADO`, `MANUTENCAO`, `ABERTO`, `DEVOLVIDO` (`Literal` nas rotas e `CHECK` no DDL).
- [x] Carga inicial: 8 equipamentos, 3/2/3, EQ-0008 (HEADSET) em MANUTENCAO; idempotente (`test_rf_03_carga_inicial`, `test_rf_03_carga_inicial_idempotente`).

**Testes**
- [x] Todo CA confere status e campo do corpo (`status`, `erro`, `situacao`, `dias_atraso`).
- [x] Limites com borda: RN-04 (13/14/15 e 2/3/4), RN-05 (−1/0), RN-06 (2º aceito, 3º recusado, após devolução aceito), RN-09 (prevista hoje, ontem, 2 dias), RN-10 (último minuto do mês e 1º do mês seguinte).
- [x] Regras de tempo usam o `relogio` de teste; nenhum teste lê a hora real.

**Erros e valores extremos** (sonda em `gerado/.tmp/sonda.py`, todos 4xx)

| Entrada | Status |
|---|---|
| GET equipamento id 99999999999999999999 | 422 |
| GET equipamento id -1 | 422 |
| GET equipamento id １２ | 422 |
| POST devolver id 99999999999999999999 | 422 |
| POST emprestimo equipamento_id 99999999999999999999 | 422 |
| POST emprestimo equipamento_id negativo | 422 |
| POST emprestimo equipamento_id '１２' | 422 |
| POST emprestimo data_prevista 9999-12-31 | 422 |
| POST emprestimo data_prevista 0001-01-01 | 422 |
| POST emprestimo data_prevista com hora | 422 |
| POST emprestimo nome só espaços | 422 |
| POST emprestimo nome 5000 chars | 422 |
| POST emprestimo email inválido | 422 |
| POST emprestimo email 5000 chars | 422 |
| POST emprestimo campo faltando | 422 |
| POST emprestimo corpo não JSON | 422 |
| POST emprestimo campo extra | 422 |
| POST equipamento descricao 5000 | 422 |
| POST equipamento descricao espaços | 422 |
| POST equipamento patrimonio dígitos Unicode | 422 |
| POST equipamento tipo inválido | 422 |
| POST equipamento tipo minúsculo | 422 |
| POST devolver defeito 'sim' | 422 |
| POST devolver defeito 1 | 422 |
| GET disponiveis tipo inválido | 422 |
| GET emprestimos status inválido | 422 |
| GET relatorio mes 9999-12 | 422 |
| GET relatorio mes 0001-01 | 422 |
| GET relatorio mes ２０３０-０１ | 422 |
| GET relatorio mes negativo -2030-01 | 422 |
| GET relatorio mes 5000 chars | 422 |

- JSON inválido: 422 com `json_invalid`, sem stack trace nem SQL.
- [x] Erros de negócio no formato `{"erro", "mensagem"}`, em português; 409 para estado (indisponível, limite, já devolvido, duplicado), 422 para prazo e data anterior; 404 para inexistente.

**Estrutura**
- [x] `app/dominio/` importa só `datetime`, `calendar` e `app.dominio.*` (sem `fastapi`, sem `sqlite3`).
- [x] SQL só em `app/repositorio/` e em `app/banco.py` (DDL e o `INSERT` da carga inicial, que o modelo põe em `banco.carga_inicial`).
- [x] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py`.
- [x] Escritas dependentes de leitura (cadastrar, emprestar, devolver) dentro de `banco.transacao`.
- [x] Carga inicial sem datas; não depende de `agora`.

**Tela**
- [x] Emprestar, devolver (com ou sem defeito), atrasados e disponíveis com filtro; erros da API exibidos por `mostrarMensagem`.
- [x] Todos os `getElementById` (`campo-equipamento`, `filtro-tipo`, `form-emprestar`, `mensagem`, `tabela-abertos`, `tabela-atrasados`, `tabela-disponiveis`) existem no HTML; nenhum `querySelector`; nenhum `innerHTML` com dado.
- [x] `node --check` no script extraído: OK (Node v22.23.2).
- [x] Endpoints chamados pela tela, com os parâmetros que ela envia, respondem via HTTP:

```
GET / 200
GET /api/equipamentos/disponiveis 200
GET /api/equipamentos/disponiveis?tipo=HEADSET 200
GET /api/emprestimos?status=ABERTO 200
GET /api/emprestimos/atrasados 200
POST /api/emprestimos 201
POST repetido (erro mostrado na tela): 409 O equipamento já está emprestado; só equipamento disponível pode ser emprestado.
POST devolver {defeito:false} 200
```
