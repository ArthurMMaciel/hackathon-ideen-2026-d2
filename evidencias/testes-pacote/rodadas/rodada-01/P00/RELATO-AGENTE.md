# Relato do agente · Rodada 01 · P00 Reserva de salas

Execução com o prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`. Duração de cerca de 26 minutos e 71 chamadas de ferramenta.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 83/83 |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Ajustes manuais | nenhum |
| Pendências | CVEs no starlette 0.41.3 (preso pelo fastapi 0.115.6) e no pytest 8.3.4, sem impacto no uso do sistema; aviso de depreciação do anyio |

## Retrabalho durante a execução

- **Revisão:** a sondagem achou HTTP 500 com id acima de 2^63−1 e com datas no ano 1 ou 9999. O agente voltou à concepção e à especificação (PR-10: datas entre 2000 e 2100). Também esbarrou numa particularidade do FastAPI 0.115: validador dentro de `Annotated` só vale em query na forma `Annotated[T, Query()]`.
- **Segurança:** o `pip-audit` apontou a CVE-2025-62727 (negação de serviço via cabeçalho `Range` no `FileResponse`), que afeta a tela servida pelo modelo de projeto. O agente trocou por `HTMLResponse` e adicionou teste de regressão.
- **Processo:** o agente escreveu uma vez fora do diretório de trabalho e apagou o arquivo. Os primeiros horários do log foram estimados; os seguintes, lidos do relógio.

## Problemas nas skills apontados pelo agente

1. `revisao` exige domínio sem FastAPI, mas o domínio levanta erros de `app/erros.py`, que importa FastAPI.
2. O modelo de projeto serve a tela com `FileResponse`, exposto à CVE-2025-62727.
3. A stack fixada tem vulnerabilidades conhecidas e não há regra para tratar CVE de dependência fixada; dependências transitivas não estão fixadas.
4. O modelo permite HTTP 500 com entradas comuns (datas extremas, id gigante). Falta regra de faixa para datas e ids.
5. Falta na `construcao` a forma correta de validar parâmetros de consulta (`Annotated[T, Query()]`).
6. A instrução sobre `.gitignore` do repositório é ambígua; o agente criou `gerado/.gitignore`.
7. A varredura de SQL da `revisao-seguranca` acusa f-strings que só interpolam constantes.
8. A fronteira entre "sem formato de dado no PRD" e "decidir formato nas lacunas" continua cinzenta.
9. A agenda do dia por sala exigiu inferir um RF que o pedido não lista como operação.
10. Comportamentos decididos pelo agente: cancelar reserva já cancelada dá 409; início igual a agora é aceito; reserva que cruza a janela das 8h às 18h é recortada; percentual arredondado com `round` do Python.
11. TDD estrito, um teste por vez em 23 linhas de plano, é caro. O agente escreveu em dois lotes e registrou o desvio.
12. O harness não ordena as linhas por código.
13. O log pede horários, mas a skill não manda ler o relógio.
14. Falta receita multiplataforma para a subida manual em segundo plano no Windows.
