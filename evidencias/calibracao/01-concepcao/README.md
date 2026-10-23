# Calibração 01 · Etapa de concepção isolada

| Campo | Valor |
|---|---|
| Data | 23/10/2026 |
| Agente | Claude Code, subagente com contexto limpo |
| Modelo | claude-opus-5-5 |
| Diretório | cópia limpa contendo apenas `skills/` e `PEDIDO.md` (cópia de `PEDIDO-TREINO.md`) |
| Escopo | etapa 0 e etapa 1 da `fabrica`, com parada depois do gate |
| Versão das skills | `fabrica` aprovada (D-08) e `concepcao` em revisão (D-09) |

## Prompt

> Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga as etapas das skills. NESTA EXECUÇÃO, rode SOMENTE a etapa 0 (preparação) e a etapa 1 (concepção) da skill fabrica, incluindo o gate da concepção, e pare. Não escreva especificação nem código.

O subagente recebeu também a instrução de trabalhar só no diretório limpo e de relatar ambiguidades das skills.

## Resultado

- [PRD.md](PRD.md): 11 RF, 11 RN, 12 PR, fora de escopo, CA-01 a CA-10 mapeados.
- [log-execucao.md](log-execucao.md): etapas 0 e 1 com tabela de cobertura e gate.
- Gate da concepção aprovado pelo agente, com uma interpretação própria do limite de uma página.
- Duração: cerca de 2 min 40 s.

## Problemas encontrados nas skills (relato do agente, conferido pela IA principal)

1. O limite "cerca de 60 linhas de conteúdo" conflita com o modelo de 9 seções em tabela: o PRD saiu com 72 linhas não vazias e 52 linhas de itens. O agente precisou inventar a regra de contagem.
2. A etapa manda transformar interfaces em RF, mas o gate proíbe tecnologia. Não está dito se termos do próprio pedido ("API REST", "banco local") são permitidos.
3. As regras transversais definem formato ISO 8601 e mandam registrar como premissa, o que leva detalhe técnico ao PRD.
4. Existem dois gates para a mesma etapa (4 itens na tabela da `fabrica`, 7 itens na `concepcao`), sem dizer qual vale.
5. "Toda lacuna virou premissa" só pode ser julgado pelo próprio agente.
6. O modelo de critérios de aceite não tem coluna de resultado esperado. O agente juntou cenário e resultado com "→".
7. Desempates de premissas (nome único, início igual a agora, reserva em andamento) podem variar entre execuções e agentes.
