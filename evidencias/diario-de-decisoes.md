# Diário de decisões · Participante × IA

Registro cronológico de como a IA foi usada no planejamento e na implementação: o que a IA propôs, o que o participante perguntou, contestou ou decidiu, e onde a IA errou ou foi imprecisa.

**Agente:** Claude Code (app desktop) · **Modelo:** Claude Opus 5.5 (`claude-opus-5-5`)
**Data:** 23/10/2026

## Regra de trabalho combinada

- A IA propõe, o participante decide. Nenhuma etapa de planejamento ou implementação avança sem aprovação explícita do participante.
- Toda decisão relevante entra aqui com: contexto, proposta da IA, intervenção do participante, decisão final e quem decidiu.
- Erros e imprecisões da IA são registrados aqui e alimentam a seção "Onde a IA errou" do README.

## Legenda

- **[IA]**: proposta ou ação da IA
- **[P]**: intervenção do participante (pergunta, contestação, direcionamento)
- **[D]**: decisão final

---

## D-01 · Entendimento do desafio

- **[P]** Pediu para a IA ler a apresentação do hackathon e dizer qual é o nosso problema. Direcionamento inicial: fugir de uma solução genérica no estilo Lovable.
- **[IA]** Leu os 15 slides pelo conector do Google Drive. Identificou o Desafio 2 (Desenvolvimento agêntico): um pacote de arquivos `SKILL.md` que leva qualquer agente de um pedido em linguagem natural até um sistema funcionando, cobrindo concepção, especificação, construção e revisão. Resumiu os pesos da avaliação (35/30/20/15) e os bônus.
- **[IA]** Observação crítica: a entrega pedida é, na essência, o que o Lovable faz (pedido → app). A diferenciação precisa vir do processo: rastreabilidade entre etapas, gates, evidências automáticas e generalização para o pedido oculto.
- **[D]** Participante aceitou a leitura e autorizou baixar o kit. *(Decidido por: participante)*

## D-02 · Download e leitura do kit

- **[P]** Autorizou explicitamente o download de `hackathon-2026-d2-kit.zip` do Drive para o projeto.
- **[IA]** Baixou, extraiu em diretório isolado, conferiu o conteúdo (apenas `.md` e `.gitkeep`) e copiou para o projeto.
- **[IA]** Achados do kit:
  - A banca roda um prompt fixo, sem intervenção humana, apontando para um arquivo chamado `PEDIDO.md`.
  - Como ninguém responde perguntas durante a execução, as skills precisam registrar premissas em vez de perguntar.
  - O fim da execução é "critérios de aceite verificados".
  - O pedido de treino (reserva de salas) tem 10 critérios de aceite e várias regras de tempo, que exigem relógio injetável e intervalos semiabertos.
- **[D]** Kit incorporado ao repositório. *(Decidido por: participante)*

## D-03 · Desenho do pacote de skills (proposta)

- **[IA]** Propôs a estrutura:
  - `fabrica/`: orquestrador e ponto de entrada.
  - `concepcao/`, `especificacao/`, `construcao/`, `revisao/`: as quatro etapas.
  - `revisao-seguranca/`: bônus.
  - `verificacao/`: roda os critérios de aceite contra o servidor real.

  Diferenciais propostos: IDs rastreáveis (RF/RN → CA → teste → resultado), gate entre etapas, log de evidências escrito pelas próprias skills, skills genéricas (sem menção a salas) e portabilidade Claude/Codex.
- **[IA]** Apontou o risco de overfitting no pedido de treino e propôs validar o pacote também num pedido inventado do mesmo tipo.
- **[P]** Aprovou a estrutura e definiu o ritmo: começar pelo orquestrador (`fabrica`) e mostrar cada skill antes de passar para a próxima.
- **[D]** Estrutura aprovada. Implementação skill por skill, com revisão do participante entre elas. *(Decidido por: participante)*

## D-04 · Stack padrão do sistema gerado

