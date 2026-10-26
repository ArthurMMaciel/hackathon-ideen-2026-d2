# Teste de instalação em `.claude/skills/`

Feito em 26/10/2026, por volta de 08:45, pelo participante no terminal, com o Claude Code CLI logado. A pasta continha só `PEDIDO.md` (pedido de treino), `gerado/` e `evidencias/` vazias, e as 8 skills copiadas para `.claude/skills/`.

## Verificação estática (antes do teste no CLI)

- 8/8 skills com frontmatter válido, nome igual ao da pasta e descrição.
- 14/14 referências relativas entre skills resolvem para arquivos existentes nesse layout.

## Teste no CLI (somente leitura)

```
claude -p "Liste as skills disponiveis nesta sessao e diga qual usaria para construir o sistema descrito em PEDIDO.md. Resolva o caminho ../concepcao/SKILL.md a partir da skill fabrica e cite o titulo dele." --allowedTools "Read,Glob,Grep"
```

Resultado, resumido da saída:

- **Descoberta:** as 8 skills do pacote listadas (`fabrica`, `concepcao`, `especificacao`, `construcao`, `revisao`, `revisao-seguranca`, `verificacao`, `evolucao`), junto com as skills gerais do harness.
- **Escolha:** `fabrica`, como ponto de entrada para construir do zero. O agente explicou que não usaria `evolucao` porque ainda não existe `gerado/docs/PRD.md`.
- **Caminho relativo:** `../concepcao/SKILL.md` resolvido a partir de `.claude/skills/fabrica/` para `.claude/skills/concepcao/SKILL.md`, com o título correto "Concepção · PRD de uma página".

Conclusão: o pacote funciona instalado em `.claude/skills/`. A construção completa nesse layout não foi rodada por falta de tempo antes do arquivamento. A construção completa a partir das mesmas skills foi provada em 12 execuções com Claude Code e 1 com Codex.
