# Log de execução

| Campo | Valor |
|---|---|
| Agente | Claude Code (subagente) |
| Modelo | claude-opus-5-5 |
| Início | 2026-10-23 17:12 -03:00 |
| Pedido usado | `PEDIDO.md` (raiz; nenhum arquivo citado além dele no prompt) |

## Prompt de entrada

> Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

## Etapa 0 · Preparação

- **Início:** 17:12
- **Pedido:** `PEDIDO.md` na raiz (citado no prompt).
- **Ambiente:** `python --version` → `Python 3.11.0` (>= 3.11, ok).
- **Pastas:** `gerado/` e `evidencias/` criadas; este log iniciado.
- **Referências lidas:** `skills/fabrica/referencias/regras-transversais.md`, `skills/fabrica/referencias/stack-padrao.md`.
- **Fim:** 17:12

## Etapa 1 · Concepção

- **Início:** 17:13
- **Artefatos:** `gerado/docs/PRD.md`
- **Decisões e premissas:**
  - PR-01 fuso America/Sao_Paulo, horários sempre com fuso explícito.
  - PR-02 cadastro de sala = criar, listar, consultar.
  - PR-03 início exatamente igual a agora é aceito.
  - PR-04 dia civil no fuso; ocupação recorta a janela 08:00–18:00.
  - PR-05 taxa em percentual com 1 casa decimal, mais minutos ocupados.
  - PR-06 ordenação de listagens.
  - PR-07 sala não muda de status, então reservas não são afetadas.
  - PR-08 reservas permitidas fora da janela 08–18h.
  - PR-09 limite de 200 caracteres para textos livres (254 para e-mail).
  - RF-08 (agenda do dia) derivado de "ver a agenda do dia por sala" na tela, que precisa de uma operação de API (RF-09 "API REST para todas as operações").
- **Cobertura do pedido:**

| Trecho do pedido | Códigos |
|---|---|
| "duas pessoas reservarem a mesma sala no mesmo horário" / "planilha compartilhada" | Problema, RN-01 |
| "cadastro das salas" | RF-01, RF-02, PR-02, RN-10 |
| "reserva sem conflito" | RF-04, RN-01 |
| "um jeito rápido de achar sala livre" | RF-06, RN-07 |
| "saber quanto cada sala é usada" | RF-07, RN-08 |
| "Não precisa de login por enquanto" | RF-11, Fora de escopo |
| Salas: nome, local (SAO_PAULO, ARARAQUARA, COWORKING), capacidade, recursos (TV, VIDEOCONFERENCIA, QUADRO) | Entidades, RF-01, RN-10 |
| "já começa com 6 salas cadastradas, duas por local" | RF-03 |
| Reserva: sala, responsável (nome e e-mail), título, participantes, início, fim | Entidades, RF-04, RN-11 |
| "não podem se sobrepor. Encostar é permitido" | RN-01 |
| "Duração mínima de 15 minutos e máxima de 4 horas" | RN-02 |
| "Não é possível reservar no passado" | RN-03, PR-03 |
| "Participantes não podem passar da capacidade" | RN-04 |
| "Só reservas futuras podem ser canceladas" | RN-05 |
| "fica no histórico com status CANCELADA e libera o horário" | RF-05, RN-06 |
| "Salas livres num intervalo, com filtro opcional por local e capacidade mínima" | RF-06, RN-07 |
| "Taxa de ocupação de cada sala num dia, 8h às 18h, só reservas ativas" | RF-07, RN-08, RN-06, PR-04, PR-05 |
| "API REST para todas as operações" | RF-09 |
| "Uma tela web simples para reservar e ver a agenda do dia por sala" | RF-10, RF-08 |
| "Dados em banco local. Sem login." | RF-11 |
| CA-01 a CA-10 | Critérios de aceite do PRD, mesmos códigos |

- **Lacunas comuns:**

