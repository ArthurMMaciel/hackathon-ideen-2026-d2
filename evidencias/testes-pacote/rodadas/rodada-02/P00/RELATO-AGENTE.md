# Relato do agente · Rodada 02 · P00 Reserva de salas (pedido de treino)

Skills v2, prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`. Horário real: 07:26 a 07:51 (25 min). É esta execução que está em `gerado/` e nas evidências da raiz de `evidencias/`.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 89/89 |
| Rodada de testes antes da implementação | 57 failed, 12 passed (os 12 do modelo) |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Ajustes manuais | nenhum |
| Pendências | nenhuma |

## Retrabalho durante a execução

- **Revisão:** achado médio pela sonda de valores extremos: horários com fração de segundo eram validados com a fração e gravados truncados, e a API devolvia um horário diferente do enviado. Corrigido descartando a fração na entrada, com teste e volta à SPEC.
- **Segurança:** um teste de XSS procurava a palavra `innerHTML` e acusou o comentário do próprio modelo; o agente corrigiu o teste para procurar uso real.
- **Construção:** comando com heredocs aninhados falhou; arquivos regravados com a ferramenta de escrita.

## Problemas nas skills apontados pelo agente

1. Exemplo "data no passado → 422" contradiz o teste de decisão em "cancelar reserva que já passou" (mesmo achado de P03, P04, P05).
2. O modelo não trata frações de segundo: `DataHora` aceita a fração e `para_banco` grava truncado.
3. `/api/saude` e `/redoc` fora da lista de endpoints permitidos (mesmo achado de todas).
4. `pip-audit` cria ambiente fora da pasta de trabalho (mesmo achado de todas).
5. O `pip-audit` instalado no `.venv` só não contamina a verificação porque ela recria o ambiente.
6. O checklist de XSS acha o comentário "nunca por innerHTML" do próprio modelo.
7. Fuso da tela: `datetime-local` não tem fuso, e o modelo não traz função para montar o horário com offset.
8. O "hoje" da tela usa o relógio do navegador; o servidor usa `APP_AGORA`.
9. Escopo da tela ambíguo quando o pedido cita mais funções do que a frase da tela.
10. Não está dito se `parametrize` atende à exigência de nomes do plano (mesmo achado do P05).
11. Contagem das 70 linhas do PRD sem script pronto (mesmo achado de P03, P04, P05).
12. O item "instala num `.venv` novo" do gate da construção é trivialmente verdadeiro; a prova real só vem na verificação.
13. "Fim" da etapa escrito antes de ler o relógio (mesmo achado de todas).
14. A lista de lacunas induz a sempre achar algo, mesmo quando "não se aplica" seria a resposta certa.
