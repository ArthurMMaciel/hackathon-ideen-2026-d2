# Relato do agente · Rodada 01 · P04 Férias da equipe

Execução com o prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 68/68 |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Ajustes manuais | nenhum |
| Pendências | CVEs do starlette 0.41.3 e do pytest 8.3.4; só a CVE-2025-62727 se aplica e foi contornada. A tela não foi clicada num navegador real |

## Retrabalho durante a execução

- **Construção:** `Field(strict=True)` em campo `date` recusou até datas válidas, porque o FastAPI valida o corpo em modo Python. O agente trocou por `field_validator` com formato `AAAA-MM-DD`.
- **Revisão:** achado alto de HTTP 500 com id gigante (`OverflowError` do SQLite), encontrado só porque o agente testou valores extremos fora do checklist. Corrigido com limite e teste de regressão.
- **Segurança:** falsos positivos no grep de SQL (concatenação de constantes) e a CVE-2025-62727 no `FileResponse` do modelo, trocado por `HTMLResponse`.
- **Processo:** um comando com caminho relativo escreveria fora do diretório; foi bloqueado antes de rodar.

## Problemas nas skills apontados pelo agente

1. **Datas sem hora não estão previstas nas regras transversais.** A regra exige ISO 8601 com offset, UTC no banco e intervalos semiabertos. O pedido trabalha com dias inteiros e período fechado. O agente improvisou datas `AAAA-MM-DD` em texto e sobreposição fechada.
2. **Contradição no próprio pedido sobre o saldo**, que a lista de lacunas não cobre. O agente resolveu com uma premissa e um teste.
3. Domínio depende de FastAPI indiretamente por `app/erros.py` (mesmo achado do P00).
4. Stack fixada com CVEs e `FileResponse` vulnerável no modelo (mesmo achado do P00).
5. Grep de SQL com falso positivo (mesmo achado do P00).
6. TDD um teste por vez é caro; o agente fez em lote (mesmo achado do P00).
7. `.gitignore` do repositório ambíguo (mesmo achado do P00).
8. Revisão feita pelo mesmo agente que construiu; o checklist não pede valores extremos.
9. A localização de `evidencias/` só fica clara pelo harness.
10. Não há forma prevista de testar a tela de verdade; o agente usou `node --check` e conferência de IDs.
11. Horários do log anotados à mão, aproximados (mesmo achado do P00).
12. Validações de formato ficam melhor no Pydantic do que em função de domínio; porta 8000 ocupada pelas execuções paralelas.