| Lacuna | Resolução |
|---|---|
| fuso horário e formato de data | PR-01 |
| bordas de limites | RN-02 (inclusive), RN-03 (início >= agora), RN-04 (1..capacidade inclusive), RN-05 (início > agora), RN-01 (semiaberto) |
| o que "cadastro" cobre | PR-02 |
| unicidade de nomes | RN-10 (nome de sala único, sem diferenciar maiúsculas) |
| formato e validação de campos | RN-10, RN-11, PR-09, RN-09 |
| registros relacionados quando um muda de status | RN-06 (cancelamento libera horário), PR-07 |
| definição de período em consultas e relatórios | PR-04, RN-08 |
| arredondamento e unidade | PR-05 |
| ordenação de listagens | PR-06 |

- **Gate:**
  - [x] `gerado/docs/PRD.md` existe com até 60 linhas de itens (contagem: 49 linhas de item).
  - [x] Todo trecho do pedido aparece na tabela de cobertura com pelo menos um código.
  - [x] Cada item da lista de lacunas comuns tem uma linha, com código.
  - [x] Toda RN com limite tem número e borda explícitos (RN-02, RN-03, RN-04, RN-05, RN-08, RN-10).
  - [x] Todo CA-xx do pedido está no PRD com código original, cenário, resultado e RF/RN.
  - [x] Seção "Fora de escopo" existe.
  - [x] Nenhuma linguagem, framework, produto de banco, formato de dado, endpoint ou tabela no PRD (conferido com `grep -niE "python|fastapi|sqlite|json|endpoint|/api|tabela|iso 8601"`: nada).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 17:16

## Etapa 2 · Especificação

- **Início:** 17:16
- **Artefatos:** `gerado/docs/SPEC.md`
- **Decisões e premissas:**
  - `recursos` como lista JSON em coluna TEXT (nenhuma consulta filtra por recurso).
  - `GET /api/reservas/{id}` incluído para permitir conferir o estado de uma reserva (RF-04/RF-09), usado em CA-07 e CA-08.
  - Cancelar reserva já cancelada: 409 `RESERVA_JA_CANCELADA` (conflito com estado). Cancelar reserva com início <= agora: 422 `CANCELAMENTO_NAO_PERMITIDO`.
  - Ordem de conferência na criação de reserva: formato, intervalo, duração, passado, sala existe, capacidade, conflito.
  - Participantes 0 ou negativo cai na validação de formato (422 padrão), acima da capacidade em 422 `CAPACIDADE_EXCEDIDA`.
  - `/api/salas/livres` declarado antes de `/api/salas/{sala_id}` para não colidir.
- **Gate:**
  - [x] `gerado/docs/SPEC.md` existe com as seções do modelo (Modelo de dados, Carga inicial, Endpoints, Regras de negócio, Tela, Rastreabilidade, Plano de testes).
  - [x] Todo RF-01..RF-11 aparece na rastreabilidade com endpoint, tela ou carga inicial.
  - [x] Todo RN-01..RN-11 aparece com função de domínio (ou modelo de entrada) e código de erro.
  - [x] Todo endpoint (9) tem método, caminho, entrada, sucesso e erros.
  - [x] Todo CA-01..CA-10 tem teste `test_ca_XX_...` no plano.
  - [x] RN com limite numérico (RN-01, RN-02, RN-03, RN-04, RN-05, RN-08, RN-10) têm teste de borda no plano.
  - [x] DDL completo, só tipos SQLite (INTEGER, TEXT).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 17:18

## Etapa 3 · Construção

- **Início:** 17:18
- **Artefatos:** `gerado/app/` (`banco.py` com ESQUEMA e carga inicial; `dominio/reservas.py`, `dominio/salas.py`, `dominio/ocupacao.py`; `repositorio/salas.py`, `repositorio/reservas.py`; `rotas/modelos.py`, `rotas/salas.py`, `rotas/reservas.py`, `rotas/relatorios.py`; `estatico/index.html`), `gerado/tests/test_criterios_aceite.py`, `gerado/tests/test_regras.py`, `gerado/verificacao/verificar_ca.py`, `gerado/README.md`.
- **Decisões e premissas:**
  - Modelo copiado de `skills/construcao/modelo-projeto/` sem `.venv`, `dados/` e `__pycache__`. Base: `2 passed` antes de qualquer mudança.
  - Testes escritos antes do código, em dois lotes (critérios de aceite e regras), em vez de um teste por vez. Fase vermelha conferida: `42 failed, 2 passed` (404 por rotas inexistentes). Depois da implementação: `44 passed` sem ajuste nos testes.
  - SQL só com strings constantes e `?` (nada de f-string em `execute`, para a varredura da etapa 5 não acusar falso positivo). Filtro opcional por sala com `(? IS NULL OR sala_id = ?)`.
  - Testes extras além do plano: `test_rn_01_encostar_dos_dois_lados_e_outra_sala`, `test_rn_08_reserva_que_atravessa_meia_noite`, `test_rn_10_sala_capacidade_bordas` (desdobramento do plano).
  - `verificar_ca.py` executado uma vez nesta etapa como ensaio: 11/11 PASSOU (o arquivo será regravado na etapa 6).
