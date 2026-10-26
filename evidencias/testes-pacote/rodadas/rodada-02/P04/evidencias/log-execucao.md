# Log de execução

| Campo | Valor |
|---|---|
| Agente | Claude Code (subagente) |
| Modelo | claude-opus-5-5 |
| Início | 2026-10-26 07:26 |
| Pedido usado | `PEDIDO.md` (raiz da pasta de trabalho; o prompt cita "PEDIDO.md") |

## Prompt de entrada

> Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

## Etapa 0 · Preparação

- **Início:** 07:27
- Pedido localizado: `PEDIDO.md` (citado no prompt e presente na raiz).
- Ambiente: `python --version` → `Python 3.11.0` (atende 3.11+).
- Pastas `gerado/` e `evidencias/` criadas; log iniciado com o modelo de `skills/fabrica/referencias/modelo-log.md`.
- Referências lidas: `regras-transversais.md`, `stack-padrao.md`, e as seis skills de etapa.
- **Fim:** 07:27

## Etapa 1 · Concepção

- **Início:** 07:28
- **Artefatos:** `gerado/docs/PRD.md`
- **Decisões e premissas:**
  - PR-04 resolve contradição do pedido: "saldo disponível = saldo − SOLICITADA − APROVADA" junto com "ao aprovar, os dias saem do saldo" descontaria aprovados duas vezes. Saldo guardado já exclui aprovados; disponível desconta só pendentes. Satisfaz CA-04 e CA-05.
  - PR-05: limite por equipe só na aprovação (pedido diz "Aprovar uma solicitação que quebra essa regra é recusado").
  - RN-09: "até o dia anterior ao início" lido como hoje ≤ início − 1 (no dia do início já não cancela).
  - RN-11: faixa de saldo 0–365 escolhida para evitar valor sem limite.
- **Cobertura do pedido:**

| Trecho do pedido | Códigos |
|---|---|
| "pedidos chegam por mensagem... metade do time sair junto" | Problema, RN-07 |
| "sistema para a pessoa pedir férias" | RF-04 |
| "gestor aprovar sem deixar gente demais da mesma equipe fora" | RF-06, RN-07 |
| "calendário para ver quem está de férias" | RF-09 |
| "Não precisa de login" | RF-12, PR-07, Fora de escopo |
| Cadastro com nome, e-mail, equipe (DADOS, PRODUTO, SUPORTE) e saldo (30 por padrão) | RF-01, RN-11, PR-03, PR-11 |
| Já começa com 9 colaboradores, 3 por equipe | RF-03 |
| Solicitação com colaborador, início, fim (dias corridos, conta primeiro e último) e situação | RF-04, RN-01, PR-02 |
| Situações SOLICITADA, APROVADA, REPROVADA, CANCELADA | Entidades, RF-04 |
| Período mínimo 5, máximo 30 | RN-02 |
| Início com pelo menos 30 dias de antecedência | RN-03, PR-01 |
| Dias ≤ saldo disponível (saldo − SOLICITADA/APROVADA) | RN-04, PR-04 |
| Sem duas SOLICITADA/APROVADA do mesmo colaborador com dias em comum | RN-05, PR-02 |
| Só SOLICITADA pode ser aprovada ou reprovada | RN-06, RF-06, RF-07, PR-06 |
| No máximo 1 pessoa por equipe APROVADA no mesmo dia | RN-07, PR-05 |
| Ao aprovar, dias saem do saldo | RN-08 |
| Cancelar SOLICITADA/APROVADA até o dia anterior ao início; aprovada devolve saldo | RF-08, RN-09, RN-10 |
| Calendário de um mês, por dia, aprovadas, por equipe | RF-09, PR-08 |
| Saldo de cada colaborador | RF-02 |
| API REST para todas as operações | RF-10 |
| Tela web simples para solicitar, aprovar, reprovar, ver calendário | RF-11, RF-05 |
| Dados em banco local. Sem login | RF-12 |
| CA-01 a CA-10 | Seção Critérios de aceite do PRD |

- **Lacunas comuns:**

| Item | Resolução |
|---|---|
| Fuso horário e formato de data | PR-01, PR-02 |
| Bordas de limites | RN-02 (5 e 30 inclusive), RN-03 (30 aceito, 29 recusado), RN-09 (até início − 1) |
| O que "cadastro" cobre | PR-03 |
| Unicidade de nomes ou identificadores | PR-11, RN-11 |
| Formato e validação de campos | RN-11 |
| Registros relacionados quando um muda de status | RN-08, RN-10, PR-06 |
| Definição de período em consultas | PR-08 |
| Arredondamento e unidade | PR-10 |
| Ordenação de listagens | PR-09 |
| Trechos que se contradizem | PR-04 |
| Interação entre duas regras no mesmo momento | PR-05 (sobreposição pendente na equipe x limite na aprovação); RN-04 + RN-08 via PR-04 |
| Datas de calendário sem horário | PR-01, PR-02, RN-01 |

