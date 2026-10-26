# Revisão de qualidade

Sistema: `gerado/` (Reembolso de despesas). Revisado contra `gerado/docs/PRD.md` e `gerado/docs/SPEC.md`.

## Testes

- Antes da revisão: `28 passed, 1 warning`
- Depois das correções: `29 passed, 1 warning` (aviso de depreciação interno do starlette/anyio)

## Checklist

**Aderência**
- [x] Rastreabilidade da SPEC conferida linha a linha: RF-01..RF-11 implementados (8 endpoints, tela, carga inicial); RN-01..RN-10 em `app/dominio/despesas.py` com comentário `# RN-xx`.
- [x] Enums exatamente como o pedido: `TRANSPORTE`, `HOSPEDAGEM`, `ALIMENTACAO`, `OUTROS`; `PENDENTE`, `APROVADA`, `RECUSADA`, `PAGA`.
- [x] Carga inicial: 5 despesas, 2 PENDENTE, 1 APROVADA, 1 RECUSADA, 1 PAGA (`test_rf_11_carga_inicial_cinco_despesas`, e conferido na tela).

**Testes**
- [x] Todo CA-xx confere status e campo do corpo (`situacao`, `erro`, `valor`, `total_geral`).
- [x] Limites com teste no limite, abaixo e acima: RN-01 (0, −1, 0,01), RN-02 (4 categorias), RN-03 (hoje/amanhã e fuso), RN-04 (59/60/61 dias).
- [x] Regras de tempo usam o `relogio` de teste; nenhum teste depende da hora real (a carga inicial usa a hora real nos testes, mas cai em mês distinto de 2030 e nenhum teste de regra depende dela).

**Erros**
- [x] Campo faltando, tipo errado, id inexistente, data com hora → 4xx (`test_validacao_formato_422`, `test_rf_06_despesa_inexistente_404`). Sondagem manual achou dois casos de 500 (R-01, R-02), corrigidos.
- [x] Erros de negócio em `{"erro", "mensagem"}` com mensagem em português.

**Estrutura**
- [x] `app/dominio/` não importa FastAPI nem `sqlite3` diretamente (importa `app.erros`, que o modelo determina; ver R-03).
- [x] SQL só em `app/repositorio/` e DDL em `app/banco.py` (`banco.carga_inicial` tem um `SELECT COUNT(*)` de idempotência, padrão do modelo).
- [x] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py`.
- [x] Escritas dependentes de leitura (lançar com checagem de duplicidade, aprovar/recusar/pagar, excluir) dentro de `banco.transacao`.

**Tela**
- [x] Conferida no navegador contra servidor real: lista carrega, "Recusar" sem motivo mostra "Erro: Informe o motivo para recusar a despesa.", "Pagar" muda a linha para PAGA e atualiza o resumo, lançamento de ALIMENTACAO 130 mostra o erro de limite, lançamento válido funciona; descrição `<b>x</b>` aparece como texto.
- [x] Sem erro de JavaScript no console; todos os IDs usados no script existem no HTML.

## Achados

| ID | Gravidade | Descrição | Arquivo | Status |
|---|---|---|---|---|
| R-01 | Alto | `GET/POST/DELETE /api/despesas/{id}` com id acima de 2^63−1 gerava `OverflowError` do SQLite e HTTP 500. Corrigido com `IdDespesa = Annotated[int, Path(ge=1, le=2**63-1)]` (422). Teste `test_revisao_entradas_fora_da_faixa_retornam_4xx`. | `app/rotas/despesas.py` | CORRIGIDO |
| R-02 | Alto | `GET /api/relatorios/mensal?mes=0000-01` ou `9999-12` gerava `ValueError` de `date` e HTTP 500. Padrão do mês restrito a anos 1900–2999 (422). Mesmo teste. | `app/rotas/despesas.py` | CORRIGIDO |
| R-03 | Baixo | Domínio importa `app.erros`, que importa `fastapi` para o tratador; o domínio fica indiretamente ligado ao FastAPI. É o desenho do modelo de projeto, que manda o domínio levantar `regra_violada`. | `app/dominio/despesas.py` | ACEITO (desenho do modelo) |
| R-04 | Baixo | A rota de lançamento captura `sqlite3.IntegrityError` como segunda barreira de RN-05 (corrida entre requisições); detalhe de banco na camada de rotas. | `app/rotas/despesas.py` | ACEITO (barreira defensiva, dentro da transação) |
| R-05 | Baixo | O mês padrão do resumo na tela vem do relógio do navegador, não de `APP_AGORA`; com relógio fixo no servidor, o resumo inicial pode mostrar outro mês. O usuário escolhe o mês no campo. | `app/estatico/index.html` | ACEITO |
| R-06 | Baixo | Carga inicial usa a hora real nos testes (o relógio de teste só substitui a dependência das rotas). | `app/banco.py` | ACEITO (não afeta nenhuma asserção) |