- **[IA]** Recomendou Python + FastAPI + SQLite + pytest. Ofereceu Node 22 + TypeScript como alternativa.
- **[P]** Contestou: não entendeu a diferença entre as duas opções e perguntou se o sistema seria só uma API, sem front.
- **[IA]** Esclareceu que as duas opções geram o mesmo sistema (API REST + tela web + banco local) e que só a linguagem do backend muda. A tela é obrigatória pelo pedido.
- **[IA]** Justificou HTML simples em vez de React: nenhum critério de aceite testa a interface, e um build extra aumenta o risco de falha sem intervenção humana.
- **[IA]** Justificou Python em vez de Node: o SQLite vem na biblioteca padrão do Python. No Node, as opções são um módulo experimental (`node:sqlite`) ou uma biblioteca com compilação nativa no Windows (`better-sqlite3`).
- **[D]** Python + FastAPI + SQLite + pytest, com tela em HTML e JavaScript simples servida pela própria API. *(Decidido por: participante, com "Ok" após a explicação; confirmar se houver dúvida)*

## D-05 · Registro do uso de IA

- **[P]** Pediu que toda a discussão de plano e implementação fosse anotada, porque a banca avalia como a IA é usada, e deixou claro que a IA não deve fazer tudo por conta própria.
- **[D]** Criado este diário. A IA passa a pedir aprovação a cada etapa e a registrar cada decisão aqui. *(Decidido por: participante)*

## D-06 · Repositório git

- **[P]** Pediu para inicializar o git.
- **[IA]** Inicializou o repositório na branch `main` e criou `.gitignore` (ambiente virtual, cache, banco local, `.env`). Nenhum commit feito, aguardando o participante.
- **[D]** Repositório inicializado. *(Decidido por: participante)*

## D-07 · Versões da stack verificadas antes de entrar na skill

- **[IA]** Antes de escrever as versões na skill, instalou a stack num ambiente descartável e rodou um teste mínimo (FastAPI + TestClient + SQLite). Resultado: Python 3.11.0, fastapi 0.115.6, uvicorn 0.32.1, pytest 8.3.4, httpx 0.28.1, SQLite 3.38.4, tudo funcionando.
- **[D]** Versões fixadas em `skills/fabrica/referencias/stack-padrao.md`. *(Decidido por: IA, dentro da stack aprovada em D-04)*

## D-08 · Skill `fabrica` (orquestrador) · aguardando revisão

- **[IA]** Escreveu `skills/fabrica/SKILL.md` e três referências: `regras-transversais.md`, `stack-padrao.md` e `modelo-log.md`.
- **[IA]** Escolhas feitas pela IA que o participante precisa revisar:
  1. **Falha de gate:** até 3 tentativas; depois registra `GATE FALHOU` e segue para a próxima etapa, em vez de parar.
  2. **Códigos HTTP:** `409` para conflito com estado existente, `422` para regra de negócio e validação, `404` para recurso inexistente.
  3. **Fuso padrão:** `America/Sao_Paulo`, com horário obrigatoriamente com offset na API.
  4. **Relógio injetável obrigatório** em toda regra de passado, futuro ou hoje.
  5. **Única parada permitida:** Python 3.11+ ausente.
- **[P]** Revisou a skill e as cinco escolhas e aprovou sem alterações.
- **[D]** `fabrica` aprovada com as cinco escolhas como propostas. *(Decidido por: participante)*

## D-09 · Skill `concepcao` · aguardando revisão

- **[P]** Pediu a skill de concepção depois de aprovar a `fabrica`.
- **[IA]** Escreveu `skills/concepcao/SKILL.md` e `skills/concepcao/modelo-prd.md`. Também acrescentou ao `modelo-log.md` da `fabrica` o espaço para a tabela de cobertura do pedido.
- **[IA]** Escolhas feitas pela IA que o participante precisa revisar:
  1. **Cobertura frase a frase:** todo trecho do pedido precisa apontar para um código. Trecho sem código é tratado como lacuna.
  2. **A tabela de cobertura fica no log de execução**, fora do PRD, para o PRD caber em uma página (cerca de 60 linhas).
  3. **Lista fixa de lacunas comuns**, que o agente confere sempre (fuso, bordas, o que "cadastro" cobre, unicidade, validação de campos, efeito de mudança de status, definição de período, arredondamento, ordenação). A skill não decide a resposta, só obriga a registrar uma premissa.
  4. **Pedido sem critérios de aceite:** o agente cria um caminho feliz por `RF` e uma recusa por `RN`.
  5. **Fora de escopo fixo do desafio** (deploy, integração com sistema real, dados reais) sempre incluído.