- **Gate:**
  - [x] `PY -m pip install -r requirements.txt` funcionou num `.venv` novo (criado nesta etapa).
  - [x] `PY -m pytest -q` passa: `44 passed, 1 warning` (aviso de depreciação do `anyio` dentro do `starlette.testclient`, de dependência transitiva).
  - [x] Existe `test_ca_01` .. `test_ca_10` (conferido com `grep -ohE "test_ca_[0-9]+"`).
  - [x] Teste de borda para cada RN com limite: RN-01, RN-02, RN-03, RN-04, RN-05, RN-08, RN-10.
  - [x] Os 9 endpoints da SPEC implementados; nenhum endpoint fora da SPEC (além de `/api/saude` e `/` do modelo).
  - [x] Nenhum `datetime.now()` fora de `app/relogio.py` (grep vazio).
  - [x] `verificacao/verificar_ca.py` tem um bloco por CA-xx (10 blocos + TELA).
  - [x] `gerado/README.md` existe com os comandos.
- **Problemas e correções:** um comando de shell com vários heredocs falhou ao ser interpretado (erro de aspas no bash); os arquivos de rotas foram gravados de novo pelo editor. Sem efeito no código.
- **Gate:** APROVADO
- **Fim:** 17:24

## Etapa 4 · Revisão de qualidade

- **Início:** 17:24
- **Artefatos:** `evidencias/revisao.md`, `gerado/tests/test_robustez.py`; correções em `gerado/app/rotas/modelos.py`, `salas.py`, `reservas.py`, `relatorios.py`.
- **Decisões e premissas:**
  - Sondagem de entradas extremas com `TestClient(raise_server_exceptions=False)` revelou HTTP 500 com ids enormes e datas nos anos 1/9999.
  - **Volta às etapas 1 e 2:** criada a premissa PR-10 (datas entre os anos 2000 e 2100) no PRD e registrados na SPEC os limites comuns (ids até 2^63−1, PR-10) e os três testes `test_robustez_*` no plano. PRD passa a 50 linhas de item (gate da concepção continua atendido).
  - Tela conferida no navegador contra o servidor real (porta 8000, banco temporário `dados/tela.db`, apagado depois; servidor encerrado).
- **Gate:**
  - [x] `evidencias/revisao.md` existe com a tabela de achados (R-01..R-06).
  - [x] Nenhum achado alto ou médio com status diferente de CORRIGIDO (R-01, R-02, R-03 corrigidos; R-04..R-06 baixos, aceitos com motivo).
  - [x] `PY -m pytest -q` passa depois das correções: `58 passed, 1 warning`.
- **Problemas e correções:**
  - Primeira tentativa da correção R-02 deixou 4 testes falhando: `data: Data = Query(...)` não aplica o `AfterValidator` do `Annotated` em parâmetros de consulta nesta versão do FastAPI. Trocado para `data: Annotated[Data, Query()]`; suíte verde.
  - Um script de sondagem foi gravado por engano fora da pasta da execução (um nível acima de `run-e2e-1/`) e apagado em seguida; as sondagens viraram testes em `gerado/tests/test_robustez.py`.
- **Gate:** APROVADO
- **Fim:** 17:28

## Etapa 5 · Revisão de segurança

