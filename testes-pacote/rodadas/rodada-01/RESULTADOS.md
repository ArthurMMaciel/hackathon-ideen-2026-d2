# Rodada 01 · Resultados consolidados

| Campo | Valor |
|---|---|
| Data | 23/10/2026 |
| Versão das skills | commit `31c3c44` (P00 rodou com o harness de porta fixa, anterior a esse commit) |
| Agente | Claude Code, subagentes com contexto limpo, em paralelo |
| Modelo | `claude-opus-5-5` |
| Prompt | o da banca, sem alteração |

## Quadro geral

| Pedido | Gates | Testes | CAs via HTTP | Ajuste manual | Tempo | Voltas a etapa anterior |
|---|---|---|---|---|---|---|
| [P00](P00/) Reserva de salas | 6/6 | 83/83 | 10/10 | nenhum | ~26 min | sim (revisão → concepção e especificação) |
| [P01](P01/) Empréstimo de equipamentos | 6/6 | 55/55 | 10/10 | nenhum | ~26 min | sim (revisão → especificação) |
| [P02](P02/) Reembolso de despesas | 6/6 | 36/36 | 10/10 | nenhum | ~25 min | sim (revisão → especificação) |
| [P03](P03/) Inscrição em treinamentos | 6/6 | 59/59 | 10/10 | nenhum | ~26 min | sim (revisão → especificação) |
| [P04](P04/) Férias da equipe | 6/6 | 68/68 | 10/10 | nenhum | ~24 min | não |
| [P05](P05/) Chamados com prazo | 6/6 | 89/89 | 10/10 | nenhum | ~24 min | sim (construção → especificação) |
| **Total** | **36/36** | **390/390** | **60/60** | **nenhum** | | |

## Leitura crítica

- **O pacote generalizou.** Seis domínios, nenhum ajuste manual, todos os critérios verificados contra o servidor real.
- **Os gates trabalharam de verdade.** Cinco execuções voltaram a uma etapa anterior. A revisão achou HTTP 500 reais em cinco das seis, e a construção do P05 pegou um bug de regra de negócio pelos testes de transição.
- **Parte do trabalho das revisões foi apagar incêndio causado pelo próprio pacote.** As seis execuções gastaram tempo corrigindo o mesmo defeito do modelo de projeto (`FileResponse` vulnerável) e o mesmo HTTP 500 (id sem limite). São falhas da IA ao escrever o modelo, registradas no diário.
- **O "teste antes do código, um por vez" não foi seguido por nenhum agente.** Todos escreveram os testes em lote. A instrução está mal desenhada e o gate não consegue verificá-la.
- **Disciplina de processo:** horários do log estimados em cinco execuções; arquivos temporários fora da pasta de trabalho em quatro (todos apagados em seguida).
- **A tela não foi executada num navegador real em nenhuma execução.** Só verificação estática e HTTP.

## Recorrência dos problemas

| # | Problema | P00 | P01 | P02 | P03 | P04 | P05 | Origem |
|---|---|---|---|---|---|---|---|---|
| 1 | `FileResponse` do modelo exposto à CVE-2025-62727 | x | x | x | x | x | x | modelo de projeto |
| 2 | HTTP 500 com id gigante ou data extrema | x | x | x | x | x | x | modelo e regras transversais |
| 3 | Domínio importa FastAPI via `app/erros.py` | x | x | x | x | x | x | modelo de projeto |
| 4 | TDD um a um ignorado (testes em lote) | x | x | x | x | x | x | `construcao` |
| 5 | `.gitignore` "do repositório" sem repositório | x | x | x | x | x | x | `revisao-seguranca` |
| 6 | Stack fixada com CVEs e sem regra para elas | x | x | x | x | x | x | stack e `revisao-seguranca` |
| 7 | Falso positivo no grep de SQL | x | x | | | x | x | `revisao-seguranca` |
| 8 | Horários do log estimados | x | x | x | | x | x | `fabrica` |
| 9 | Escrita fora da pasta de trabalho | x | x | x | x | x | | `fabrica` |
| 10 | Datas sem horário não previstas | | x | x | | x | | regras transversais |
| 11 | Carga inicial fora do relógio injetável | | | x | x | | x | modelo de projeto |
| 12 | 409 ou 422 para estado inválido | x | x | x | | | x | regras transversais |
| 13 | Acentos quebrados no console do Windows | | x | x | x | | x | harness |
| 14 | Sem receita para subir e derrubar o servidor | x | | x | | | x | `verificacao` |
| 15 | Evidência do CA cortada ou fora de ordem | x | x | | x | | | harness |
| 16 | `datetime.now()` no harness contra o gate | | x | x | x | | x | `construcao` |
| 17 | Sem método para conferir a tela | | x | | x | x | x | `revisao` |
| 18 | Pedido contradiz regra transversal ou a si mesmo | | | x | | x | | `concepcao` |

## Melhorias propostas para a rodada 02

Ordenadas pelo impacto: primeiro o que se repetiu em todas as execuções e o que pode quebrar o pedido oculto.

| # | Melhoria | Resolve | Onde |
|---|---|---|---|
| M1 | Atualizar a stack para versões sem CVE conhecida, fixando também as dependências transitivas, verificado com `pip-audit` limpo | 1, 6 | `stack-padrao.md`, modelo |
| M2 | Tela servida com `HTMLResponse` no modelo | 1 | modelo |
| M3 | Tipos prontos no modelo: id limitado, data e hora com ano entre 2000 e 2100, data sem horário estrita (`AAAA-MM-DD`), texto com `strip` e tamanho máximo | 2, 10 | modelo, `construcao` |
| M4 | Exceções de negócio num módulo puro (`app/dominio/erros.py`); tradução para HTTP fica em `app/main.py` | 3 | modelo |
| M5 | Carga inicial recebe `agora`; o ciclo de vida usa o relógio substituído nos testes e `APP_AGORA` no servidor | 11 | modelo |
| M6 | Regras novas: o pedido prevalece sobre as regras transversais; seção de datas sem horário; teste de decisão 409 ou 422 ("a mesma requisição seria aceita com outro estado no banco? então 409") | 10, 12, 18 | `regras-transversais.md` |
| M7 | TDD em lote: escrever todos os testes do plano, rodar, registrar a contagem de falhas no log, implementar. O gate exige essa evidência | 4 | `construcao` |
| M8 | Log com horário lido do relógio a cada etapa (comando dado na skill); proibição explícita de escrever fora da pasta de trabalho, com temporários em `gerado/.tmp/` | 8, 9 | `fabrica` |
| M9 | Harness: saída UTF-8, linhas ordenadas por código, função para registrar só os campos conferidos; script pronto de subida manual que sobe, confere e derruba o servidor | 13, 14, 15 | modelo, `verificacao` |
| M10 | Ajustes de checklist: `gerado/.gitignore`; composição de SQL só com constantes é aceita; `datetime.now()` proibido só em `app/`; valores extremos obrigatórios na revisão; conferência da tela por IDs, `node --check` e HTTP | 5, 7, 16, 17 | `revisao`, `revisao-seguranca`, `construcao` |
| M11 | CSS padrão no modelo para a tela sair apresentável (pedido do participante) | | modelo |
| M12 | Lacunas novas na concepção: contradições no pedido e interação entre regras | 18 | `concepcao` |