- **Gate:**
  - [x] `gerado/docs/PRD.md` existe com até 70 linhas de itens (contagem por script: 52).
  - [x] Todo trecho do pedido aparece na tabela de cobertura com pelo menos um código.
  - [x] Cada item da lista de lacunas comuns tem uma linha no log.
  - [x] Toda RN com limite tem número e borda explícitos (RN-02, RN-03, RN-04, RN-07, RN-09, RN-11).
  - [x] Todo CA-xx do pedido está no PRD com código original, cenário, resultado e RF/RN.
  - [x] Seção "Fora de escopo" existe.
  - [x] Nenhuma linguagem, framework, banco, formato, endpoint ou tabela de banco no PRD (grep por sqlite/fastapi/python/json/api/endpoint: nada).
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 07:29

## Etapa 2 · Especificação

- **Início:** 07:29
- **Artefatos:** `gerado/docs/SPEC.md`
- **Decisões e premissas:**
  - Códigos de erro: 422 para PERIODO_INVALIDO, DURACAO_INVALIDA, ANTECEDENCIA_INSUFICIENTE, CANCELAMENTO_FORA_DO_PRAZO (inválidos em qualquer estado, ou prazo); 409 para SALDO_INSUFICIENTE, SOBREPOSICAO, TRANSICAO_INVALIDA, LIMITE_EQUIPE, EMAIL_DUPLICADO (dependem do estado guardado).
  - Novo tipo `Mes` (AAAA-MM, ano 2000–2100) em `app/tipos.py` para o calendário; o modelo de projeto não traz tipo de mês.
  - Ordem de validação no POST de solicitação: formato → colaborador → RN-01 → RN-02 → RN-03 → RN-05 → RN-04.
  - Nenhuma carga inicial de solicitações (o pedido só cita colaboradores).
  - E-mails da carga inicial em `exemplo.com` (fictícios).
- **Gate:**
  - [x] `gerado/docs/SPEC.md` existe com as seções do modelo (Modelo de dados, Carga inicial, Endpoints, Regras de negócio, Tela, Rastreabilidade, Plano de testes).
  - [x] RF-01 a RF-12 na tabela de rastreabilidade com endpoint, tela ou carga inicial.
  - [x] RN-01 a RN-11 com função de domínio e código de erro (RN-08 e RN-10 são cálculos, sem erro próprio).
  - [x] Os 10 endpoints têm método, caminho, entrada, saída e erros.
  - [x] CA-01 a CA-10 com teste `test_ca_XX_...` no plano.
  - [x] RN com limite numérico (RN-02, RN-03, RN-04, RN-07, RN-09, RN-11) com teste de borda no plano.
  - [x] DDL completo, só tipos SQLite (INTEGER, TEXT).
- **Problemas e correções:** linha do plano de RN-04 estava vaga; reescrita antes do gate.
- **Gate:** APROVADO
- **Fim:** 07:31

## Etapa 3 · Construção

- **Início:** 07:31
- **Artefatos:** `gerado/app/` (`banco.py` com ESQUEMA e carga, `tipos.py` com `Mes`, `dominio/ferias.py`, `dominio/colaboradores.py`, `repositorio/ferias.py`, `rotas/colaboradores.py`, `rotas/solicitacoes.py`, `rotas/calendario.py`, `estatico/index.html`), `gerado/tests/test_ferias.py`, `gerado/verificacao/verificar_ca.py`, `gerado/README.md`
- **Decisões e premissas:**
  - Modelo copiado de `skills/construcao/modelo-projeto/`; `.venv` criado e `pip install -r requirements.txt` sem erro; testes do modelo antes de mudar: `12 passed, 1 warning`.
  - Nenhuma dependência adicionada.
  - Regras de sobreposição ficaram no domínio: o repositório entrega todos os períodos ativos do colaborador e todas as aprovadas da equipe (volume pequeno), sem filtrar datas no SQL.
  - **Volta à especificação:** `GET /api/saude` vem do modelo de projeto e o harness depende dele, mas não estava na SPEC; acrescentado à SPEC como endpoint de infraestrutura para cumprir "nenhum endpoint fora da SPEC".