- **[P]** Antes de aprovar, pediu para rodar só a etapa de concepção no pedido de treino e ver o PRD produzido.
- **[D]** Aprovação suspensa até a calibração (D-10). *(Decidido por: participante)*

## D-10 · Calibração da concepção no pedido de treino

- **[IA]** Rodou a etapa num subagente com contexto limpo, num diretório que continha só `skills/` e `PEDIDO.md`, para o conhecimento da conversa não contaminar o resultado. Evidência em `evidencias/calibracao/01-concepcao/`.
- **[IA]** Avaliação do PRD produzido:
  - **Pontos fortes:** os 10 CAs estão mapeados; a regra de sobreposição saiu com a fórmula correta e o encosto permitido; as bordas de duração estão explícitas; a ocupação recorta a parte da reserva fora da janela das 8h às 18h; as canceladas ficam fora de conflito, agenda e ocupação.
  - **Problemas nas skills:** sete, listados no README da calibração. Os mais relevantes são o limite de uma página incompatível com o modelo, os dois gates para a mesma etapa e a lista de lacunas que não pode ser verificada.
- **[IA]** Propôs seis correções nas skills (ver E-02 a E-04). Não aplicadas, aguardando o participante.
- **[P]** Antes de decidir, questionou se a IA tinha entendido o problema e o que precisava ser feito.
- **[IA]** Recapitulou o problema e reconheceu o desvio de foco: estava refinando a concepção sem ter nenhuma execução completa, que vale 35% da nota.
- **[D]** Ver D-11. *(Decidido por: participante)*

## D-11 · Mudança de abordagem: execução completa primeiro, refino depois

- **[IA]** Propôs a ordem: (1) escrever as skills que faltam de forma direta, (2) rodar tudo de ponta a ponta no pedido de treino, (3) refinar com base no que quebrar.
- **[P]** Concordou com a ordem. Pediu skills o mais assertivas possível e um ciclo contínuo de gerar testes e resultados, melhorando a partir deles. Liberou a escrita das skills restantes sem revisão uma a uma.
- **[D]** As correções simples de D-10 entram junto com a escrita das skills restantes. Depois vem a primeira execução completa. *(Decidido por: participante)*
- **[IA]** Aplicou as correções de D-10 (limite do PRD por linhas de item, gate único por etapa, tabela de lacunas no log, termos do pedido permitidos, formato de data movido para a especificação, coluna de resultado esperado).
- **[IA]** Criou `skills/construcao/modelo-projeto/`, uma base de projeto já funcionando: relógio injetável com `APP_AGORA`, SQLite com transação `BEGIN IMMEDIATE`, formato de erro padrão, `conftest` com relógio que avança e script de verificação que sobe o servidor real. Testada numa cópia descartável: 2 testes passaram e a verificação via HTTP gravou a evidência.
- **[IA]** Achado durante o teste: no Windows, `zoneinfo` precisa do pacote `tzdata`, que entrou no `requirements.txt` do modelo.

## D-12 · Repositório remoto

- **[P]** Pediu para criar o repositório com o layout do desafio e subir o que já foi feito. Comentou que não entendeu se o banco é mesmo necessário, para discutir depois.
- **[IA]** Confirmou que o repositório ainda não existia na organização e o criou como privado, com o nome do padrão do desafio, `ideen-tech/hackathon-2026-d2-arthurmm3-ideentech`.
- **[D]** Repositório criado e primeiro commit enviado. A discussão sobre o banco fica pendente. *(Decidido por: participante)*

## D-13 · Skills restantes e primeira execução completa

- **[IA]** Escreveu as skills `especificacao` (com `modelo-spec.md`), `construcao`, `revisao`, `revisao-seguranca` e `verificacao`. Atualizou `stack-padrao.md` para tornar obrigatório partir do modelo de projeto.
- **[IA]** Escolhas da IA nessas skills:
  1. **Testes antes do código:** um teste por linha do plano, rodado antes de implementar.
  2. **Divisão fixa do código:** `dominio/` (regras puras, recebem `agora`), `repositorio/` (SQL), `rotas/` (HTTP).
  3. **Verificação contra o servidor real**, com o tempo "passando" por reinício do servidor com outro `APP_AGORA`.
  4. **Segurança com testes de ataque** (injeção de SQL, XSS, entrada fora do limite) que ficam na suíte.
  5. **`pip-audit` opcional:** sem rede, a execução registra o motivo e segue.
