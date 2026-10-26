# Log de execução

| Campo | Valor |
|---|---|
| Agente | Claude Code (subagente) |
| Modelo | claude-opus-5-5 |
| Início | 2026-10-23 17:36 |
| Pedido usado | `PEDIDO.md` (raiz; citado no prompt) |

## Prompt de entrada

> Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

## Etapa 0 · Preparação

- **Início:** 17:36
- **Pedido:** `PEDIDO.md` na raiz, citado no prompt.
- **Ambiente:** `python --version` → `Python 3.11.0` (atende ≥ 3.11).
- **Pastas:** `gerado/` e `evidencias/` criadas.
- **Fim:** 17:36

## Etapa 1 · Concepção

- **Início:** 17:36
- **Artefatos:** `gerado/docs/PRD.md`
- **Decisões e premissas:**
  - PR-01 fuso America/Sao_Paulo; PR-02 cadastro = criar, listar, consultar.
  - PR-03 duração 1 a 1440 min (pedido não limita).
  - PR-04 e-mail sem diferenciar maiúsculas; PR-05 reinscrição após cancelar.
  - PR-06 cancelar ESPERA não promove; PR-07 promoção vale até o início.
  - PR-08 presença marcada uma vez; PR-09 definição de "futura" e ordenações.
  - PR-10 arredondamento e taxa vazia sem marcações; PR-11 carga inicial relativa à primeira inicialização.
  - PR-12 títulos/nomes repetíveis; fila sem limite.
  - "Fecham 24 horas antes" interpretado como borda fechada: exatamente 24 h antes já recusa (RN-08).
  - Ocupadas inclui PRESENTE e AUSENTE (RN-05), para a vaga não "reabrir" depois da marcação de presença.
- **Cobertura do pedido:**

  | Trecho do pedido | Códigos |
  |---|---|
  | "Sempre lota, alguém desiste e a vaga fica parada" (problema) | Problema, RN-10 |
  | "cadastrar as turmas" | RF-01, RF-02, PR-02 |
  | "as pessoas se inscreverem" | RF-04 |
  | "lista de espera automática" | RN-05, RN-06, RN-10 |
  | "saber quem compareceu" | RF-07, RF-09 |
  | "Não precisa de login" | RF-12, Fora de escopo |
  | Turma: título, data e hora de início, duração em minutos | RF-01, RN-02, RN-03, RN-04 |
  | Modalidade PRESENCIAL, ONLINE | RF-01, Entidades |
  | Vagas de 1 a 50 | RN-01 |
  | Começa com 3 turmas futuras | RF-03, PR-11 |
  | Inscrição: turma, pessoa (nome, e-mail), situação com 5 valores | RF-04, Entidades, RN-03 |
  | Com vaga nasce CONFIRMADA; lotada nasce ESPERA por ordem de chegada | RN-05, RN-06 |
  | Mesmo e-mail sem duas inscrições ativas na mesma turma | RN-07, PR-04, PR-05 |
  | Inscrições fecham 24 h antes do início | RN-08 |
  | Pode cancelar até o início | RF-06, RN-09 |
  | Cancelar CONFIRMADA promove a primeira da ESPERA | RN-10, PR-06, PR-07 |
  | Presença só depois do início e só para CONFIRMADA | RF-07, RN-11, PR-08 |
  | Turmas futuras com vagas restantes | RF-08, RN-13, PR-09 |
  | Taxa de presença presentes ÷ (presentes + ausentes) em % | RF-09, RN-12, PR-10 |
  | API REST para todas as operações | RF-10 |
  | Tela web: ver turmas, se inscrever, ver inscritos | RF-11 |
  | Dados em banco local, sem login | RF-12 |
  | CA-01 a CA-10 | Critérios de aceite do PRD |