- **Testes antes da implementação (com ESQUEMA, carga inicial e tipo `Mes` prontos, sem rotas):** `46 failed, 12 passed, 1 warning in 6.34s` (os 12 que passam são os do modelo; todos os 46 novos falham).
- **Testes depois da implementação:** `58 passed, 1 warning in 9.96s`
- **Tela:** `node --check` no script extraído: OK; nenhum `innerHTML` com dado (só o comentário do modelo).
- **Ensaio de `verificar_ca.py`:** 11/11 PASSOU (TELA + CA-01 a CA-10).
- **Gate:**
  - [x] `PY -m pip install -r requirements.txt` funciona num `.venv` novo.
  - [x] O log registra a rodada de testes antes da implementação, com falhas (46 failed).
  - [x] `PY -m pytest -q` passa sem falhas: `58 passed, 1 warning`.
  - [x] Existe teste `test_ca_XX_...` para CA-01 a CA-10.
  - [x] Teste de borda para RN-02 (4/5/30/31), RN-03 (29/30/31), RN-04 (disponível e +1), RN-07 (1 dia em comum / dia seguinte no CA-08), RN-09 (véspera / dia do início / dia seguinte), RN-11 (−1/0/365/366).
  - [x] Todos os endpoints da SPEC implementados; nenhum fora dela (`/api/saude` agora na SPEC; `/docs`, `/openapi.json` permitidos).
  - [x] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py` (grep).
  - [x] `verificacao/verificar_ca.py` tem um bloco por CA-xx.
  - [x] `gerado/README.md` existe com os comandos.
- **Problemas e correções:** nenhuma falha de teste após a implementação; só a volta à SPEC descrita acima.
- **Gate:** APROVADO
- **Fim:** 07:40

## Etapa 4 · Revisão de qualidade

- **Início:** 07:40
- **Testes no ponto de partida:** `58 passed, 1 warning`
- **Artefatos:** `evidencias/revisao.md`, sonda em `gerado/.tmp/sonda.py` (saída em `gerado/.tmp/sonda.txt`)
- **Decisões:** 4 achados, todos baixos e aceitos com motivo; nenhum alto ou médio. Sondagem de valores extremos: 43 requisições, nenhum 5xx.
- **Gate:**
  - [x] `evidencias/revisao.md` existe com a tabela de achados.
  - [x] Nenhum achado alto ou médio com status diferente de `CORRIGIDO` (não houve alto/médio).
  - [x] `PY -m pytest -q` passa depois da revisão: `58 passed, 1 warning`.
- **Problemas e correções:** a sonda falhou na primeira execução por `UnicodeEncodeError` no console cp1252 (problema do script de sonda, não do sistema); rodada de novo com `PYTHONIOENCODING=utf-8`.
- **Gate:** APROVADO
- **Fim:** 07:42

## Etapa 5 · Revisão de segurança

- **Início:** 07:42
- **Artefatos:** `gerado/tests/test_seguranca.py` (13 testes), `evidencias/seguranca.md`, `gerado/.tmp/pip-audit.json`
- **Decisões:** nenhum achado alto ou médio; 1 baixo (sem login, exigido pelo pedido) e 1 informativo (f-strings de SQL só com constantes).
- **Varreduras:** grep de SQL dinâmico: vazio; `innerHTML`: só comentário; grep de segredos: vazio; `pip-audit`: `No known vulnerabilities found` (23 pacotes, 0 vulnerabilidades); `pip check`: OK.
- **Observação de ambiente:** o `pip-audit` cria um venv temporário em `%TEMP%` do sistema (fora da pasta de trabalho), por comportamento próprio da ferramenta; não há opção usada pela skill para evitar isso.
- **Gate:**
  - [x] `tests/test_seguranca.py` existe e passa (13 passed).
  - [x] `evidencias/seguranca.md` existe com todos os itens do checklist preenchidos.
  - [x] Nenhum achado alto ou médio aberto.
  - [x] `PY -m pytest -q` passa: `71 passed, 1 warning`.
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 07:45

## Etapa 6 · Verificação

- **Início:** 07:45
- **Artefatos:** `evidencias/criterios-aceite.md`, `evidencias/subida-manual.md`
- **Instalação limpa:** `.venv/` e `dados/` apagados; `python -m venv .venv` e `PY -m pip install -r requirements.txt` sem erro (saída 0).
- **Testes:** `71 passed, 1 warning in 9.90s`
- **Critérios de aceite via HTTP (`PY verificacao/verificar_ca.py`, uvicorn real, `APP_AGORA=2030-01-07T09:00:00-03:00`, banco novo):** 11/11 PASSOU (CA-01 a CA-10 e TELA), saída 0.
- **Subida manual (`PY verificacao/subida_manual.py`, relógio real, banco novo):** API, TELA e DOCS PASSOU, saída 0.
- **Processos:** consulta `Win32_Process` por `python.exe` com `uvicorn` ou a pasta P04 na linha de comando: nenhum.
- **Gate:**
  - [x] Instalação num `.venv` novo funcionou.
  - [x] `PY -m pytest -q` passa (71 passed).
  - [x] `evidencias/criterios-aceite.md` com uma linha por CA-01 a CA-10 e a linha TELA, todas PASSOU.
  - [x] `evidencias/subida-manual.md` com as três linhas PASSOU.
  - [x] Nenhum processo do servidor ficou rodando.
- **Problemas e correções:** nenhum.
- **Gate:** APROVADO
- **Fim:** 07:48

## Encerramento

- `gerado/README.md` conferido: o que o sistema faz, instalar, rodar, testar, verificar e endereço da tela (`http://127.0.0.1:8000/`).
- Nenhum dado real nem segredo em `gerado/` ou `evidencias/` (grep de segredos vazio; dados fictícios em `exemplo.com`).
- **Fim da execução:** 2026-10-26 07:48

## Quadro final

| Item | Resultado |
|---|---|
| Gates aprovados | 6/6 (concepção, especificação, construção, revisão, segurança, verificação), todos na primeira tentativa |
| Testes | 71/71 |
| Critérios de aceite verificados via HTTP | 10/10 (mais TELA) |
| Ajustes manuais | nenhum |
| Pendências | nenhuma |
