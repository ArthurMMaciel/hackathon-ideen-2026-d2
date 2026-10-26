# Rodada 02 · Resultados consolidados

| Campo | Valor |
|---|---|
| Data | 26/10/2026, de 07:26 a 07:51 |
| Versão das skills | v2, commit `0124d04` (melhorias M1 a M12 da rodada 01) |
| Agente | Claude Code, subagentes com contexto limpo, em paralelo |
| Modelo | `claude-opus-5-5` |
| Prompt | o da banca, sem alteração |

## Quadro geral

| Pedido | Gates | Testes | CAs via HTTP | Ajuste manual | Pendências | Tempo | Chamadas de ferramenta |
|---|---|---|---|---|---|---|---|
| [P00](P00/) Reserva de salas | 6/6 | 89/89 | 10/10 | nenhum | nenhuma | 25 min | 56 |
| [P01](P01/) Empréstimo de equipamentos | 6/6 | 80/80 | 10/10 | nenhum | nenhuma | 23 min | 58 |
| [P02](P02/) Reembolso de despesas | 6/6 | 75/75 | 10/10 | nenhum | nenhuma | 22 min | 47 |
| [P03](P03/) Inscrição em treinamentos | 6/6 | 95/95 | 10/10 | nenhum | nenhuma | 24 min | 52 |
| [P04](P04/) Férias da equipe | 6/6 | 71/71 | 10/10 | nenhum | nenhuma | 22 min | 48 |
| [P05](P05/) Chamados com prazo | 6/6 | 87/87 | 10/10 | nenhum | nenhuma | 24 min | 46 |

## Comparação com a rodada 01

| Indicador | Rodada 01 (v1) | Rodada 02 (v2) |
|---|---|---|
| Gates | 36/36 | 36/36 |
| Testes | 390 | 497 |
| CAs via HTTP | 60/60 | 60/60 |
| Execuções com pendência | 6 de 6 (CVEs da stack fixada) | 0 de 6 |
| Execuções que acharam HTTP 500 com valores extremos | 6 de 6 | 0 de 6 |
| Execuções que corrigiram a vulnerabilidade do `FileResponse` | 6 de 6 | 0 |
| `pip-audit` | 8 a 16 vulnerabilidades por execução | 0 vulnerabilidades |
| Testes escritos antes do código, com evidência no log | 0 de 6 | 6 de 6 |
| Horários do log | estimados em 5 de 6 | lidos do relógio (alguns "Fim" corrigidos depois da leitura) |
| Datas sem horário | improvisadas (P01, P02, P04) | cobertas pela regra nova |
| Carga inicial com datas relativas | improvisada (P02, P03, P05) | coberta por `carga_inicial(conn, agora)` |
| Tempo médio por execução | ~25 min | ~23 min |
| Chamadas de ferramenta (média) | ~66 | ~51 |

## Leitura crítica

- **As melhorias atacaram as causas certas.** Os seis problemas que apareceram em todas as execuções da rodada 01 sumiram dos relatos da rodada 02. A revisão de segurança deixou de apagar incêndio do próprio modelo.
- **O pacote ficou mais barato e previsível.** Cerca de 25% menos chamadas de ferramenta, nenhuma pendência e todos os gates na primeira conferência.
- **A v2 introduziu fricções novas, todas menores e repetidas:** `/api/saude` fora da lista de endpoints permitidos (todas as execuções), `pip-audit` criando ambiente fora da pasta (todas), SQL da carga inicial em `banco.py`, título errado em `subida-manual.md`, aviso do starlette não filtrado.
- **A regra 409 ou 422 melhorou, mas um exemplo contradiz o teste de decisão** em regras que dependem de prazo ou saldo guardado (P03, P04, P05). Falha da IA ao escrever os exemplos.
- **Ainda depende da disciplina do agente:** horários "Fim" escritos antes da leitura do relógio em quatro execuções, corrigidos pelos próprios agentes.

## Recorrência dos problemas da rodada 02

| # | Problema | P01 | P02 | P03 | P04 | P05 | Origem |
|---|---|---|---|---|---|---|---|
| 1 | `/api/saude` não isento no gate da construção | x | x | x | x | x | `construcao` |
| 2 | `pip-audit` cria ambiente fora da pasta de trabalho | x | x | x | x | x | `revisao-seguranca` |
| 3 | SQL da carga inicial em `banco.py` | x | x | x | | x | modelo |
| 4 | Exemplo "prazo → 422" contradiz o teste de decisão | | | x | x | x | regras transversais |
| 5 | "Fim" da etapa escrito antes de ler o relógio | x | x | x | x | x | modelo de log |
| 6 | `subida-manual.md` com título de critérios de aceite | | x | x | | x | harness |
| 7 | Grep de SQL não pega constantes de módulo | x | x | x | | | `revisao-seguranca` |
| 8 | Aviso do starlette não filtrado no `pytest.ini` | x | x | | x | | modelo |
| 9 | Precedência quando duas regras falham juntas | x | x | | | x | regras transversais |
| 10 | Falta tipo `Mes` | x | | | x | | modelo |
| 11 | Mensagens de validação do framework em inglês | x | | | x | | modelo |
| 12 | Tipos aceitam tipo JSON errado (`true`, `1.5`) | | x | x | | | modelo |

## Melhorias candidatas para uma rodada 03

Nenhuma bloqueia a entrega. Todas são ajustes de uma ou poucas linhas:

1. Isentar `/api/saude`, `/redoc` e `/docs/oauth2-redirect` no gate da construção.
2. Rodar `pip-audit` sobre o ambiente instalado (`PY -m pip_audit`, sem `-r`), que não cria ambiente temporário.
3. Mover a carga inicial para `app/repositorio/carga_inicial.py`, chamada por `banco.iniciar`.
4. Corrigir os exemplos da regra 409 ou 422: prazo calculado sobre dado guardado (data de resolução, início da turma, saldo) é 409; só limites fixos da requisição são 422. Definir a precedência: formato, depois 404, depois 409, depois 422.
5. Modelo de log com "Fim" preenchido só depois do comando do relógio.
6. Título configurável em `Verificacao.salvar`.
7. Grep de SQL também em constantes de módulo.
8. Filtrar o aviso do starlette pelo texto.
9. Tipos `Mes` e inteiros estritos em `app/tipos.py`.
10. `DataHora` descartando fração de segundo, para o valor validado ser o mesmo gravado (achado do P00).
11. Função `comFuso()` na tela para montar horário com offset a partir de `datetime-local`, e "hoje" da tela vindo da API.
