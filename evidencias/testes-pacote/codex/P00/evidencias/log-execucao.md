# Log de execução

| Campo | Valor |
|---|---|
| Agente | Codex |
| Modelo | GPT-6 |
| Início | 2026-10-26 08:20, horário lido por Python |
| Pedido usado | `PEDIDO.md` |

## Prompt de entrada

> Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

## Etapa 0 · Preparação

- Python 3.11.0 confirmado; `gerado/` e `evidencias/` criados.
- Referências `regras-transversais.md` e `stack-padrao.md` lidas.

## Etapa 1 · Concepção

- **Horário lido:** 08:21 (fechamento).
- **Artefato:** `gerado/docs/PRD.md`.
- **Cobertura do pedido:**

| Trecho | Códigos |
|---|---|
| Salas em três locais, cadastro e recursos | RF-01, RN-07 |
| Seis salas, duas por local | RF-02 |
| Reserva com responsável, título, participantes e intervalo | RF-03 |
| Evitar sobreposição e permitir encostar | RN-01 |
| Duração de 15 minutos a 4 horas | RN-02 |
| Não reservar no passado | RN-03 |
| Participantes até capacidade | RN-04 |
| Cancelar apenas futura, manter histórico e liberar horário | RF-04, RN-05 |
| Salas livres com filtros | RF-05, PR-06 |
| Ocupação 8h–18h sem canceladas | RF-06, RN-06 |
| API REST, tela web, banco local, sem login | RF-07, RF-08, RF-09, fora de escopo |
| CA-01 a CA-10 | Tabela de critérios no PRD |

- **Lacunas comuns:**

| Item | Resolução |
|---|---|
| Fuso e formato de data | PR-01 |
| Bordas de limites | RN-01 a RN-07 |
| Alcance de cadastro | PR-02 |
| Unicidade | PR-03 |
| E-mail, vazio, negativo | PR-03, RN-04, RN-07 |
| Mudança de status e relacionados | RN-05 |
| Dia, período e horário | RN-06, PR-05, PR-06 |
| Arredondamento e unidade | PR-05, RN-06 |
| Ordenação | PR-04 |
| Contradições | Não se aplica: pedido consistente |
| Interação de regras | RN-01 e RN-05: cancelada libera horário |
| Data sem horário | PR-05 |

- **Gate:** [x] PRD até 70 linhas de itens; [x] cobertura completa; [x] lacunas registradas; [x] bordas explícitas; [x] CA originais; [x] fora de escopo; [x] sem decisões técnicas.
- **Resultado:** APROVADO.

## Etapa 2 · Especificação

- **Artefato:** `gerado/docs/SPEC.md`.
- **Gate:** [x] seções do modelo; [x] RF rastreados; [x] RN mapeadas a funções e erros; [x] contratos dos endpoints; [x] dez testes CA; [x] testes de borda RN; [x] DDL SQLite completo.
- **Resultado:** APROVADO.

## Etapa 3 · Construção

- **Artefatos:** código, testes, tela, README e roteiro HTTP em `gerado/`.
- **Ambiente:** `.venv` com versões fixas instaladas. Primeira tentativa de `venv` demorou; instalação repetida diretamente com `pip` concluiu.
- **Rodada inicial registrada:** `2 failed, 26 passed` após implementação inicial; correção de asserções de relatório por `sala_id`.
- **Desvio e correção:** a primeira implementação não registrou a rodada vermelha antes do código. O gate foi repetido em `gerado/.tmp/reconstrucao`: modelo original + todos os testes do plano, antes de copiar a implementação, resultou em `20 failed, 12 passed`; após copiar o código, `32 passed, 1 warning`. A repetição prova a sequência vermelho/verde em uma construção isolada.
- **Gate:** [x] instalação; [x] rodada vermelha antes da implementação na reconstrução; [x] suíte sem falhas; [x] um teste por CA; [x] bordas RN; [x] endpoints da SPEC; [x] relógio isolado; [x] verificador HTTP; [x] README.
- **Resultado:** APROVADO após repetição isolada.

## Etapa 4 · Revisão de qualidade

- **Artefato:** `evidencias/revisao.md`.
- **Gate:** [x] tabela de achados; [x] nenhum achado alto/médio aberto; [x] testes passaram após correções.
- **Resultado:** APROVADO.

## Etapa 5 · Revisão de segurança

- **Artefato:** `evidencias/seguranca.md`, `tests/test_seguranca.py`, `.tmp/pip-audit.json`.
- **Varredura:** `No known vulnerabilities found`.
- **Gate:** [x] testes de ataque; [x] checklist preenchido; [x] nenhum achado alto/médio aberto; [x] suíte passou após correções.
- **Resultado:** APROVADO.

## Etapa 6 · Verificação

- **Artefatos:** `evidencias/criterios-aceite.md` e `evidencias/subida-manual.md`.
- **Horário lido:** 08:37 (fechamento).
- **Instalação limpa:** `.venv/` e `dados/` removidos dentro de `gerado/`; ambiente recriado e dependências instaladas.
- **Testes:** `32 passed, 1 warning in 1.76s`.
- **HTTP:** CA-01 a CA-10 e TELA `PASSOU`; subida manual API, TELA e DOCS `PASSOU`.
- **Processos:** nenhum uvicorn restante na inspeção de processos.
- **Gate:** [x] instalação limpa; [x] suíte; [x] dez CA mais TELA; [x] subida manual três endpoints; [x] nenhum processo do servidor restante.
- **Resultado:** APROVADO.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 32/32 |
| Critérios de aceite verificados via HTTP | 10/10 (mais TELA) |
| Ajustes manuais | nenhum |
| Pendências | nenhuma |
