# Teste com outro agente: Codex

| Campo | Valor |
|---|---|
| Agente | Codex CLI 0.164.0 (`codex exec`, sandbox de escrita com rede liberada para o `pip`) |
| Pedido | `PEDIDO-TREINO.md` (reserva de salas) |
| Skills | v2, em `skills/` dentro da pasta, sem alteração para o Codex |
| Prompt | o da banca, sem nenhuma nota adicional |
| Início e fim | 08:19:32 e 08:37:41 (18 min) |
| Gates | 6/6 registrados no log |
| Testes | 32/32 (conferido de forma independente depois da execução) |
| Critérios via HTTP | 10/10, mais a tela (11/11) |
| Ajuste manual | nenhum |

Artefatos: [log](P00/evidencias/log-execucao.md), [critérios](P00/evidencias/criterios-aceite.md), [revisão](P00/evidencias/revisao.md), [segurança](P00/evidencias/seguranca.md), [PRD](P00/gerado/docs/PRD.md), [SPEC](P00/gerado/docs/SPEC.md), [saída do Codex](P00/saida-codex.txt).

## Comparação com o Claude Code no mesmo pedido (rodada 02, P00)

| Indicador | Claude Code | Codex |
|---|---|---|
| Tempo | 25 min | 18 min |
| Gates | 6/6 | 6/6 |
| Testes | 89 | 32 |
| Critérios via HTTP | 10/10 | 10/10 |
| Cancelar reserva que já passou | 409 | 422 |

Leitura crítica: o pacote funcionou nos dois agentes sem mudar uma linha. O Codex foi mais rápido e escreveu bem menos testes, cobrindo os critérios e menos bordas. A divergência de status no cancelamento vem do exemplo contraditório da regra 409 ou 422 (E-10 do diário): com a regra ambígua, cada agente escolheu um lado.
