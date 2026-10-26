# Relato do agente · Rodada 01 · P05 Chamados com prazo

Execução com o prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 89/89 |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Ajustes manuais | nenhum |
| Pendências | CVEs do starlette 0.41.3 e do pytest 8.3.4; só a CVE-2025-62727 se aplica e foi contornada com `HTMLResponse` |

## Retrabalho durante a execução

- **Especificação:** o autoexame achou uma regra de limite sem teste de borda no plano; o agente incluiu o teste antes de fechar o gate.
- **Construção:** a primeira validação de transições aceitava "assumir" um chamado resolvido como se fosse reabrir, sem a janela de 7 dias. Dois testes pegaram o erro. O agente refez a validação por ação e voltou à especificação para corrigir a SPEC.
- **Revisão:** dois HTTP 500 reais (id gigante e data `9999-12-31` no relatório), corrigidos com testes.

## Problemas nas skills apontados pelo agente

1. **Carga inicial não recebe o relógio injetável.** Dados de exemplo com datas relativas ("atrasado") usam o relógio real, enquanto os testes usam 2030. Nada nas skills cobre isso.
2. "Nenhum `datetime.now()` fora de `app/relogio.py`" conflita com o `harness.py` do modelo, que usa `datetime.now()`.
3. Domínio depende de FastAPI por `app/erros.py` (mesmo achado de P00 e P04).
4. Transição de estado inválida: 409 ou 422 não está definido.
5. Campo obrigatório: erro 422 do framework ou código de negócio não está definido.
6. Grep de SQL com falso positivo (mesmo achado de P00 e P04).
7. `pip-audit` encontrou CVEs nas versões que a própria stack fixa; não há regra para isso. No Windows, a saída em texto do `pip-audit` quebra com `UnicodeEncodeError`, e a saída do script de verificação mostra acentos errados sem `PYTHONIOENCODING=utf-8`.
8. `.gitignore` do repositório pressupõe um repositório git (mesmo achado de P00 e P04).
9. TDD um teste por vez é inviável; o agente fez em lote (mesmo achado de P00 e P04).
10. Não há forma prevista de conferir erros de JavaScript da tela; o agente usou `node --check` e o console do navegador.
11. Não há receita para parar o servidor em segundo plano no Windows (mesmo achado do P00).
12. A contagem de 60 linhas do PRD é trabalhosa (deu 48).
13. Horários do log estimados (mesmo achado de P00 e P04).
14. A construção roda `verificar_ca.py` como teste e sobrescreve a evidência antes da etapa de verificação.
