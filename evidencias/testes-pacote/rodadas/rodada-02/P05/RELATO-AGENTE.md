# Relato do agente · Rodada 02 · P05 Chamados com prazo

Skills v2, prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`. Horário real: 07:26 a 07:50 (24 min).

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6, todos na primeira conferência |
| Testes | 87/87 |
| Rodada de testes antes da implementação | 1 failed, 10 passed, 56 errors (erros de import da carga inicial) |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Sondas de valores extremos | nenhuma resposta 5xx |
| `pip-audit` | 23 pacotes, 0 vulnerabilidades |
| Ajustes manuais | nenhum |
| Pendências | nenhuma |

Horário por etapa, lido do relógio: preparação 07:26–07:27, PRD 07:28–07:29, SPEC 07:29–07:31, construção 07:31–07:40, revisão 07:41–07:43, segurança 07:44–07:47, verificação 07:47–07:50.

## Retrabalho durante a execução

- **Construção:** testes parametrizados com nomes diferentes do plano, reescritos como funções separadas; volta à SPEC para documentar `/api/saude`.
- **Revisão:** arredondamento com `round()` de float (6,25 virava 6,2) corrigido para "meio para cima", com volta ao PRD e à SPEC.

## Problemas nas skills apontados pelo agente

1. Exemplo "prazo → 422" contradiz o teste de decisão na reabertura depois de 7 dias (mesmo achado de P03, P04).
2. Campo exigido só numa ação não pode usar `Texto` (que tem `min_length=1`), senão a recusa sai como 422 do framework.
3. `/api/saude` fora da lista de endpoints permitidos (mesmo achado de todas as execuções da rodada 02).
4. Sem regra de precedência quando uma requisição viola duas regras (mesmo achado de P01, P02).
5. Carga inicial em `banco.py` com SQL fora do repositório (mesmo achado de P01, P02, P03).
6. Com a carga inicial no passo 3, a rodada de testes antes da implementação vira erro de import em vez de falha de asserção.
7. Não está dito se `pytest.mark.parametrize` atende à exigência de nomes do plano.
8. Contagem das 70 linhas do PRD exige script (mesmo achado de P03, P04).
9. `pip-audit`, `venv` e cache do pip escrevem fora da pasta de trabalho (mesmo achado de todas).
10. `subida-manual.md` sai com o título de critérios de aceite (mesmo achado de P02, P03).
11. Lacunas novas: o que acontece com campos quando o fluxo volta atrás (reabertura) e quais situações entram no relatório.
12. Falta orientação para representar uma indicação pedida como palavra (`ATRASADO`).
13. A regra de horário funcionou, mas depende da disciplina do agente; nenhum gate confere.
