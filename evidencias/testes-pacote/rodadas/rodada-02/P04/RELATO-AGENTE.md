# Relato do agente · Rodada 02 · P04 Férias da equipe

Skills v2, prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`. Horário real: 07:26 a 07:48 (22 min).

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6, todos na primeira tentativa |
| Testes | 71/71 (12 do modelo, 46 funcionais, 13 de segurança) |
| Rodada de testes antes da implementação | 46 failed, 12 passed |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Subida manual | API, TELA e DOCS aprovadas |
| Ajustes manuais | nenhum |
| Pendências | nenhuma |

## Retrabalho durante a execução

- **Construção:** `GET /api/saude` do modelo não estava na SPEC; volta à especificação para documentá-lo.
- **Revisão:** o script de sonda quebrou com `UnicodeEncodeError` no console; rodado de novo com `PYTHONIOENCODING=utf-8`.

## Problemas nas skills apontados pelo agente

1. `/api/saude` não está isento no gate da construção (mesmo achado do P02).
2. Exemplos do teste 409 ou 422 se contradizem em regras que dependem de saldo ou de tempo.
3. Mensagens de validação do framework saem em inglês, contra a regra de mensagens em português.
4. Falta um tipo `Mes` (`AAAA-MM`) no modelo; o agente criou.
5. Contradição do próprio pedido sobre o saldo, resolvida com premissa.
6. O modelo de log convida a preencher o "Fim" antes de ler o relógio.
7. `pip-audit` cria ambiente temporário fora da pasta de trabalho (mesmo achado do P02).
8. `pytest.ini` não filtra o `StarletteDeprecationWarning` (mesmo achado do P02).
9. Falta dizer que testes e `verificar_ca.py` com os formatos da tela bastam para conferir a tela.
10. Contagem das 70 linhas do PRD sem comando pronto.
11. "Nenhuma tabela no PRD" é ambíguo, porque o modelo de PRD é feito de tabelas markdown.
12. Testes de segurança nascem depois do código e passam de primeira; a skill não diz que isso é esperado.
