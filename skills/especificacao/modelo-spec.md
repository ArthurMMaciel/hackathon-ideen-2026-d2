# Modelo da especificação

Copie a estrutura para `gerado/docs/SPEC.md`.

````markdown
# SPEC · <nome do sistema>

## Modelo de dados

```sql
CREATE TABLE IF NOT EXISTS <tabela> (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ...
);
```

## Carga inicial
| <coluna> | <coluna> | ... |
|---|---|---|

## Endpoints

### <MÉTODO> /api/<caminho> · RF-xx
- **Entrada:** <campos, tipos, obrigatoriedade, limites>
- **Sucesso:** <status> `<exemplo JSON>`
- **Erros:**
  | Status | Código | Regra |
  |---|---|---|
  | 409 | <CODIGO> | RN-xx |

## Regras de negócio
| Regra | Função em app/dominio | Erro |
|---|---|---|
| RN-01 | `<modulo>.<funcao>` | 422 <CODIGO> |

## Tela
- <o que mostra, ações, endpoints chamados>

## Rastreabilidade
| Requisito | Atendido por |
|---|---|
| RF-01 | `POST /api/...` |

## Plano de testes
| Teste | Verifica | Relógio | Entrada | Esperado |
|---|---|---|---|---|
| test_ca_01_<resumo> | CA-01 | 2030-01-07 09:00 | <dados> | 201, status ATIVA |
| test_rn_04_<resumo> | RN-04 | ... | ... | 422 <CODIGO> |
````
