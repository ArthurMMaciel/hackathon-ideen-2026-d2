# Fábrica de software em skills · Hackathon Ideen 2026 · Desafio 2

## 1. O problema

Cada pessoa conduz o agente de IA do seu jeito, e não existe um processo reaproveitável que leve um pedido em linguagem natural até um sistema funcionando com o mínimo de ajuste manual.

## 2. O que eu fiz

Um pacote de 7 skills (`SKILL.md`) que conduz qualquer agente, sem intervenção humana, por quatro etapas obrigatórias mais duas de garantia, com um gate verificável entre elas:

```
PEDIDO.md
   │
   ▼
fabrica ── orquestra, mantém o log e confere cada gate
   │
   ├─ 1 concepcao          → gerado/docs/PRD.md   (RF, RN, premissas PR, fora de escopo, CA)
   ├─ 2 especificacao      → gerado/docs/SPEC.md  (DDL, contrato de cada endpoint, plano de testes)
   ├─ 3 construcao         → código + testes      (parte de um modelo de projeto testado)
   ├─ 4 revisao            → evidencias/revisao.md
   ├─ 5 revisao-seguranca  → evidencias/seguranca.md
   └─ 6 verificacao        → evidencias/criterios-aceite.md (cada CA executado via HTTP no servidor real)
```

O que diferencia o pacote de um gerador de aplicação genérico:

- **Rastreabilidade de ponta a ponta.** Todo trecho do pedido vira um código (`RF`, `RN`, `PR`), e todo `CA-xx` chega até um teste com o código no nome e a uma linha da evidência HTTP.
- **Gates objetivos.** Uma etapa só começa quando o checklist da anterior está marcado no log. Os agentes voltaram a etapas anteriores quando um teste ou uma revisão mostrou erro na SPEC.
- **Sem perguntas.** Lacunas do pedido viram premissas registradas, com uma lista fixa de lacunas comuns que o agente precisa conferir.
- **Modelo de projeto testado** (`skills/construcao/modelo-projeto/`) com a infraestrutura que todo pedido desse tipo precisa:
  - relógio injetável e `APP_AGORA`, para testar regras de "passado" e "futuro";
  - SQLite com transação que evita corrida;
  - tipos de entrada com limites, que evitam HTTP 500;
  - erros padronizados;
  - tela com CSS e funções prontas;
  - scripts que sobem o servidor real para verificar os critérios.
- **Evidências escritas pelas próprias skills.** Cada execução deixa log com horários, revisões, varredura de segurança e o resultado de cada critério via HTTP.

Stack padrão do sistema gerado: Python 3.11+, FastAPI, SQLite (biblioteca padrão), pytest e uma página HTML sem build.

## 3. Como reproduzir

### Rodar o pacote num pedido

1. Crie uma pasta vazia com `PEDIDO.md` (por exemplo, uma cópia de `PEDIDO-TREINO.md`) e as pastas vazias `gerado/` e `evidencias/`.
2. Instale as skills. Todas precisam ficar lado a lado, porque elas se referenciam por caminho relativo:
   - Claude Code: copie o conteúdo de `skills/` para `.claude/skills/` dentro da pasta, ou para `~/.claude/skills/`.
   - Outros agentes que leem `SKILL.md`: copie `skills/` para a pasta de skills do agente.
3. Abra o agente na pasta e use o prompt da banca:

   > Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

4. Requisitos: Python 3.11 ou superior e acesso à internet para o `pip`. Uma execução leva cerca de 25 minutos.

### Rodar o sistema gerado a partir do pedido de treino

A partir de `gerado/` (no Linux e no macOS, troque `.venv\Scripts\python` por `.venv/bin/python`):

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python verificacao/verificar_ca.py
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

A tela fica em `http://localhost:8000/` e a documentação da API em `http://localhost:8000/docs`.

## 4. Evidências

