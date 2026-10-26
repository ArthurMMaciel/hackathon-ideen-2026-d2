# Fábrica de software em skills · Hackathon Ideen 2026 · Desafio 2

## 1. O problema

Cada pessoa conduz o agente de IA do seu jeito, e não existe um processo reaproveitável que leve um pedido em linguagem natural até um sistema funcionando com o mínimo de ajuste manual.

## 2. O que eu fiz

Um pacote de 8 skills (`SKILL.md`): uma orquestradora, seis etapas e uma de evolução.

| Skill | Fluxo | O que faz | Saída |
|---|---|---|---|
| `fabrica` | ambos | Orquestra as etapas, mantém o log, confere cada gate e desvia para `evolucao` quando o sistema já existe | `evidencias/log-execucao.md` |
| `concepcao` | construção, etapa 1 | Pedido → PRD com RF, RN, premissas, fora de escopo e CA | `gerado/docs/PRD.md` |
| `especificacao` | construção, etapa 2 | PRD → contrato dos endpoints, DDL e plano de testes | `gerado/docs/SPEC.md` |
| `construcao` | construção, etapa 3 | Testes primeiro e depois o código, sobre o modelo de projeto testado | `gerado/` |
| `revisao` | construção, etapa 4 | Revisão de qualidade com sondas de valores extremos | `evidencias/revisao.md` |
| `revisao-seguranca` | construção, etapa 5 | Injeção, XSS, validação, segredos e `pip-audit` | `evidencias/seguranca.md` |
| `verificacao` | construção, etapa 6 | Instalação limpa e cada CA executado via HTTP no servidor real | `evidencias/criterios-aceite.md` |
| `evolucao` | evolução | Mudança incremental sem refazer o sistema | `evidencias/log-evolucao.md` |

**Construção do zero (cerca de 23 minutos):** a partir de um pedido completo, a `fabrica` passa pelas seis etapas, sem intervenção humana, com um gate verificável entre elas.

**Evolução (cerca de 5 minutos):** quando o sistema já existe e chega um pedido de mudança ("agora quero editar..."), a `evolucao` atualiza PRD e SPEC só no que muda. Ela escreve os testes da mudança antes do código, roda a suíte inteira contra regressão e verifica via HTTP.

Diferenciais:

- **Rastreabilidade:** todo trecho do pedido vira um código, e todo `CA-xx` chega a um teste com o código no nome e a uma linha da evidência HTTP.
- **Sem perguntas:** lacunas viram premissas registradas, a partir de uma lista fixa de lacunas comuns.
- **Modelo de projeto testado** (`skills/construcao/modelo-projeto/`): relógio injetável, tipos com limites que evitam HTTP 500, erros padronizados, tela com CSS pronto, scripts que sobem o servidor real. Stack: Python 3.11+, FastAPI, SQLite, pytest, HTML sem build, com dependências fixadas e `pip-audit` sem vulnerabilidades.
- **Evidência escrita pelas próprias skills:** log com horários lidos do relógio, revisões, varredura de segurança e critérios via HTTP.

## 3. Como reproduzir

### Rodar o pacote num pedido

1. Crie uma pasta com `PEDIDO.md` (por exemplo, uma cópia de `PEDIDO-TREINO.md`) e as pastas vazias `gerado/` e `evidencias/`.
2. Disponibilize as skills mantendo as pastas lado a lado, porque elas se referenciam por caminho relativo (`../concepcao/SKILL.md`):
   - **Forma testada:** copie `skills/` para dentro da pasta do pedido.
   - **Instalada como skills do agente** (no Claude Code, copiar o conteúdo de `skills/` para `.claude/skills/`): testada. O Claude Code CLI descobriu as 8 skills, escolheu a `fabrica` para o pedido e resolveu os caminhos relativos entre skills ([teste](evidencias/testes-pacote/instalacao-claude-skills.md)). Nesse layout testei a descoberta e a leitura; a construção completa rodou com as skills dentro da pasta.
3. Abra o agente na pasta e use o prompt da banca:

   > Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

4. Para uma mudança depois, peça em linguagem natural, por exemplo: "Usando as skills disponíveis, aplique esta mudança ao sistema em gerado/: ...".

Requisitos: Python 3.11+ e internet para o `pip`. Construção do zero: cerca de 23 minutos. Evolução: cerca de 5 minutos.

### Rodar o sistema gerado do pedido de treino

Rode os comandos a partir de `gerado/`. Depois de subir o servidor, abra `http://localhost:8000/`. O script de verificação reescreve `evidencias/criterios-aceite.md`.

**Windows (PowerShell ou cmd)**

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python verificacao\verificar_ca.py
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

**Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python verificacao/verificar_ca.py
.venv/bin/python -m uvicorn app.main:app --port 8000
```

No Debian e no Ubuntu, se o `venv` faltar: `sudo apt install python3-venv`.

**macOS**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python verificacao/verificar_ca.py
.venv/bin/python -m uvicorn app.main:app --port 8000
```

Se o `python3` não existir, instale com `brew install python@3.11` ou pelo instalador de python.org.

## 4. Evidências

