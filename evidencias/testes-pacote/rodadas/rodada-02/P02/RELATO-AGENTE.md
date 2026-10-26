# Relato do agente · Rodada 02 · P02 Reembolso de despesas

Skills v2, prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`. Horário real: 07:26 a 07:48 (22 min).

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 75/75 (57 funcionais, 18 de segurança, incluindo os 12 do modelo) |
| Rodada de testes antes da implementação | 45 failed, 12 passed |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Subida manual | API, TELA e DOCS aprovadas |
| Ajustes manuais | nenhum |
| Pendências | nenhuma |

## Retrabalho durante a execução

- **Construção:** `GET /api/saude` do modelo não estava na SPEC; o agente voltou à SPEC para documentá-lo.
- **Revisão:** achado médio: SQL da carga inicial em `app/banco.py`, movido para o repositório.

## Problemas nas skills apontados pelo agente

1. A carga inicial fica em `banco.py`, mas a revisão exige SQL só no repositório.
2. `/api/saude` não está listado como endpoint permitido fora da SPEC.
3. Dados iniciais com datas relativas caem nos períodos dos relatórios; não há orientação para testar totais (o agente testou por diferença antes e depois).
4. Pedido com "5 despesas em situações diferentes" e só 4 situações.
5. Fronteira entre "sem formato de dado no PRD" e unidade de dinheiro; a API recebe centavos inteiros só por indicação do tipo `Centavos`.
6. Contagem das 70 linhas do PRD com detalhes em aberto.
7. Sem precedência entre 409 e 422 quando duas regras se aplicam na mesma requisição.
8. `pytest.ini` do modelo não filtra o `StarletteDeprecationWarning` (1 aviso em toda execução).
9. O `pip-audit` cria ambiente temporário fora da pasta de trabalho, contra a regra 6 da `fabrica`.
10. `Verificacao.salvar` usa título fixo; `subida-manual.md` sai com título de critérios de aceite.
11. Horário do fim da etapa anotado antes de ler o relógio uma vez.
12. O grep de SQL não pega f-string definida como constante de módulo.
13. `Centavos` aceita a string `"12"` (coerção leniente do Pydantic).
14. Falta receita para confirmar no Windows que nenhum servidor ficou rodando.
