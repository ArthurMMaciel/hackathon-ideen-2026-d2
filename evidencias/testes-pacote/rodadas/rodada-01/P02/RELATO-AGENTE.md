# Relato do agente · Rodada 01 · P02 Reembolso de despesas

Execução com o prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6, todos na primeira conferência |
| Testes | 36/36 |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Ajustes manuais | nenhum |
| Pendências | CVEs da stack fixada (só a CVE-2025-62727 se aplica e foi contornada). Desvio de processo: código escrito antes dos testes, compensado com mutação proposital (4 regras alteradas, 7 testes falharam, código restaurado) |

## Retrabalho durante a execução

- **Revisão:** dois HTTP 500 (id gigante e mês `0000-01` ou `9999-12`), corrigidos para 422 com testes e com volta à especificação.
- **Segurança:** CVE-2025-62727 no `FileResponse` do modelo, trocado por `HTMLResponse` com teste.
- **Processo:** horários do log inventados no início (18:10–18:38), corrigidos pelo próprio agente para os reais (17:36–18:00) comparando com as datas dos arquivos. Um arquivo de log temporário foi escrito fora do diretório de trabalho e apagado.

## Problemas nas skills apontados pelo agente

1. **Contradição direta:** as regras transversais dizem "não apague registros de negócio" e o pedido manda excluir despesa pendente. Nada diz qual prevalece. O agente fez o pedido prevalecer.
2. **Carga inicial não recebe o relógio injetável** e roda no startup, fora do alcance do relógio de teste (mesmo achado do P05).
3. **Datas sem horário não previstas** nas regras (mesmo achado do P04). Pydantic aceita `"2030-01-05T00:00:00"` como data; o agente precisou de regex.
4. Itens de gate que o próprio modelo quebra: domínio importa FastAPI via `app/erros.py`; `datetime.now()` no `harness.py` (mesmos achados de P00, P04, P05).
5. `pip-audit` sem severidade e stack fixada com CVEs; `FileResponse` vulnerável no modelo (mesmo achado de P00, P04, P05).
6. `.gitignore` pressupõe repositório git; o grep de SQL não pega consulta montada em outra linha.
7. Regra de contagem de linhas do PRD só aparece na `concepcao`.
8. Código HTTP para mudança de estado inválida e exclusão proibida não definido (409 ou 422) (mesmo achado do P05).
9. A ordem "teste antes do código" não tem evidência exigida por nenhum gate.
10. Windows: acentos quebrados no console sem `PYTHONIOENCODING=utf-8`; falta receita para subir e derrubar o servidor; o painel do navegador recusou `127.0.0.1` e aceitou `localhost`.
11. Menores: distribuição dos dados iniciais não definida; mês fora da faixa de datas do Python gerou HTTP 500; o checklist pede teste de "data sem fuso", que não se aplica a campo só de data.
