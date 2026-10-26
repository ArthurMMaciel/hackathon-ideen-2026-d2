# Teste da skill `evolucao`

Mede o fluxo em que o usuário pede uma mudança sobre um sistema que já existe, em vez de um sistema completo num prompt só.

## E01 · Reembolso de despesas (sistema P02 da rodada 02)

| Campo | Valor |
|---|---|
| Ponto de partida | Sistema gerado pela rodada 02 para o P02, com 75 testes passando e `.venv` pronto |
| Agente e modelo | Claude Code, subagente com contexto limpo, `claude-opus-5-5` |
| Mensagem do usuário | "agora preciso poder editar uma despesa enquanto ela estiver pendente (valor, descrição e categoria), respeitando os mesmos limites. Também quero que o resumo do mês mostre quantas despesas há em cada categoria, além do total." |
| Início e fim (relógio) | 08:00:56 e 08:06:03, **5 min 7 s** |
| Códigos novos | RF-12, RN-11, PR-13 a PR-15, CA-11 a CA-14 |
| Códigos alterados | RF-07, RN-01, RN-02, RN-10, PR-06, fora de escopo |
| Testes da mudança antes do código | 11 failed |
| Suíte completa depois | 92 passed (6 testes de segurança novos para a edição) |
| Critérios via HTTP | 15/15 (TELA e CA-01 a CA-14) |
| Testes antigos alterados | nenhum |

Artefatos: [log da evolução](E01-P02/evidencias/log-evolucao.md), [PRD](E01-P02/gerado/docs/PRD.md), [SPEC](E01-P02/gerado/docs/SPEC.md), [critérios](E01-P02/evidencias/criterios-aceite.md), código em [`E01-P02/gerado/`](E01-P02/gerado/).

## Pontos que o agente apontou na skill

- Não diz se os testes da mudança vão para arquivo próprio ou para o existente.
- Não orienta a ordem de validação entre regra nova e regras antigas reaproveitadas.
- Escolhas do pedido (edição parcial ou completa, recorte da contagem) viram premissas e podem variar entre execuções.
- `verificar_ca.py` usa um banco só para todos os blocos; falta orientação de isolamento.
- `verificar_ca.py` sobrescreve `criterios-aceite.md`, apagando a evidência da construção original.
- Não pede conferência da tela quando a mudança a altera.
