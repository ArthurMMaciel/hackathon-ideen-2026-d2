---
name: fabrica
description: Ponto de entrada da fábrica de software. Use sempre que pedirem para construir, gerar ou implementar um sistema a partir de um pedido em linguagem natural (por exemplo "construa o sistema descrito em PEDIDO.md dentro da pasta gerado/"). Conduz o agente, sem intervenção humana, pelas etapas concepcao, especificacao, construcao, revisao, revisao-seguranca e verificacao, com gate entre elas, até o sistema rodar e os critérios de aceite serem verificados.
---

# Fábrica · orquestrador

Você vai levar um pedido em linguagem natural até um sistema funcionando, percorrendo etapas fixas. Esta skill decide a ordem, verifica cada gate e mantém o log de evidências. O trabalho de cada etapa está na skill da etapa.

## Regras que valem para a execução inteira

1. **Ninguém vai responder perguntas.** Nunca pare para perguntar ao usuário. Diante de ambiguidade, escolha a interpretação mais simples que atende ao pedido e registre como premissa (`PR-xx`) no PRD.
2. **Nenhuma etapa é pulada.** Não escreva código de aplicação antes do gate da especificação. Não declare o trabalho pronto antes do gate da verificação.
3. **Tudo que é gerado fica em `gerado/`.** Evidências ficam em `evidencias/`. Não altere `skills/` nem o arquivo do pedido.
4. **Leia as referências antes da etapa 1:** [referencias/regras-transversais.md](referencias/regras-transversais.md) e [referencias/stack-padrao.md](referencias/stack-padrao.md). Elas valem para todas as etapas.
5. **Só dados fictícios.** Nenhum segredo, senha ou token real em código, configuração ou log.
6. **Não escreva nada fora da pasta de trabalho** (a que contém o pedido). Arquivos temporários e sondas vão em `gerado/.tmp/`, que já está no `.gitignore`. Use caminhos relativos a essa pasta.
7. **Horários do log vêm do relógio, nunca de estimativa.** No início e no fim de cada etapa rode `python -c "from datetime import datetime; print(datetime.now().strftime('%H:%M'))"` e copie a saída.

## Etapa 0 · Preparação

0. **Construção ou evolução?** Se `gerado/docs/PRD.md` já existe e o pedido é alterar, adicionar ou corrigir algo no sistema existente, não siga esta skill: use a skill `evolucao` (`../evolucao/SKILL.md`), que aplica a mudança sem refazer o sistema.
1. Localize o pedido, nesta ordem: o arquivo citado no prompt; `PEDIDO.md` na raiz; o único `PEDIDO*.md` na raiz; o texto do próprio prompt. Registre qual foi usado.
2. Confirme o ambiente com `python --version` (exige 3.11 ou superior). Se faltar, registre no log e pare com a mensagem de erro. Essa é a única parada permitida.
3. Crie `gerado/` e `evidencias/` se não existirem.
4. Inicie `evidencias/log-execucao.md` com o modelo de [referencias/modelo-log.md](referencias/modelo-log.md). Preencha agente, modelo, prompt de entrada (literal) e pedido usado.

## Etapas e gates

Execute em ordem. Para cada etapa: anote o início no log, siga a skill da etapa, passe pelo gate, anote o resultado no log.

A coluna "Gate" abaixo é um resumo. **O gate que vale é o checklist completo no fim da skill de cada etapa.** Registre no log esse checklist, item por item.

| # | Etapa | Skill | Saída principal | Gate (tudo precisa ser verdade) |
|---|---|---|---|---|
| 1 | Concepção | `concepcao` | `gerado/docs/PRD.md` | PRD com até uma página; todo requisito do pedido virou `RF-xx` ou `RN-xx`; premissas `PR-xx` registradas; seção "Fora de escopo" presente |
| 2 | Especificação | `especificacao` | `gerado/docs/SPEC.md` | Todo `RF`/`RN` aparece na especificação; todo endpoint tem contrato (método, caminho, entrada, saída, erros); todo `CA-xx` mapeado para endpoint e nome de teste |
| 3 | Construção | `construcao` | código e testes em `gerado/` | Instalação e testes rodam com os comandos de [referencias/stack-padrao.md](referencias/stack-padrao.md); todos os testes passam; existe pelo menos um teste por `CA-xx` com o código no nome |
| 4 | Revisão de qualidade | `revisao` | `evidencias/revisao.md` | Achados classificados; todo achado alto ou médio corrigido; testes passam de novo depois das correções |
| 5 | Revisão de segurança | `revisao-seguranca` | `evidencias/seguranca.md` | Checklist completo; todo achado alto ou médio corrigido; testes passam de novo |
| 6 | Verificação | `verificacao` | `evidencias/criterios-aceite.md` | Servidor sobe com um comando; todo `CA-xx` executado via HTTP contra o servidor real, com resultado registrado; tela web responde |

As skills das etapas ficam ao lado desta, em `../<nome-da-skill>/SKILL.md`. Se o agente já carregou as skills pelo nome, use-as pelo nome.

## Quando um gate falha

1. Corrija dentro da própria etapa e confira o gate de novo. São no máximo 3 tentativas por gate.
2. Se uma correção exigir voltar a uma etapa anterior (por exemplo, um teste revela um requisito mal especificado), volte, ajuste o artefato daquela etapa e registre a volta no log.
3. Depois de 3 tentativas, registre no log `GATE FALHOU`, com a causa e o que ficou pendente, e siga para a próxima etapa. A execução completa vale mais que uma parada silenciosa. Nunca marque como aprovado um gate que falhou.

## Encerramento

1. Confira `gerado/README.md` (escrito na construção): o que o sistema faz, como instalar, rodar, testar e verificar, e onde está a tela.
2. Feche o log com o quadro final: gates (aprovado ou falhou), testes (passaram/total), critérios de aceite (verificados/total), ajustes manuais (deve ser "nenhum") e pendências.
3. Responda ao usuário com o mesmo quadro final, em poucas linhas.

## Definição de pronto

- [ ] Os seis gates foram registrados no log.
- [ ] `gerado/` instala e roda do zero com os comandos documentados.
- [ ] Todos os testes passam.
- [ ] `evidencias/criterios-aceite.md` mostra cada `CA-xx` com resultado obtido via HTTP.
- [ ] Nenhum dado real e nenhum segredo em `gerado/` ou `evidencias/`.