| O quê | Onde |
|---|---|
| Sistema gerado do pedido de treino | [`gerado/`](gerado/) |
| Log da execução (agente, modelo, prompt, etapas, gates) | [`evidencias/log-execucao.md`](evidencias/log-execucao.md) |
| Critérios de aceite verificados via HTTP | [`evidencias/criterios-aceite.md`](evidencias/criterios-aceite.md) |
| Revisão de qualidade e de segurança | [`evidencias/revisao.md`](evidencias/revisao.md), [`evidencias/seguranca.md`](evidencias/seguranca.md) |
| Diário de decisões participante × IA | [`evidencias/diario-de-decisoes.md`](evidencias/diario-de-decisoes.md) |
| Teste de generalização em 6 pedidos (pedidos, rodadas, relatos dos agentes) | [`evidencias/testes-pacote/`](evidencias/testes-pacote/) |
| Calibração isolada da etapa de concepção | [`evidencias/calibracao/`](evidencias/calibracao/) |

Tudo o que não é o pacote (`skills/`) nem o sistema gerado (`gerado/`) fica em `evidencias/`.

Agente e modelo: Claude Code com `claude-opus-5-5`, em subagentes com contexto limpo, num diretório só com as skills e o pedido, sem intervenção humana.

### Generalização: o mesmo pacote em 6 pedidos

Além do pedido de treino, escrevi 5 pedidos do mesmo tamanho e tipo, cada um forçando um tipo diferente de regra, para simular o pedido oculto.

| Rodada | Skills | Gates | Testes | CAs via HTTP | Ajuste manual |
|---|---|---|---|---|---|
| [01](evidencias/testes-pacote/rodadas/rodada-01/RESULTADOS.md) | v1 | 36/36 | 390/390 | 60/60 | nenhum |

A rodada 01 passou em tudo. Mesmo assim, a matriz de recorrência dos relatos dos agentes mostrou 18 problemas nas skills, seis deles em todas as execuções. Eles viraram as melhorias M1 a M12 das skills v2.

## 5. Onde a IA errou e como corrigi

O registro completo está no [diário de decisões](evidencias/diario-de-decisoes.md), na tabela "Onde a IA errou". Os principais:

- **O modelo de projeto que a IA escreveu tinha uma vulnerabilidade conhecida** (CVE-2025-62727, `FileResponse` na versão fixada do starlette) **e permitia HTTP 500 com valores extremos** (id gigante, ano 9999). As seis execuções da rodada 01 acharam e contornaram os dois problemas sozinhas nas etapas de revisão. A correção definitiva veio na v2: stack atualizada e verificada com `pip-audit` limpo, e tipos com limites.
- **Instruções contraditórias:** a revisão exigia domínio sem FastAPI, enquanto o modelo obrigava o domínio a importar um módulo com FastAPI. Também havia dois gates diferentes para a mesma etapa. Os dois casos foram detectados pelos próprios agentes de teste e corrigidos.
- **Instrução impossível de seguir:** a IA exigiu TDD um teste por vez. Nenhum dos seis agentes seguiu. Na v2 a regra virou "testes em lote, com a rodada de falhas registrada no log".
- **Limite mal calibrado:** a IA fixou "60 linhas" para o PRD sem conferir com o próprio modelo de PRD. A calibração mostrou o conflito.
- **Pedido de teste com contradição:** a IA escreveu o pedido P04 com regras de saldo contraditórias. O agente percebeu e resolveu com premissa e teste, o que motivou uma lacuna nova na concepção.
- **Comportamento dos agentes:** horários do log inventados em vez de lidos do relógio, e arquivos temporários escritos fora da pasta de trabalho (apagados em seguida). Na v2, a skill `fabrica` manda ler o relógio com um comando e proíbe escrever fora da pasta.
- **Comunicação:** a IA apresentou a escolha de stack como "Python ou Node" sem deixar claro que as duas incluíam a tela. O participante questionou e a explicação foi refeita.

O participante decidiu cada etapa e corrigiu o rumo quando a IA se perdeu em refino antes de ter uma execução completa (decisões D-10 e D-11 do diário).
