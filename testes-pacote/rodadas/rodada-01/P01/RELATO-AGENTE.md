# Relato do agente · Rodada 01 · P01 Empréstimo de equipamentos

Execução com o prompt da banca, subagente Claude Code com contexto limpo, modelo `claude-opus-5-5`.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6, todos na primeira tentativa |
| Testes | 55/55 |
| Critérios de aceite via HTTP | 10/10, mais a linha TELA (11/11) |
| Ajustes manuais | nenhum |
| Pendências | Equipamento em `MANUTENCAO` nunca volta a `DISPONIVEL` (o pedido não pede; registrado como premissa e fora de escopo). CVEs do starlette 0.41.3 sem impacto no código. Tela não clicada num navegador real |

## Retrabalho durante a execução

- **Construção:** um ensaio do `verificar_ca.py` mostrou que o corte do JSON em 160 caracteres apagava o campo `status` da evidência do CA-01. O agente passou a registrar os campos conferidos.
- **Revisão:** um achado alto (HTTP 500 com id acima de 2^63−1 em três endpoints) e dois médios (data prevista aceitava número Unix e data com hora; padrão `\d` aceitava dígitos Unicode de largura cheia). Corrigidos com testes e SPEC atualizada.
- **Segurança:** falso positivo no grep de SQL; CVE-2025-62727 no `FileResponse` do modelo, trocado por `HTMLResponse`.
- **Processo:** horários do log estimados, corrigidos pelo carimbo do harness e marcados como aproximados. O painel do navegador, compartilhado com as execuções paralelas, trocou para a aplicação de outra execução no meio do teste; o agente parou de usá-lo sem enviar nada.

## Problemas nas skills apontados pelo agente

1. **Datas sem horário não previstas** nas regras transversais (mesmo achado de P02 e P04): falta dizer qual fuso define "hoje" e como gravar.
2. **O modelo e a orientação não limitam o id** pelo limite de 64 bits do SQLite (mesmo achado de todas as execuções).
3. Stack fixada com CVEs e `FileResponse` vulnerável no modelo; segurança e stack não dizem qual prevalece (mesmo achado de todas).
4. Domínio importa FastAPI via `app/erros.py` (mesmo achado de todas).
5. Grep de SQL com falso positivo (mesmo achado de todas).
6. 409 ou 422 ambíguo: limite de 2 empréstimos por pessoa, equipamento já emprestado, empréstimo já devolvido (mesmo achado de P02 e P05).
7. TDD um teste por vez; o agente escreveu em lote, com 41 falhas antes de implementar (mesmo achado de todas).
8. Não há método para conferir a tela sem navegador; o painel compartilhado atrapalhou.
9. `.gitignore` pressupõe repositório git (mesmo achado de todas).
10. Zonas cinzentas do PRD: formato `EQ-0000` do próprio pedido; nível de detalhe da premissa de ordenação; RF inferido para listar empréstimos abertos na tela.
11. Menores: `datetime.now()` no harness; ordem das linhas na evidência depende da ordem de execução; `pip-audit` fica no `.venv`; acentos corrompidos no console do Windows.
