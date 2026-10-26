# Log de execução

| Campo | Valor |
|---|---|
| Agente | Claude Code (subagente) |
| Modelo | claude-opus-5-5 |
| Início | 2026-10-26 07:26 |
| Pedido usado | `PEDIDO.md` na raiz da pasta de trabalho (único pedido; o prompt não cita outro arquivo além dele) |

## Prompt de entrada

> Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

## Etapa 0 · Preparação

- **Início:** 07:26
- **Ambiente:** `python --version` → `Python 3.11.0` (atende 3.11+). Node `v22.23.2` disponível para `node --check`.
- **Artefatos:** `gerado/`, `gerado/docs/`, `evidencias/`, este log.
- **Leituras:** `skills/fabrica/SKILL.md`, `referencias/regras-transversais.md`, `referencias/stack-padrao.md`, `referencias/modelo-log.md`, skills das seis etapas e o `modelo-projeto/`.
- **Fim:** 07:27

## Etapa 1 · Concepção

- **Início:** 07:27
- **Artefatos:** `gerado/docs/PRD.md`
- **Decisões e premissas:** PR-01 a PR-12 no PRD. Destaques: PR-03 (duração 1 a 1440 min, o pedido não limita); PR-06 (cancelada não é ativa, pode reinscrever); PR-07 (promoção da espera vale até o início, mesmo com inscrições fechadas); PR-08 (taxa vazia sem presença marcada); PR-09 (presença definitiva). Vagas ocupadas contam CONFIRMADA, PRESENTE e AUSENTE (RN-03, RN-13).
- **Cobertura do pedido:**

| Trecho do pedido | Códigos |
|---|---|
| "Sempre lota, alguém desiste e a vaga fica parada" (problema) | RF-07, RN-09 |
| "cadastrar as turmas" | RF-01, RF-02, PR-02 |
| "as pessoas se inscreverem" | RF-04, PR-11 |
| "lista de espera automática" | RN-03, RN-04, RF-07 |
| "saber quem compareceu" | RF-08, RF-10 |
| "Não precisa de login" | RF-13, Fora de escopo |
| Turma: título, data e hora de início, duração em minutos | RF-01, RN-02, PR-03, PR-04 |
| Modalidade `PRESENCIAL`, `ONLINE` | Entidades, RF-01 |
| Quantidade de vagas de 1 a 50 | RN-01 |
| "O sistema já começa com 3 turmas futuras" | RF-03 |
| Inscrição: turma, pessoa (nome e e-mail), situação e seus 5 valores | Entidades, RF-04, PR-05, PR-11 |
| "Se a turma tem vaga, nasce CONFIRMADA. Se está lotada, nasce ESPERA" | RN-03, RN-13 |
| "por ordem de chegada" | RN-04, PR-10 |
| "mesmo e-mail não pode ter duas inscrições ativas (CONFIRMADA ou ESPERA) na mesma turma" | RN-05, PR-05, PR-06 |
| "Inscrições fecham 24 horas antes do início" | RN-06 |
| "Pode cancelar até o início da turma" | RF-06, RN-07, RN-08 |
| "Quando uma CONFIRMADA é cancelada, a primeira da ESPERA passa a CONFIRMADA" | RF-07, RN-09, PR-07 |
| "Só depois do início da turma, e só para CONFIRMADA: marcar PRESENTE ou AUSENTE" | RF-08, RN-10, RN-11, PR-09 |
| "Turmas futuras com a quantidade de vagas restantes" | RF-09, RN-13, RN-14, PR-10 |
| "Taxa de presença: presentes ÷ (presentes + ausentes), em percentual" | RF-10, RN-12, PR-08 |
| "API REST para todas as operações" | RF-11 |
| "tela web simples para ver as turmas, se inscrever e ver os inscritos" | RF-12, RF-05, PR-12 |
| "Dados em banco local. Sem login." | RF-13 |
| CA-01 a CA-10 | Seção Critérios de aceite do PRD |

- **Lacunas comuns:**

| Item | Resolução |
|---|---|
| Fuso horário e formato de data | PR-01 |
| Bordas de limites | RN-01, RN-02 (inclusivos), RN-06 (≤ início − 24h aceita), RN-07 (< início), RN-10 (≥ início) |
| O que "cadastro" cobre | PR-02 |
| Unicidade de nomes ou identificadores | PR-04 (título repetido permitido), RN-05 (e-mail por turma) |
| Formato e validação de campos | PR-05, RN-01, RN-02 |
| Registros relacionados quando um muda de status | RN-09 (cancelamento promove a espera), PR-06 |
| Período em consultas e relatórios | RN-14 (turma futura = início depois de agora); relatório por turma, sem período |
| Arredondamento e unidade de resultados | RN-12 (percentual, 2 casas), PR-08 |
| Ordenação de listagens | PR-10, RN-04 |
| Trechos que se contradizem | Não se aplica: nenhum conflito encontrado. "Pode cancelar até o início" lido como antes do início, coerente com CA-06 (RN-07) |
| Interação entre duas regras no mesmo momento | PR-07 (promoção dentro da janela fechada); RN-08 + RN-09 (cancelar ESPERA não promove ninguém) |
| Datas de calendário sem horário | Não se aplica: todas as regras usam data e hora (início da turma, 24 horas) |