- **[IA]** Iniciou a primeira execução completa num subagente com contexto limpo, num diretório só com `skills/` e `PEDIDO.md`, usando o prompt exato da banca.
- **[D]** Resultado em análise. *(Pendente)*

## D-14 · Rodada 01: cinco pedidos novos em paralelo

- **[P]** Viu a tela gerada pela execução em andamento e questionou a qualidade e a origem dela. Depois pediu cerca de 5 testes novos, rodados por subagentes, com pedidos e resultados salvos, para melhorar o pacote a partir dos resultados.
- **[IA]** Confirmou que a tela veio da execução completa (gates 1 a 4 aprovados naquele momento). Avaliação crítica da tela: funcional e com XSS bloqueado, mas visual cru, tabela que transborda e um "Failed to fetch" provavelmente causado pelo servidor sendo derrubado pela verificação.
- **[IA]** Escreveu 5 pedidos novos em `evidencias/testes-pacote/pedidos/`, cada um forçando um tipo de regra diferente: estado de item e limites por tipo (P01), dinheiro e fluxo de aprovação (P02), lista de espera (P03), datas sem horário e restrição por equipe (P04), prazo em horas e máquina de estados (P05).
- **[IA]** Corrigiu o harness de verificação, que usava a porta fixa 8765 e colidiria em execuções paralelas. Agora escolhe uma porta livre. Testado.
- **[IA]** Commit `31c3c44` enviado. O GitHub avisou que a `main` exige pull request e que a regra foi contornada pela permissão da conta. Daqui em diante, nada vai direto para a `main` sem decisão do participante.
- **[IA]** Disparou as 5 execuções em subagentes paralelos, cada uma num diretório limpo e com o prompt da banca.
- **[D]** Rodada 01 em andamento: P00 (treino) mais P01 a P05. *(Decidido por: participante)*

## D-15 · Resultado da rodada 01 e melhorias propostas

- **[IA]** As seis execuções terminaram: 36/36 gates, 390/390 testes, 60/60 critérios de aceite verificados via HTTP e nenhum ajuste manual. Artefatos e relatos em `evidencias/testes-pacote/rodadas/rodada-01/`.
- **[IA]** Cruzou os relatos dos seis agentes e montou a matriz de recorrência em `evidencias/testes-pacote/rodadas/rodada-01/RESULTADOS.md`. Seis problemas apareceram em todas as execuções; quatro deles foram causados pelo modelo de projeto escrito pela IA (ver E-05 a E-08).
- **[IA]** Propôs 12 melhorias (M1 a M12), ordenadas por impacto. Não aplicadas, aguardando o participante.
- **[P]** Aprovou as 12 melhorias e pediu a rodada 02 com os 6 pedidos em paralelo.
- **[D]** M1 a M12 aprovadas. *(Decidido por: participante)*

## D-16 · Melhorias M1 a M12 aplicadas (skills v2)

- **[IA]** Às 07:14 de 26/10, alertou que o prazo é 09:00 do mesmo dia e que `gerado/` e o `README.md` final ainda não estavam no repositório. Criou a branch `rodada-02` para não enviar mais nada direto à `main`.
- **[IA]** Modelo de projeto:
  - **M1:** stack atualizada para fastapi 0.162.0, starlette 1.10.0, uvicorn 0.54.0, pytest 9.1.1, com todas as dependências transitivas fixadas. `pip-audit` no `requirements.txt`: nenhuma vulnerabilidade conhecida.
  - **M2:** tela servida com `HTMLResponse`.
  - **M3:** `app/tipos.py` com `Id`, `DataHora`, `Data`, `Texto`, `TextoLongo`, `Email` e `Centavos`.
  - **M4:** erros de negócio movidos para `app/dominio/erros.py`, sem FastAPI.
  - **M5:** `carga_inicial(conn, agora)`, com o ciclo de vida usando o mesmo relógio das rotas.
  - **M9:** harness em porta livre e saída UTF-8, com `resumo()` dos campos conferidos e linhas ordenadas; novo `subida_manual.py`.
  - **M11:** CSS e funções de tela prontas (`mostrarMensagem`, `lerFormulario`, `desenharTabela`).
  - **Testes:** novos testes dos tipos e do relógio da carga inicial. O modelo passou com 12 testes, verificação e subida manual.
