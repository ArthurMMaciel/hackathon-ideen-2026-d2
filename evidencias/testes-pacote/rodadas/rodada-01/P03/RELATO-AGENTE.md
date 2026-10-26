# Relato do agente · Rodada 01 · P03 Inscrição em treinamentos

Execução com o prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 59/59 |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Ajustes manuais | nenhum |
| Pendências | Atualizar fastapi e starlette quando a stack permitir; só a CVE-2025-62727 atingia a tela e foi contornada. A tela não foi aberta num navegador real |

## Retrabalho durante a execução

- **Revisão:** dois HTTP 500 (id acima de 64 bits e data `9999-12-31T23:00-03:00` na conversão para UTC) e textos só com espaços aceitos. Corrigidos, com volta à especificação.
- **Segurança:** CVE-2025-62727 no `FileResponse` do modelo, trocado por `HTMLResponse`.
- **Verificação:** a evidência do CA-03 cortava o JSON antes do campo que prova a promoção da fila; o agente ajustou o texto registrado e rodou de novo.
- **Processo:** um comando com heredocs aninhados falhou sem gravar nada. Arquivos temporários foram escritos fora do diretório de trabalho e apagados em seguida; uma tentativa de remoção fora do diretório foi bloqueada antes de rodar.

## Problemas nas skills apontados pelo agente

1. **Carga inicial sem relógio injetável.** "3 turmas futuras" precisa de datas relativas a "agora". O agente alterou o modelo para `iniciar(caminho, agora)` e fez o ciclo de vida ler a substituição de `obter_agora` (mesmo achado de P02 e P05).
2. `datetime.now()` no `harness.py` do modelo contradiz o gate (mesmo achado de P02 e P05).
3. Domínio importa FastAPI via `app/erros.py` (mesmo achado de todas as execuções).
4. Stack fixada com CVEs e `FileResponse` vulnerável no modelo (mesmo achado de todas as execuções).
5. TDD um teste por vez; o agente escreveu o plano inteiro e confirmou 46 falhas antes de implementar (mesmo achado de todas as execuções).
6. `.gitignore` pressupõe repositório git (mesmo achado de todas as execuções).
7. `/docs` e `/openapi.json` do FastAPI: não está dito se contam como endpoint fora da SPEC.
8. Não há forma prevista de executar a tela num navegador real.
9. Interpretações de negócio deixadas ao agente, todas registradas: 24 h exatas antes do início já recusa; vaga ocupada inclui presentes e ausentes; cancelar inscrição em espera não promove ninguém; promoção vale até o início; presença não muda depois de marcada.
10. O limite de 60 linhas do PRD ficou perto de estourar (55).
11. O harness não orienta que campo registrar como "obtido"; acentos corrompidos no console do Windows.
12. Escrita fora do diretório de trabalho (falha do agente, apagada em seguida).
