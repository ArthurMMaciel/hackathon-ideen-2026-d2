# Testes do pacote de skills

O pedido oculto da banca tem o mesmo tamanho e tipo do pedido de treino. Para medir se o pacote generaliza, ele é rodado em pedidos novos, de domínios diferentes, com o prompt exato da banca e sem intervenção humana.

## Pedidos

| Pedido | Domínio | O que ele força |
|---|---|---|
| P00 | Reserva de salas (`PEDIDO-TREINO.md`) | Intervalos de horário, sobreposição, ocupação por janela |
| [P01](pedidos/P01-emprestimo-equipamentos.md) | Empréstimo de equipamentos | Estado do item, limites por tipo, contagem por pessoa, atraso em dias |
| [P02](pedidos/P02-reembolso-despesas.md) | Reembolso de despesas | Dinheiro com centavos, fluxo de aprovação, duplicidade, relatório mensal |
| [P03](pedidos/P03-inscricao-treinamentos.md) | Inscrição em treinamentos | Lista de espera, promoção automática, janelas de tempo antes e depois do início |
| [P04](pedidos/P04-ferias-equipe.md) | Férias da equipe | Datas sem horário, dias corridos inclusivos, saldo, restrição por equipe |
| [P05](pedidos/P05-chamados-sla.md) | Chamados com prazo | Prazo em horas, máquina de estados, reabertura com janela, percentual no prazo |

## Método

1. Cada execução roda num diretório limpo com só `skills/` e `PEDIDO.md`, num subagente com contexto limpo.
2. Prompt da banca, sem alteração. O subagente relata no fim onde as skills foram ambíguas.
3. Os artefatos de cada execução (log, PRD, SPEC, revisões, critérios de aceite, código gerado) ficam em `rodadas/<rodada>/<pedido>/`.
4. Cada rodada tem um `RESULTADOS.md` com o quadro consolidado e as melhorias que ela motivou.
5. As melhorias entram nas skills e a rodada seguinte mede o efeito.