- **Lacunas comuns:**

  | Item | Resolução |
  |---|---|
  | Fuso horário e formato de data | PR-01 |
  | Bordas de limites | RN-01, RN-02, RN-08 (24 h exatas recusam), RN-09 (no início recusa), RN-11 (no início aceita) |
  | O que "cadastro" cobre | PR-02 |
  | Unicidade de nomes ou identificadores | RN-07, PR-12 |
  | Formato e validação de campos | RN-03, RN-01, RN-02, PR-04 |
  | Registros relacionados quando um muda de status | RN-10, PR-06, PR-07, PR-08 |
  | Definição de período em consultas e relatórios | PR-09 (futura = início > agora); relatório é por turma, sem período |
  | Arredondamento e unidade de resultados calculados | RN-12, PR-10 |
  | Ordenação de listagens | PR-09 |

- **Gate:**
  - [x] `gerado/docs/PRD.md` existe com até 60 linhas de itens (55 linhas de itens).
  - [x] Todo trecho do pedido aparece na tabela de cobertura com pelo menos um código.
  - [x] Cada item da lista de lacunas comuns tem uma linha, com código.
  - [x] Toda `RN` com limite tem número e borda explícitos (RN-01, RN-02, RN-03, RN-08, RN-09, RN-11).
  - [x] Todo `CA-xx` do pedido está no PRD com código original, cenário, resultado e `RF`/`RN`.
  - [x] A seção "Fora de escopo" existe.
  - [x] Nenhuma linguagem, framework, produto de banco, formato de dado, endpoint ou tabela no PRD ("API REST" e "banco local" são termos do pedido).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 17:38

## Etapa 2 · Especificação

- **Início:** 17:38
- **Artefatos:** `gerado/docs/SPEC.md`
- **Decisões e premissas:**
  - 8 endpoints: `POST/GET /api/turmas`, `GET /api/turmas/{id}`, `POST/GET /api/turmas/{id}/inscricoes`, `POST /api/inscricoes/{id}/cancelar`, `POST /api/inscricoes/{id}/presenca`, `GET /api/turmas/{id}/taxa-presenca`.
  - Inscrição como sub-recurso da turma; cancelamento e presença como ações `POST .../{acao}`.
  - Índice único parcial `(turma_id, email) WHERE situacao IN ('CONFIRMADA','ESPERA')` como defesa extra de RN-07.
  - `posicao_espera` calculada na leitura (não gravada), para a fila nunca ficar inconsistente após cancelamentos.
  - Resposta do cancelamento traz `cancelada` e `promovida`, para CA-03 ser verificável numa só chamada.
  - Carga inicial com datas relativas ao relógio injetável (não ao relógio do sistema), para as turmas serem "futuras" também sob `APP_AGORA` e nos testes.
  - RN-01/02/03 validadas no modelo Pydantic (422 do framework), sem código de negócio próprio.
- **Gate:**
  - [x] `gerado/docs/SPEC.md` existe com as seções do modelo (modelo de dados, carga inicial, endpoints, regras, tela, rastreabilidade, plano de testes).
  - [x] Todo `RF-01`..`RF-12` aparece na rastreabilidade com endpoint, tela ou carga inicial.
  - [x] Todo `RN-01`..`RN-13` aparece com função de domínio (ou modelo Pydantic) e erro.
  - [x] Todo endpoint tem método, caminho, entrada, saída de sucesso e erros.
  - [x] Todo `CA-01`..`CA-10` tem teste `test_ca_XX_...` no plano.
  - [x] Toda `RN` com limite numérico (RN-01, RN-02, RN-03, RN-05, RN-08, RN-09, RN-11) tem teste de borda.
  - [x] DDL completo, só tipos SQLite (INTEGER, TEXT).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 17:40

## Etapa 3 · Construção