- **Início:** 17:28
- **Artefatos:** `evidencias/seguranca.md`, `evidencias/pip-audit.json`, `gerado/tests/test_seguranca.py`, `gerado/.gitignore`; correção em `gerado/app/main.py`.
- **Decisões e premissas:**
  - `pip-audit` rodou (havia rede): 8 vulnerabilidades distintas (7 na starlette 0.41.3, 1 no pytest 8.3.4). Só a CVE-2025-62727 (`Range` no `FileResponse`) atinge o sistema; corrigida servindo a tela com `HTMLResponse`. As demais tocam recursos não usados (formulários, `request.url`, `StaticFiles`, `HTTPEndpoint`) e ficam aceitas.
  - Não atualizei FastAPI/starlette: a stack padrão fixa `fastapi==0.115.6`, que limita a starlette a < 0.42. Fica como pendência.
  - `.gitignore` da raiz não foi alterado (fora de `gerado/`); criado `gerado/.gitignore` com `dados/` e `.venv/`.
- **Gate:**
  - [x] `tests/test_seguranca.py` existe e passa (`25 passed`).
  - [x] `evidencias/seguranca.md` existe com todos os itens do checklist preenchidos.
  - [x] Nenhum achado alto ou médio aberto (S-01 médio corrigido; S-02..S-05 baixos, com motivo).
  - [x] `PY -m pytest -q` passa: `83 passed, 1 warning`.
- **Problemas e correções:** dois comandos auxiliares tentaram gravar arquivo temporário fora da pasta da execução; um foi apagado e o outro foi bloqueado antes de rodar. A saída do `pip-audit` foi gravada em `evidencias/pip-audit.json`.
- **Gate:** APROVADO
- **Fim:** 17:34

## Etapa 6 · Verificação

- **Início:** 17:35
- **Artefatos:** `evidencias/criterios-aceite.md`, `evidencias/subida-manual.log`
- **Passos:**
  1. Instalação limpa: `.venv/`, `dados/` e `__pycache__/` apagados em `gerado/`; `python -m venv .venv` e `.venv/Scripts/python -m pip install -r requirements.txt` sem erro.
  2. Testes: `.venv/Scripts/python -m pytest -q` → `83 passed, 1 warning`.
  3. Critérios de aceite: `.venv/Scripts/python verificacao/verificar_ca.py` → código de saída 0, **11/11 aprovados** (TELA + CA-01..CA-10). Servidor real na porta 8765, relógio `APP_AGORA=2030-01-07T09:00:00-03:00`; CA-08 com o servidor reiniciado em `2030-01-09T09:00:00-03:00` sobre o mesmo banco. Primeira execução já passou.
  4. Subida manual: `.venv/Scripts/python -m uvicorn app.main:app --port 8000` em segundo plano; `GET /api/saude` → 200 `{"status":"ok"}`; `GET /` → 200 com `<title>Reserva de salas</title>`; `GET /api/salas` → 6 salas. Escutando em `127.0.0.1`. Processo encerrado (PID 20348); nenhuma escuta nas portas 8000 e 8765 e nenhum `python.exe` restante.
- **Gate:**
  - [x] Instalação num `.venv` novo funcionou.
  - [x] `PY -m pytest -q` passa (`83 passed`).
  - [x] `evidencias/criterios-aceite.md` existe com uma linha por CA-01..CA-10 e a linha TELA, todas PASSOU.
  - [x] A subida manual respondeu em `/api/saude` e `/`.
  - [x] Nenhum processo do servidor ficou rodando.
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 17:37

## Encerramento

- `gerado/README.md` conferido: o que o sistema faz, comandos de instalar, testar, rodar e verificar, endereço da tela (`http://127.0.0.1:8000/`) e tabela de endpoints.
- Varredura final de segredos em `gerado/` e `evidencias/`: nenhuma linha.

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 |
| Testes | 83/83 |
| Critérios de aceite verificados via HTTP | 10/10 (mais a linha TELA: 11/11) |
| Ajustes manuais | nenhum |
| Pendências | starlette 0.41.3 (presa pelo `fastapi==0.115.6` da stack padrão) tem 6 CVEs em recursos não usados pelo sistema e o pytest 8.3.4 tem 1 CVE só de ambiente UNIX; atualizar exige sair das versões da stack padrão. Aviso de depreciação do `anyio` no `TestClient` (dependência transitiva sem versão fixada). |