Tudo o que não é o pacote (`skills/`) nem o sistema gerado (`gerado/`) está em `evidencias/`.

| O quê | Onde |
|---|---|
| Log da execução do pedido de treino (agente, modelo, prompt, gates) | [`log-execucao.md`](evidencias/log-execucao.md) |
| Critérios de aceite via HTTP: 10/10, mais a tela | [`criterios-aceite.md`](evidencias/criterios-aceite.md) |
| Subida com relógio real (API, tela, docs) | [`subida-manual.md`](evidencias/subida-manual.md) |
| Revisões de qualidade e de segurança | [`revisao.md`](evidencias/revisao.md), [`seguranca.md`](evidencias/seguranca.md) |
| Diário das minhas decisões com a IA | [`diario-de-decisoes.md`](evidencias/diario-de-decisoes.md) |
| Generalização em 6 pedidos, 2 rodadas | [`testes-pacote/`](evidencias/testes-pacote/) |
| Teste da evolução (5 min 7 s) | [`testes-pacote/evolucao/`](evidencias/testes-pacote/evolucao/) |
| Teste com outro agente (Codex) | [`testes-pacote/codex/`](evidencias/testes-pacote/codex/) |

**Agente e modelo:** Claude Code com `claude-opus-5-5`, em subagentes com contexto limpo, numa pasta só com as skills e o pedido. **O prompt da banca foi enviado acompanhado de notas de ambiente:**
- trabalhar só naquela pasta;
- usar o Python do Windows;
- não usar o navegador compartilhado entre execuções paralelas;
- relatar no fim onde as skills foram ambíguas.

Nenhuma nota orientou o conteúdo do sistema.

**Generalização:** além do pedido de treino, escrevi 5 pedidos do mesmo tamanho e tipo, cada um forçando regras diferentes, para simular o pedido oculto.

| Rodada | Skills | Gates | Testes | CAs via HTTP | Ajuste manual | Pendências |
|---|---|---|---|---|---|---|
| [01](evidencias/testes-pacote/rodadas/rodada-01/RESULTADOS.md) | v1 | 36/36 | 390/390 | 60/60 | nenhum | 6 de 6 (CVEs da stack) |
| [02](evidencias/testes-pacote/rodadas/rodada-02/RESULTADOS.md) | v2 | 36/36 | 497/497 | 60/60 | nenhum | 0 de 6 |

A rodada 01 passou em tudo, mas os relatos dos agentes mostraram 18 problemas nas skills. Eles viraram as melhorias da v2. Na rodada 02:
- o `pip-audit` não encontrou vulnerabilidades;
- nenhum HTTP 500 com valores extremos;
- testes antes do código em todas as execuções;
- cerca de 23% menos chamadas de ferramenta.

**Bônus do desafio:**
- Resultado de testes e scans: feito.
- Skill dedicada à segurança: feito.
- Pacote rodado em dois agentes diferentes: **feito**. O Codex CLI rodou o pedido de treino com as mesmas skills e o prompt da banca, sem nenhuma alteração: 6/6 gates, 32/32 testes e 10/10 critérios via HTTP, em 18 minutos ([comparação](evidencias/testes-pacote/codex/)). Ele escreveu menos testes que o Claude Code (32 contra 89) e escolheu outro status num caso ambíguo da regra 409 ou 422.

## 5. Onde a IA errou e como corrigi

Registro completo no [diário de decisões](evidencias/diario-de-decisoes.md), tabela "Onde a IA errou".

- **O modelo de projeto que a IA escreveu tinha uma vulnerabilidade conhecida** (CVE-2025-62727 no `FileResponse` da versão fixada do starlette) **e permitia HTTP 500 com valores extremos.** As seis execuções da rodada 01 acharam e contornaram os dois problemas nas revisões. A v2 corrigiu na origem: stack atualizada com `pip-audit` limpo, e tipos com limites.
- **Instruções contraditórias ou impossíveis:**
  - a revisão exigia domínio sem FastAPI, mas o modelo forçava o import;
  - havia dois gates para a mesma etapa;
  - o limite de 60 linhas para o PRD não cabia no próprio modelo;
  - o "TDD um teste por vez" foi ignorado pelos seis agentes.

  Os agentes de teste detectaram tudo, e a v2 corrigiu.
- **Exemplo contraditório na regra 409 ou 422 (ainda na v2):** a IA listou "prazo" como 422, mas o teste de decisão que ela mesma escreveu leva a 409 quando o prazo depende de dado guardado. Quatro agentes apontaram e resolveram de forma consistente. É a próxima correção.
- **Pedido de teste com contradição:** o P04, escrito pela IA, tinha regras de saldo contraditórias. O agente resolveu com premissa e teste.
- **Comportamento dos agentes:** horários do log estimados e arquivos temporários fora da pasta de trabalho. A v2 passou a mandar ler o relógio por comando e proibiu escrever fora da pasta. Ainda houve horários de fim corrigidos pelos próprios agentes.

Eu decidi cada etapa. Também corrigi o rumo quando a IA se perdeu em refino antes de ter uma execução completa (D-10 e D-11 do diário) e quando o pacote não tinha resposta para pedidos em partes (D-19).
