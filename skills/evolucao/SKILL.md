---
name: evolucao
description: Mudança incremental num sistema já construído pela fábrica. Use quando gerado/docs/PRD.md já existe e o pedido é alterar, adicionar ou corrigir algo ("agora quero...", "adicione...", "mude a regra..."), em vez de construir do zero. Atualiza PRD e SPEC só no que muda, escreve os testes da mudança antes do código, implementa, roda a suíte inteira contra regressão e verifica via HTTP. Meta de poucos minutos por mudança.
---

# Evolução · mudança incremental

Objetivo: aplicar uma mudança pedida em linguagem natural a um sistema que já existe em `gerado/`, com o mesmo rigor da fábrica e uma fração do tempo. **Nada é refeito do zero.**

## Regras

1. **Velocidade:** não releia o projeto inteiro. Leia `gerado/docs/PRD.md`, `gerado/docs/SPEC.md` e só os arquivos de código que a mudança toca (encontre-os com busca por nome de rota, tabela ou código `RN-xx`).
2. **Não reinstale o ambiente.** Use o `.venv` existente em `gerado/`. Só instale se ele não existir ou se a mudança alterar `requirements.txt`.
3. **Ninguém responde perguntas.** Lacuna vira premissa `PR-xx` nova.
4. As regras da fábrica continuam valendo: tipos de `app/tipos.py`, regra 409 ou 422, relógio injetável, SQL parametrizado, nada fora da pasta de trabalho, horários lidos com `python -c "from datetime import datetime; print(datetime.now().strftime('%H:%M:%S'))"`.

## Passo a passo

1. **Horário de início** (comando acima).
2. **Entenda a mudança** e classifique cada parte: requisito novo, regra alterada, regra nova ou correção. Escreva os critérios de aceite da mudança, continuando a numeração (`CA-11`, `CA-12`...). Se o pedido já trouxer critérios, use-os.
3. **PRD e SPEC por delta.** Acrescente os códigos novos (`RF`, `RN`, `PR`, `CA`) continuando a numeração. Em itens alterados, mantenha o código e acrescente "(alterado na evolução N)". Na SPEC: endpoints, DDL e linhas do plano de testes só do que muda. Mudança de esquema em banco existente: `ALTER TABLE` idempotente em `banco.ESQUEMA` ou coluna nova com valor padrão; nunca apague dados.
4. **Testes da mudança primeiro.** Escreva só os testes novos ou alterados do plano. Rode só esses arquivos ou nomes (`PY -m pytest -q -k "ca_11 or rn_12"`) e registre a linha de falhas.
5. **Implemente o mínimo** em `dominio/`, `repositorio/`, `rotas/` e, se a mudança aparece na tela, em `estatico/index.html`.
6. **Regressão:** rode a suíte inteira (`PY -m pytest -q`). Tudo verde. Teste antigo que quebrou por causa de uma regra que o pedido mudou de propósito é atualizado e citado no log; qualquer outra quebra é bug da mudança.
7. **Segurança da mudança:** se ela trouxe entrada nova, acrescente em `tests/test_seguranca.py` um caso de valor extremo e um de injeção para o campo novo. Se mexeu em SQL, confira que todo dado entra por `?`.
8. **Verificação:** acrescente em `verificacao/verificar_ca.py` um bloco por `CA` novo e rode o script inteiro (ele verifica também os critérios antigos, em segundos).
9. **Log:** acrescente em `evidencias/log-evolucao.md` (crie se não existir) o bloco abaixo, com horário de fim lido do relógio.

```markdown
## Evolução <N> · <título curto>

- **Pedido:** > <texto literal>
- **Início / fim:** <hh:mm:ss> / <hh:mm:ss>
- **Códigos novos ou alterados:** <RF, RN, PR, CA>
- **Arquivos alterados:** <lista>
- **Testes da mudança antes do código:** <linha do pytest>
- **Suíte completa depois:** <linha do pytest>
- **Critérios via HTTP:** <n>/<total>
- **Testes antigos alterados:** nenhum | <teste e motivo>
```

## Gate da evolução

- [ ] PRD e SPEC têm os códigos novos ou alterados da mudança.
- [ ] A rodada de testes da mudança antes do código está no log, com falhas.
- [ ] `PY -m pytest -q` passa inteiro.
- [ ] `verificacao/verificar_ca.py` passa, incluindo os critérios novos.
- [ ] `evidencias/log-evolucao.md` tem o bloco da evolução com horários reais.
