# Log de execução

| Campo | Valor |
|---|---|
| Agente | Claude Code (subagente) |
| Modelo | claude-opus-5-5 |
| Início | 2026-10-23 17:36 (America/Sao_Paulo) |
| Pedido usado | `PEDIDO.md` na raiz (o prompt cita "PEDIDO.md") |

## Prompt de entrada

> Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

## Etapa 0 · Preparação

- **Início:** 17:36
- **Ambiente:** `python --version` → `Python 3.11.0` (atende 3.11+).
- **Pastas:** `gerado/` e `evidencias/` criadas.
- **Referências lidas:** `skills/fabrica/referencias/regras-transversais.md`, `skills/fabrica/referencias/stack-padrao.md`, `skills/fabrica/referencias/modelo-log.md`.
- **Fim:** 17:36

## Etapa 1 · Concepção

- **Início:** 17:37 (aprox.)
- **Artefatos:** `gerado/docs/PRD.md` (50 linhas de itens)
- **Decisões e premissas:**
  - PR-01 fuso America/Sao_Paulo; "hoje" é a data civil nesse fuso.
  - PR-02 datas de empréstimo são datas de calendário, sem hora (o pedido fala só em dias).
  - PR-03 cadastro = criar, listar, consultar.
  - PR-04 e-mail identifica a pessoa sem diferenciar caixa; formato simples.
  - PR-05 textos obrigatórios, não vazios, até 200 caracteres.
  - PR-06 retirada e devolução usam o dia do registro.
  - PR-07 relatório mostra os 3 tipos, com zero.
  - PR-08 ordenações das listagens.
  - PR-09 equipamento em MANUTENCAO permanece assim (saída não pedida).
  - RF-08 (listar empréstimos) foi acrescentado porque a tela precisa mostrar empréstimos em aberto para "devolver"; deriva de "registrar devolução" + "tela para devolver".
- **Cobertura do pedido:**

  | Trecho do pedido | Códigos |
  |---|---|
  | "ninguém sabe com quem está. Já perdemos equipamento" (problema) | Problema, RF-03, RF-08 |
  | Cadastro com patrimônio `EQ-0000`, tipo e descrição | RF-01, RN-01, PR-03, PR-05 |
  | Tipos `NOTEBOOK`, `PROJETOR`, `HEADSET` | Entidades, RF-01 |
  | Situação `DISPONIVEL`, `EMPRESTADO`, `MANUTENCAO` | Entidades, RF-02, RN-07, RN-09 |
  | Começa com 8 equipamentos (3/2/3, um headset em manutenção) | RF-12 |
  | Empréstimo: equipamento, pessoa (nome e e-mail), retirada (dia do registro), data prevista | RF-03, RN-03, PR-02, PR-06 |
  | Só `DISPONIVEL` pode ser emprestado | RN-02 |
  | Prazo máximo 14 / 3 dias contados da retirada | RN-04 |
  | Data prevista não anterior à retirada | RN-05 |
  | Máximo 2 empréstimos em aberto por e-mail | RN-06, PR-04 |
  | Status `ABERTO` / `DEVOLVIDO` | Entidades, RN-07, RN-08 |
  | Devolução registra data e encerra | RF-04, RN-08, RN-10 |
  | Defeito → `MANUTENCAO`, senão `DISPONIVEL` | RN-09 |
  | Disponíveis com filtro opcional por tipo | RF-05 |
  | Atrasados com dias de atraso | RF-06, RN-11 |
  | Relatório mensal por tipo (pela data de retirada) | RF-07, RN-12, PR-07 |
  | API REST para todas as operações | RF-09 |
  | Tela web para emprestar, devolver e ver atrasados | RF-10 |
  | Banco local, sem login | RF-11, Fora de escopo |
  | CA-01 a CA-10 | Seção Critérios de aceite do PRD |

