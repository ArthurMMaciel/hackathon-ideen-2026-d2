# Relato do agente · Rodada 02 · P03 Inscrição em treinamentos

Skills v2, prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`. Horário real: 07:26 a 07:50 (24 min).

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6, todos na primeira tentativa |
| Testes | 95/95 |
| Rodada de testes antes da implementação | 59 failed, 12 passed (os 12 do modelo) |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Subida manual | API, TELA e DOCS aprovadas |
| `pip-audit` | 23 pacotes, 0 vulnerabilidades |
| Ajustes manuais | nenhum |
| Pendências | nenhuma |

## Retrabalho durante a execução

- **Construção:** um comando com heredocs aninhados falhou sem gravar arquivos; o agente regravou com a ferramenta de escrita.
- **Revisão:** achado médio: inteiros no corpo aceitavam `true`, `1.5` e `"10"` por coerção do Pydantic (`vagas: true` criava turma com 1 vaga). Corrigido com `strict=True` e 9 casos de teste.
- **Revisão:** o script de sonda em `.tmp/` não importava `app` sem `PYTHONPATH=.`.

## Problemas nas skills apontados pelo agente

1. Faixa numérica de regra de negócio (ex.: vagas de 1 a 50): no framework ou no domínio? As regras transversais e o gate da especificação apontam para lados diferentes.
2. Os tipos do modelo deixam passar tipo JSON errado no corpo (`true`, `1.5`); falta variante estrita.
3. Recusa por tempo (cancelar depois do início): o teste 409 ou 422 serve para os dois lados; só os exemplos decidiram.
4. "Até o início" tem borda aberta; nenhuma regra diz para que lado pender.
5. Contagens derivadas (vagas ocupadas por presentes e ausentes) não estão na lista de lacunas.
6. Contagem das 70 linhas do PRD exige script.
7. Consulta que a tela precisa registrada como RF sem nomear endpoint: possível, mas trabalhoso.
8. `/api/saude` não isento no gate da construção (mesmo achado de P02 e P04).
9. Carga inicial em `banco.py` contém SQL fora do repositório (mesmo achado do P02).
10. `pip-audit` cria ambiente fora da pasta de trabalho (mesmo achado de P02 e P04).
11. `subida-manual.md` sai com o título de critérios de aceite (mesmo achado do P02).
12. Sondas em `.tmp/` não importam `app` sem `PYTHONPATH=.`.
13. O grep de SQL não pega SQL concatenado em constantes de módulo (mesmo achado do P02).
14. A lista de lacunas não tem item para maiúsculas e minúsculas em chaves únicas (e-mail).
15. O modelo de log não diz para escrever o horário só depois de ler o relógio (mesmo achado de P02 e P04).