- **[IA]** Skills e regras:
  - **M6:** o pedido prevalece sobre as regras; seção de datas sem horário; teste de decisão 409 ou 422.
  - **M7:** testes em lote, com a rodada de falhas registrada no log e exigida no gate.
  - **M8:** proibição de escrever fora da pasta de trabalho; horários lidos do relógio.
  - **M10:** checklists ajustados (valores extremos, conferência da tela sem navegador, grep de SQL, `.gitignore`, `pip-audit`).
  - **M12:** lacunas novas na concepção e limite do PRD em 70 linhas de itens.
- **[D]** Skills v2 prontas para a rodada 02. *(Decidido por: participante)*
- **[IA]** Preparou a entrega como rede de segurança na branch `rodada-02` (README com os cinco itens, `gerado/` e evidências da rodada 01) e propôs enviar a branch e abrir o PR antes do fim da rodada 02.
- **[P]** Decidiu esperar a rodada 02 terminar antes de enviar a branch e abrir o PR.

## D-17 · Estrutura do repositório

- **[P]** Perguntou se o diário pode ficar em `evidencias/` e se pastas fora do esqueleto do kit são aceitas, pedindo confirmação sem edição.
- **[IA]** Conferiu o slide 12 e o README do kit: os obrigatórios são `skills/`, `gerado/`, `evidencias/` e `README.md`, sem proibição de pastas extras. O diário é evidência de uso de IA e cabe em `evidencias/`. Apontou o risco de a banca não abrir `testes-pacote/`, que estava fora do esqueleto, e sugeriu movê-la para dentro de `evidencias/`.
- **[D]** `testes-pacote/` movida para `evidencias/testes-pacote/`, com links do README e do diário ajustados. *(Decidido por: participante)*

---

## Onde a IA errou ou foi imprecisa

| # | Situação | Erro ou imprecisão | Como foi corrigido |
|---|---|---|---|
| E-01 | Proposta de stack (D-04) | A IA apresentou as opções de stack como escolha entre "Python" e "Node" sem deixar claro que ambas incluíam a tela web. A apresentação levou o participante a entender que poderia ser só API. | O participante questionou. A IA refez a explicação com uma tabela por camada (API, banco, testes, tela) e explicitou que a tela é requisito do pedido. |
| E-02 | Skill `concepcao` (D-09) | A IA fixou "cerca de 60 linhas" para o PRD sem conferir contra o próprio modelo de 9 seções em tabela. Num pedido pequeno o PRD já passa de 70 linhas. | Detectado na calibração 01. Correção proposta em D-10. |
| E-03 | Skills `fabrica` e `concepcao` | A IA escreveu dois gates diferentes para a mesma etapa (4 itens na `fabrica`, 7 na `concepcao`), sem dizer qual vale. | Detectado na calibração 01. Correção proposta em D-10. |
| E-04 | Skill `concepcao` | O item de gate "toda lacuna virou premissa" depende só do julgamento do agente, então não pode ser verificado. | Detectado na calibração 01. Corrigido em D-11 com a tabela de lacunas no log. |
| E-05 | Modelo de projeto | A IA serviu a tela com `FileResponse`, exposto à CVE-2025-62727 na versão fixada do starlette, e fixou versões com CVEs conhecidas sem rodar `pip-audit` antes. | As seis execuções da rodada 01 acharam e contornaram o problema sozinhas. Correção proposta em M1 e M2. |
| E-06 | Modelo de projeto | A IA não limitou ids nem anos, e o SQLite e a conversão para UTC geram HTTP 500 com valores extremos. | Achado pela revisão em todas as execuções. Correção proposta em M3. |
| E-07 | Modelo de projeto e skill `revisao` | A IA colocou as exceções de negócio num módulo que importa FastAPI e, na revisão, exigiu domínio sem FastAPI. As duas instruções se contradizem. | Apontado em todas as execuções. Correção proposta em M4. |
| E-08 | Skill `construcao` | A IA exigiu TDD um teste por vez, caro demais e impossível de verificar no gate. Nenhum agente seguiu. | Correção proposta em M7: lote de testes com rodada de falhas registrada. |
| E-09 | Pedido de teste P04 | A IA escreveu um pedido com regras de saldo que se contradizem. | O agente da execução percebeu e resolveu com premissa e teste. Motivou a lacuna nova de M12. |