- **Lacunas comuns:**

  | Item | Resolução |
  |---|---|
  | Fuso horário e formato de data | PR-01, PR-02 |
  | Bordas de limites | RN-04 (inclusivo), RN-05 (prazo 0 aceito), RN-06 (3º recusado), RN-11 (mínimo 1) |
  | O que "cadastro" cobre | PR-03 |
  | Unicidade de nomes ou identificadores | RN-01 (patrimônio único) |
  | Formato e validação de campos | RN-01, PR-04, PR-05 |
  | Registros relacionados quando um muda de status | RN-07, RN-09 (equipamento acompanha o empréstimo), PR-09 |
  | Definição de período em consultas e relatórios | RN-11 ("hoje" = data civil, PR-01), RN-12 (mês civil) |
  | Arredondamento e unidade de resultados calculados | RN-11 (dias inteiros de calendário), RN-12 (contagem inteira) |
  | Ordenação de listagens | PR-08 |

- **Gate:**
  - [x] `gerado/docs/PRD.md` existe com até 60 linhas de itens (50).
  - [x] Todo trecho do pedido aparece na tabela de cobertura com pelo menos um código.
  - [x] Cada item da lista de lacunas comuns tem uma linha no log.
  - [x] Toda `RN` com limite tem número e borda explícitos (RN-04, RN-05, RN-06, RN-11).
  - [x] Todo `CA-xx` do pedido está no PRD com código original, cenário, resultado e `RF`/`RN`.
  - [x] A seção "Fora de escopo" existe.
  - [x] Nenhuma linguagem, framework, produto de banco, formato de dado, endpoint ou tabela no PRD ("EQ-0000", "API REST", "banco local" são termos do próprio pedido).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 17:38 (aprox.)

## Etapa 2 · Especificação

- **Início:** 17:38 (aprox.)
- **Artefatos:** `gerado/docs/SPEC.md`
- **Decisões e premissas:**
  - Datas de empréstimo como data de calendário `YYYY-MM-DD` (PR-02). A regra transversal pede "ISO 8601 com offset" e "no banco, UTC"; ela trata de horários. Como o domínio só tem dias, a data é a civil de America/Sao_Paulo e é gravada sem conversão. O único carimbo com hora (`criado_em`) vai em UTC.
  - Disponíveis (RF-05) atendidos por `GET /api/equipamentos?situacao=DISPONIVEL&tipo=...`, sem endpoint separado.
  - RN-06 (limite por pessoa) e RN-04/RN-05 (prazo) retornam 422 (regra violada); equipamento indisponível e empréstimo já devolvido retornam 409 (conflito com estado existente).
  - Índice único parcial `ux_emprestimo_aberto_por_equipamento` como defesa extra contra dois empréstimos abertos no mesmo equipamento.
  - Relatório em `/api/relatorios/emprestimos-por-tipo?mes=YYYY-MM`.
- **Gate:**
  - [x] `gerado/docs/SPEC.md` existe com as seções do modelo (Modelo de dados, Carga inicial, Endpoints, Regras de negócio, Tela, Rastreabilidade, Plano de testes).
  - [x] Todo `RF-xx` (RF-01 a RF-12) aparece na rastreabilidade com endpoint, tela ou carga inicial.
  - [x] Todo `RN-xx` (RN-01 a RN-12) aparece com função de domínio e código de erro (ou "—" quando a regra não recusa nada).
  - [x] Todo endpoint tem método, caminho, entrada, saída de sucesso e erros.
  - [x] Todo `CA-xx` (CA-01 a CA-10) tem teste `test_ca_XX_...` no plano.
  - [x] Toda `RN` com limite numérico tem teste de borda: RN-04 (notebook 13/14/15, projetor 2/3/4, headset 3/4), RN-05 (−1/0), RN-06 (2º/3º), RN-11 (0/1/3 dias).
  - [x] DDL completo, só tipos SQLite (`INTEGER`, `TEXT`).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 17:40 (aprox.)

## Etapa 3 · Construção