- **Início:** 17:40
- **Artefatos:** `gerado/app/` (dominio/turmas.py, dominio/inscricoes.py, dominio/relatorios.py, repositorio/turmas.py, repositorio/inscricoes.py, rotas/modelos.py, rotas/turmas.py, rotas/inscricoes.py, banco.py, main.py, estatico/index.html), `gerado/tests/` (apoio.py, test_criterios_aceite.py, test_regras.py), `gerado/verificacao/verificar_ca.py`, `gerado/README.md`, `gerado/.gitignore`
- **Decisões e premissas:**
  - Modelo copiado de `skills/construcao/modelo-projeto/`; `.venv` novo; `pip install -r requirements.txt` ok; 2 testes do modelo passaram antes de qualquer mudança.
  - `banco.iniciar` e `banco.carga_inicial` passaram a receber `agora`; `criar_app` usa o mesmo relógio da API (inclusive o substituto dos testes) para a carga inicial. Sem isso as 3 turmas "futuras" nasceriam no passado sob o relógio de teste (2030) ou com `APP_AGORA`.
  - Consultas SQL com subconsulta de ocupadas guardadas como constantes de texto fixo (sem f-string em `execute`).
  - Testes escritos antes do código, mas em lote (todo o plano da SPEC de uma vez): a primeira execução deu `46 failed, 2 passed` (rotas inexistentes, 404); depois da implementação, todos passaram. Não segui o ciclo "um teste por vez" literalmente.
  - Nenhuma dependência nova além do `requirements.txt` do modelo.
