# Modelo do log de execução

Copie para `evidencias/log-execucao.md` na etapa 0 e preencha durante a execução. Uma seção por etapa, na ordem em que aconteceram. Voltas a etapas anteriores ganham uma seção nova.

```markdown
# Log de execução

| Campo | Valor |
|---|---|
| Agente | <nome e versão> |
| Modelo | <id do modelo> |
| Início | <data e hora> |
| Pedido usado | <caminho do arquivo ou "texto do prompt"> |

## Prompt de entrada

> <prompt literal>

## Etapa <n> · <nome>

- **Início:** <hora>
- **Artefatos:** <caminhos>
- **Decisões e premissas:** <PR-xx e escolhas relevantes, uma por linha>
- **Cobertura do pedido (só na etapa 1):** tabela com cada trecho do pedido e os códigos que o cobrem
- **Lacunas comuns (só na etapa 1):** tabela com cada item da lista da `concepcao` e o código que o resolve, ou "não se aplica" com o motivo
- **Gate:** o checklist da skill da etapa, item por item, marcado `[x]` ou `[ ]`
- **Problemas e correções:** <o que falhou e como foi corrigido>
- **Gate:** APROVADO | GATE FALHOU (<causa>)
- **Fim:** <hora>

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | <n>/6 |
| Testes | <passaram>/<total> |
| Critérios de aceite verificados via HTTP | <n>/<total> |
| Ajustes manuais | nenhum \| <lista> |
| Pendências | <lista ou "nenhuma"> |
```