- **Início:** 17:40 (aprox.)
- **Artefatos:** `gerado/app/` (banco, dominio/equipamentos.py, dominio/emprestimos.py, repositorio/*, rotas/equipamentos.py, rotas/emprestimos.py, rotas/relatorios.py, estatico/index.html), `gerado/tests/test_equipamentos.py`, `gerado/tests/test_emprestimos.py`, `gerado/tests/test_relatorio.py`, `gerado/verificacao/verificar_ca.py`, `gerado/README.md`, `gerado/.gitignore`
- **Decisões e premissas:**
  - Modelo copiado de `skills/construcao/modelo-projeto/`; `.venv` novo; os 2 testes do modelo passaram antes de qualquer mudança (`2 passed`).
  - Testes escritos antes do código, mas em lote (os 3 arquivos de teste de uma vez, depois a implementação), não linha a linha do plano. Antes da implementação: `41 failed, 2 passed`. Depois: `43 passed`.
  - Testes extras além do plano: `test_rf_12_carga_inicial_idempotente`, `test_rf_01_validacao_entrada`, `test_rn_11_atrasados_ordenados_por_maior_atraso`, `test_erro_devolucao_sem_corpo_assume_sem_defeito`.
  - Textos de entrada com `StringConstraints(strip_whitespace=True, min_length=1, max_length=200)`; nome só com espaços é recusado.
  - `intervalo_do_mes` limita o ano a 1..9998 para evitar `ValueError` (erro 500) com `date(10000, 1, 1)`.
  - Nenhuma dependência adicionada.
  - `verificar_ca.py` executado uma vez como ensaio (11/11); a função `resumo` foi ajustada para registrar os campos conferidos (status, situação) em vez de cortar o JSON em 160 caracteres.
- **Gate:**
  - [x] `PY -m pip install -r requirements.txt` funciona num `.venv` novo.
  - [x] `PY -m pytest -q` passa: `43 passed, 1 warning` (aviso de depreciação do starlette/anyio, sem relação com o código).
  - [x] Existe `test_ca_XX_...` para CA-01 a CA-10.
  - [x] Teste de borda para cada RN com limite: RN-04 (6 testes + CA-04/CA-05), RN-05 (2), RN-06 (3 + CA-06), RN-11 (4 + CA-09).
  - [x] Todo endpoint da SPEC implementado (8); nenhum fora da SPEC (além de `/api/saude` e `/` do modelo).
  - [x] Nenhum `datetime.now()` fora de `app/relogio.py`.
  - [x] `verificacao/verificar_ca.py` tem um bloco por CA-xx (10) mais TELA.
  - [x] `gerado/README.md` existe com os comandos.
- **Problemas e correções:** nenhum teste falhou após a implementação.
- **Gate:** APROVADO
- **Fim:** 17:46 (aprox.; ensaio do verificar_ca às 17:45:37)

## Etapa 4 · Revisão de qualidade

- **Início:** 17:46 (aprox.)
- **Artefatos:** `evidencias/revisao.md`; correções em `app/rotas/equipamentos.py`, `app/rotas/emprestimos.py`, `app/rotas/relatorios.py`; testes novos em `tests/test_emprestimos.py` e `tests/test_relatorio.py`; SPEC ajustada (seção Formatos e entrada de `POST /api/emprestimos`) para registrar os limites de id e o formato estrito de data.
- **Decisões e premissas:** a checagem "abre sem erro de JavaScript" foi feita por análise estática (IDs, `node --check`) e chamadas HTTP aos endpoints da tela; o navegador embutido é compartilhado com execuções paralelas e trocou para a aplicação de outra execução no meio do teste, então nenhuma ação foi feita nele além de preencher campos.
- **Gate:**
  - [x] `evidencias/revisao.md` existe com a tabela de achados (7 achados: 1 alto, 2 médios, 4 baixos).
  - [x] Nenhum achado alto ou médio com status diferente de `CORRIGIDO`.
  - [x] `PY -m pytest -q` passa depois das correções: `46 passed, 1 warning`.
- **Problemas e correções:** achado 1 (HTTP 500 com id acima de 2^63−1), achado 2 (data aceitava timestamp numérico), achado 3 (mês aceitava dígitos Unicode). Todos corrigidos com teste.
- **Gate:** APROVADO
- **Fim:** 17:52 (aprox.)

## Etapa 5 · Revisão de segurança

- **Início:** 17:52 (aprox.)
- **Artefatos:** `gerado/tests/test_seguranca.py` (9 testes), `evidencias/seguranca.md`; correções em `app/repositorio/equipamentos.py`, `app/repositorio/emprestimos.py`, `app/main.py`; `gerado/.gitignore`.
- **Decisões e premissas:**
  - `pip-audit` rodou (havia rede) e apontou 8 vulnerabilidades em `starlette 0.41.3` (transitiva de `fastapi==0.115.6`, fixada pela stack padrão) e 1 em `pytest 8.3.4`. Em vez de trocar as versões da stack, foi feita análise de aplicabilidade: só a CVE-2025-62727 (DoS por `Range` em `FileResponse`) atingia o código, e foi mitigada servindo a tela com `HTMLResponse`. As demais tratam de recursos não usados.
  - O `grep` de SQL acusou f-strings com fragmentos constantes; mesmo sem risco real, as consultas foram reescritas como constantes para a varredura sair limpa.
  - Não há repositório git na pasta de trabalho; o `.gitignore` foi criado em `gerado/`.
- **Gate:**
  - [x] `tests/test_seguranca.py` existe e passa (`9 passed`).
  - [x] `evidencias/seguranca.md` existe com todos os itens do checklist preenchidos.
  - [x] Nenhum achado alto ou médio aberto (S2 médio corrigido; S1, S3, S4 baixos).
  - [x] `PY -m pytest -q` passa: `55 passed, 1 warning`.
- **Problemas e correções:** S1 (SQL com f-string de constantes) e S2 (CVE-2025-62727 aplicável à tela) corrigidos.
- **Gate:** APROVADO
- **Fim:** 17:58 (aprox.)

## Etapa 6 · Verificação

- **Início:** 17:58
- **Artefatos:** `evidencias/criterios-aceite.md`
- **Passos e resultados:**
  1. Instalação limpa: `.venv/`, `dados/`, `.pytest_cache/` e `__pycache__/` apagados; `python -m venv .venv` e `PY -m pip install -r requirements.txt` → sucesso (código de saída 0).
  2. `PY -m pytest -q` → `55 passed, 1 warning`.
  3. `PY verificacao/verificar_ca.py` → código de saída 0; arquivo com TELA e CA-01 a CA-10, `11/11 aprovados`, todos `PASSOU`. CA-09 usa dois servidores: `APP_AGORA=2030-01-07T09:00-03:00` para criar o empréstimo com prevista 2030-01-07 (e confirmar que ainda não está atrasado) e `APP_AGORA=2030-01-08T09:00-03:00` com o mesmo banco para ver 1 dia de atraso.
  4. Subida manual: `PY -m uvicorn app.main:app --port 59036` (porta livre; 8000 pode estar ocupada por execuções paralelas). `GET /api/saude` → `HTTP 200 {"status":"ok"}`; `GET /` → `HTTP 200`, `<title>Empréstimo de equipamentos</title>`; `GET /api/equipamentos` trouxe a carga inicial. Processo encerrado; nenhuma porta 59036 em escuta e nenhum processo `uvicorn` desta execução restante.
- **Gate:**
  - [x] Instalação num `.venv` novo funcionou.
  - [x] `PY -m pytest -q` passa (`55 passed`).
  - [x] `evidencias/criterios-aceite.md` existe com uma linha por CA-01..CA-10 e a linha TELA, todas `PASSOU`.
  - [x] A subida manual respondeu em `/api/saude` e `/`.
  - [x] Nenhum processo do servidor ficou rodando (inclui o servidor manual aberto na revisão de qualidade, encerrado naquela etapa).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 18:01

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 (todos na primeira tentativa) |
| Testes | 55/55 |
| Critérios de aceite verificados via HTTP | 10/10 (mais a linha TELA: 11/11) |
| Ajustes manuais | nenhum |
| Pendências | Equipamento em MANUTENCAO não tem como voltar a DISPONIVEL (não pedido; PR-09, fora de escopo). `starlette 0.41.3` da stack fixada mantém CVEs não aplicáveis ao código (S3). Interação da tela não foi exercitada num navegador (só análise estática + endpoints via HTTP). |