- **Gate:**
  - [x] `gerado/docs/PRD.md` existe com até 70 linhas de itens (contagem por script: 56).
  - [x] Todo trecho do pedido aparece na tabela de cobertura com pelo menos um código.
  - [x] Cada item da lista de lacunas comuns tem uma linha, com código ou "não se aplica" e motivo.
  - [x] Toda `RN` com limite tem número e borda explícitos (RN-01, RN-02, RN-06, RN-07, RN-10, RN-12, RN-13).
  - [x] Todo `CA-xx` do pedido está no PRD com código original, cenário, resultado e `RF`/`RN`.
  - [x] Seção "Fora de escopo" existe.
  - [x] Nenhuma linguagem, framework, produto de banco, formato de dado, endpoint ou tabela (grep sem ocorrências; "API REST" e "banco local" são termos do pedido).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 07:29

## Etapa 2 · Especificação

- **Início:** 07:29
- **Artefatos:** `gerado/docs/SPEC.md`
- **Decisões e premissas:**
  - Endpoints: `POST/GET /api/turmas`, `GET /api/turmas/{id}`, `GET /api/turmas/{id}/inscricoes`, `GET /api/turmas/{id}/relatorio-presenca`, `POST /api/inscricoes`, `POST /api/inscricoes/{id}/cancelar`, `POST /api/inscricoes/{id}/presenca`.
  - RN-01 e RN-02 (faixas de vagas e duração) validadas no domínio com código de negócio (`VAGAS_INVALIDAS`, `DURACAO_INVALIDA`, 422), com faixa larga no Pydantic só para evitar estouro. Motivo: o gate exige função de domínio e código de erro para toda RN; a regra transversal manda faixa como validação de formato do framework. Escolhi a que satisfaz o gate, mantendo o status 422.
  - Prazos (RN-06, RN-07, RN-10) → 422; estado (RN-05, RN-08, RN-11) → 409, conforme a lista de exemplos das regras transversais.
  - Ordem de chegada pelo `id` (o relógio fixo dos testes empata `criada_em`).
  - Índice único parcial `(turma_id, email) WHERE situacao IN ('CONFIRMADA','ESPERA')` como defesa extra de RN-05.
  - Cancelamento devolve `{inscricao, promovida}` para a promoção ficar visível (CA-03).
- **Gate:**
  - [x] `gerado/docs/SPEC.md` existe com as seções do modelo (modelo de dados, carga inicial, endpoints, regras, tela, rastreabilidade, plano de testes).
  - [x] RF-01 a RF-13 na tabela de rastreabilidade.
  - [x] RN-01 a RN-14 com função de domínio e erro (cálculos sem erro marcados "—").
  - [x] Todo endpoint com método, caminho, entrada, saída e erros.
  - [x] CA-01 a CA-10 com `test_ca_XX_...` no plano.
  - [x] RN com limite numérico com teste de borda: RN-01, RN-02, RN-06, RN-07, RN-10 (RN-12/RN-13 com teste de cálculo).
  - [x] DDL completo, só tipos SQLite.
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 07:31

## Etapa 3 · Construção

- **Início:** 07:31
- **Artefatos:** `gerado/app/` (banco, dominio/turmas, dominio/inscricoes, dominio/relatorio, repositorio/turmas, repositorio/inscricoes, rotas/modelos, rotas/turmas, rotas/inscricoes, estatico/index.html), `gerado/tests/apoio.py`, `gerado/tests/test_criterios.py`, `gerado/tests/test_regras.py`, `gerado/verificacao/verificar_ca.py`, `gerado/README.md`.
- **Decisões e premissas:**
  - Modelo copiado de `skills/construcao/modelo-projeto/` para `gerado/` (inclusive `.gitignore`), mantendo `gerado/docs/`.
  - `.venv` novo + `pip install -r requirements.txt` sem erro; testes do modelo antes de qualquer mudança: `12 passed, 1 warning`.
  - Nenhuma dependência adicionada.
  - Funções de apoio dos testes em `tests/apoio.py` (cria turma e inscrição pela API).
  - `GET /api/saude` continua existindo: vem do modelo e é usado pelo harness; não está na SPEC, mas é infraestrutura do modelo, não funcionalidade.