- **Gate:**
  - [x] `PY -m pip install -r requirements.txt` funciona num `.venv` novo.
  - [x] `PY -m pytest -q` passa: `48 passed, 1 warning` (aviso de depreciação do anyio dentro do starlette, não do código gerado).
  - [x] Existe teste `test_ca_XX_...` para cada CA-01..CA-10 (`tests/test_criterios_aceite.py`).
  - [x] Teste de borda para cada RN com limite (RN-01, RN-02, RN-03, RN-04, RN-05, RN-08, RN-09, RN-11) em `tests/test_regras.py`.
  - [x] Os 8 endpoints da SPEC implementados; nenhum endpoint de negócio fora da SPEC (`/api/saude`, `/` e `/docs`/`/openapi.json` vêm do modelo/framework).
  - [x] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py` (o único outro uso é em `verificacao/harness.py`, do modelo, só para carimbar a data do relatório).
  - [x] `verificacao/verificar_ca.py` tem um bloco por CA-01..CA-10, mais TELA; execução de fumaça: 11/11 PASSOU.
  - [x] `gerado/README.md` existe com os comandos.
- **Problemas e correções:** um comando de shell com vários heredocs aninhados falhou por erro de aspas antes de gravar `banco.py`/`main.py`/rotas; refeito com gravação direta dos arquivos. Sem impacto no sistema.
- **Gate:** APROVADO
- **Fim:** 17:47

## Etapa 4 · Revisão de qualidade

- **Início:** 17:47
- **Artefatos:** `evidencias/revisao.md`; correções em `gerado/app/rotas/modelos.py`, `gerado/app/rotas/turmas.py`, `gerado/app/rotas/inscricoes.py`, `gerado/tests/test_regras.py`, `gerado/docs/SPEC.md`
- **Decisões e premissas:**
  - Ponto de partida: `48 passed, 1 warning`.
  - Sondagem com entradas extremas encontrou dois 500 (id acima de 64 bits; ano 9999 com offset negativo).
  - **Volta à etapa 2:** SPEC ajustada (faixa de ids no caminho, ano do início de 2000 a 2999, textos sem espaços nas pontas, 2 testes novos no plano).
- **Gate:**
  - [x] `evidencias/revisao.md` existe com a tabela de achados (2 altos, 2 médios, 5 baixos).
  - [x] Nenhum achado alto ou médio com status diferente de `CORRIGIDO`.
  - [x] `PY -m pytest -q` passa depois das correções: `50 passed, 1 warning`.
- **Problemas e correções:** o painel de navegador não tinha aba livre (execuções em paralelo); a tela foi conferida por grep de IDs, `node --check` e `GET /` contra servidor real (porta 65226, encerrado em seguida).
- **Gate:** APROVADO
- **Fim:** 17:52

## Etapa 5 · Revisão de segurança

- **Início:** 17:52
- **Artefatos:** `gerado/tests/test_seguranca.py`, `evidencias/seguranca.md`; correção em `gerado/app/main.py`
- **Decisões e premissas:**
  - `pip-audit` rodou (com rede): 16 registros em starlette 0.41.3 e pytest 8.3.4. Só CVE-2025-62727 (Range no `FileResponse`) atinge código usado; mitigada trocando `FileResponse` por `HTMLResponse` na tela, sem mudar as versões fixadas pela stack.
  - Não atualizei fastapi/starlette: a stack padrão fixa `fastapi==0.115.6`, e as demais CVEs atingem recursos não usados (registrado como ACEITO, baixo).
  - `.gitignore` criado em `gerado/` (não há repositório git na pasta).
- **Gate:**
  - [x] `tests/test_seguranca.py` existe e passa (9 testes).
  - [x] `evidencias/seguranca.md` existe com todos os itens do checklist preenchidos.
  - [x] Nenhum achado alto ou médio aberto (S1 alto CORRIGIDO; S2–S4 baixos ACEITOS).
  - [x] `PY -m pytest -q` passa: `59 passed, 1 warning`.
- **Problemas e correções:** S1 corrigido na primeira tentativa.
- **Gate:** APROVADO
- **Fim:** 17:57

## Etapa 6 · Verificação

- **Início:** 17:57
- **Artefatos:** `evidencias/criterios-aceite.md`
- **Decisões e premissas:**
  - Instalação limpa: `.venv/`, `dados/`, `.pytest_cache` e `__pycache__` apagados; `python -m venv .venv` + `PY -m pip install -r requirements.txt` → código de saída 0.
  - `verificar_ca.py` em duas fases contra o uvicorn real e o mesmo banco: `APP_AGORA=2030-01-07T09:00:00-03:00` (antes do início) e `APP_AGORA=2030-01-10T09:30:00-03:00` (depois do início) para CA-06, CA-08 e CA-10.
  - Ajuste só de evidência: a linha de CA-03 cortava o JSON antes de `promovida`; o script passou a registrar explicitamente a cancelada, a promovida e a próxima da fila. Rodado de novo: 11/11.
  - Subida manual: `PY -m uvicorn app.main:app --port 55661` (porta livre; 8000 pode estar ocupada por execuções paralelas) → `GET /api/saude` `{"status":"ok"}`, `GET /` 200 `text/html`; processo encerrado e porta sem resposta depois.
- **Gate:**
  - [x] Instalação num `.venv` novo funcionou.
  - [x] `PY -m pytest -q` passa: `59 passed, 1 warning`.
  - [x] `evidencias/criterios-aceite.md` tem CA-01..CA-10 e TELA, todas `PASSOU` (11/11).
  - [x] A subida manual respondeu em `/api/saude` e `/`.
  - [x] Nenhum processo do servidor desta execução ficou rodando (conferido na lista de processos; os uvicorn listados pertencem a outra pasta, `r01/P01`).
- **Problemas e correções:** nenhum no sistema; só a melhoria da evidência de CA-03 descrita acima.
- **Gate:** APROVADO
- **Fim:** 18:00

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 59/59 (`59 passed, 1 warning`: aviso de depreciação do anyio no starlette) |
| Critérios de aceite verificados via HTTP | 10/10 (+ TELA) |
| Ajustes manuais | nenhum |
| Pendências | Atualizar fastapi/starlette quando a stack padrão permitir (CVEs de starlette 0.41.3 em recursos não usados; a que afetava a tela foi mitigada). Tela conferida por HTTP, IDs e `node --check`, sem navegador real. |
