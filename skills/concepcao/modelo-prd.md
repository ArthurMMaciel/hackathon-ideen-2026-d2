# Modelo do PRD

Copie a estrutura para `gerado/docs/PRD.md`. Mantenha em uma página: frases curtas, uma linha por item.

```markdown
# PRD · <nome do sistema>

## Problema
<uma ou duas frases, com as palavras do cliente e a dor atual>

## Usuários
- <quem usa e para quê>

## Objetivo
<o resultado esperado em uma frase>. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| <Entidade> | <atributo, atributo> | <ENUM_A, ENUM_B> |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | <verbo + capacidade> |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | <restrição com número e borda explícitos> |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | <interpretação assumida para uma lacuna do pedido> |

## Fora de escopo
- <item>

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | <cenário do pedido> | <resultado do pedido> | RF-xx, RN-xx |
```