- **Rodada de testes antes da implementação:** `59 failed, 12 passed, 1 warning in 5.33s` (os 12 que passaram são os testes do modelo).
- **Rodada final:** `71 passed, 1 warning in 9.62s`.
- **Gate:**
  - [x] `PY -m pip install -r requirements.txt` funciona num `.venv` novo.
  - [x] Rodada antes da implementação registrada com falhas (59 failed).
  - [x] `PY -m pytest -q` passa: `71 passed, 1 warning`.
  - [x] `test_ca_01` a `test_ca_10` existem (em `tests/test_criterios.py`).
  - [x] Teste de borda para RN-01, RN-02, RN-06, RN-07, RN-10 (e cálculo de RN-12, RN-13).
  - [x] Os 8 endpoints da SPEC implementados; nenhum outro além de `/api/saude` (modelo), `/`, `/docs`, `/openapi.json`.
  - [x] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py` (grep).
  - [x] `verificacao/verificar_ca.py` com um bloco por CA-01 a CA-10, mais TELA; ensaio: 11/11 PASSOU.
  - [x] `gerado/README.md` com os comandos.
- **Problemas e correções:**
  - Um comando de shell com vários heredocs aninhados falhou por aspas (`unexpected EOF`) e não gravou as rotas; os arquivos foram reescritos com a ferramenta de escrita. Sem efeito no sistema.
  - `tests/apoio.py`: `email or padrão` trocava e-mail vazio pelo padrão e tornaria o teste de e-mail vazio falso-positivo; corrigido para `padrão if email is None else email` antes da primeira rodada.
- **Gate:** APROVADO
- **Fim:** 07:40

## Etapa 4 · Revisão de qualidade

- **Início:** 07:40
- **Artefatos:** `evidencias/revisao.md`, `gerado/.tmp/sonda.py`, `gerado/.tmp/sonda_tela.py`
- **Ponto de partida:** `71 passed, 1 warning in 9.62s`
- **Achados:** 1 médio (inteiros do corpo aceitavam `true`, `1.5`, `"10"` por coerção), corrigido com `strict=True` e 9 casos de teste novos; 5 baixos aceitos com motivo.
- **Gate:**
  - [x] `evidencias/revisao.md` existe com a tabela de achados.
  - [x] Nenhum achado alto ou médio com status diferente de `CORRIGIDO`.
  - [x] `PY -m pytest -q` depois das correções: `80 passed, 1 warning in 7.62s`.
- **Problemas e correções:** a sonda falhou na primeira execução por `ModuleNotFoundError: app` (rodada de `.tmp/`); repetida com `PYTHONPATH=.`.
- **Gate:** APROVADO
- **Fim:** 07:43

## Etapa 5 · Revisão de segurança

- **Início:** 07:43
- **Artefatos:** `gerado/tests/test_seguranca.py`, `evidencias/seguranca.md`, `gerado/.tmp/pip-audit.json`
- **Decisões:** `pip-audit` instalado só no `.venv`. Observação: o `pip-audit` cria por conta própria um venv temporário na pasta TEMP do sistema (aviso `Actual environment location may have moved`), fora da pasta de trabalho; não há opção no comando prescrito para evitar isso.
- **Gate:**
  - [x] `tests/test_seguranca.py` existe e passa (15 passed).
  - [x] `evidencias/seguranca.md` com todos os itens do checklist preenchidos.
  - [x] Nenhum achado alto ou médio aberto.
  - [x] `PY -m pytest -q`: `95 passed, 1 warning in 11.56s`.
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 07:47

## Etapa 6 · Verificação

- **Início:** 07:47
- **Artefatos:** `evidencias/criterios-aceite.md`, `evidencias/subida-manual.md`
- **Instalação limpa:** `.venv/` e `dados/` apagados; `python -m venv .venv` e `PY -m pip install -r requirements.txt` → sucesso (saída 0).
- **Testes:** `95 passed, 1 warning in 10.43s`
- **Critérios de aceite via HTTP:** `PY verificacao/verificar_ca.py` → 11/11 PASSOU (CA-01 a CA-10 + TELA), saída 0. CA-06, CA-08 e CA-10 rodaram num segundo servidor com `APP_AGORA=2030-01-10T10:00:00-03:00` e o mesmo banco.
- **Subida manual:** `PY verificacao/subida_manual.py` → API, TELA e DOCS PASSOU, saída 0.
- **Processos:** consulta a `Win32_Process` por uvicorn desta pasta → nenhum processo restante.
- **Gate:**
  - [x] Instalação num `.venv` novo funcionou.
  - [x] `PY -m pytest -q` passa (95 passed).
  - [x] `evidencias/criterios-aceite.md` com CA-01 a CA-10 e TELA, todas `PASSOU`.
  - [x] `evidencias/subida-manual.md` com as três linhas `PASSOU`.
  - [x] Nenhum processo do servidor ficou rodando.
- **Problemas e correções:** nenhum. Observação: `subida-manual.md` sai com o título "Critérios de aceite verificados via HTTP" porque `Verificacao.salvar` do harness do modelo usa título fixo; não alterado.
- **Gate:** APROVADO
- **Fim:** 07:50

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 95/95 |
| Critérios de aceite verificados via HTTP | 10/10 (mais TELA) |
| Ajustes manuais | nenhum |
| Pendências | nenhuma |

Fim da execução: 2026-10-26 07:50.
