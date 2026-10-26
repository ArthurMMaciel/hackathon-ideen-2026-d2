---
name: verificacao
description: Etapa 6 e final da fábrica. Sobe o sistema gerado do zero (ambiente novo, banco novo), executa cada critério de aceite CA-xx via HTTP contra o servidor real e grava evidencias/criterios-aceite.md. Use depois do gate da revisão de segurança, para provar que o sistema roda e atende ao pedido.
---

# Verificação · critérios de aceite no servidor real

Objetivo: provar, fora dos testes unitários, que o sistema instala, sobe e atende cada critério de aceite. É a evidência principal da entrega.

## Passo a passo

1. **Instalação limpa.** Em `gerado/`, apague `.venv/` e `dados/`. Crie o ambiente e instale com os comandos da stack padrão. Registre no log se funcionou.
2. **Testes.** `PY -m pytest -q`. Registre a última linha.
3. **Critérios de aceite via HTTP.** `PY verificacao/verificar_ca.py`. O script sobe o uvicorn real, executa um bloco por `CA-xx` e grava `evidencias/criterios-aceite.md`.
   - Confira que o arquivo tem uma linha por `CA-xx` do PRD, mais a linha `TELA`.
   - Se algum CA falhar: descubra se o erro está no sistema ou no script. Corrija o lado errado. Se a correção for no sistema, rode os testes de novo. Repita o passo 3.
4. **Subida manual.** Rode `PY verificacao/subida_manual.py`. Ele sobe o servidor com o relógio real e banco novo numa porta livre, confere `/api/saude`, `/` e `/docs`, derruba o servidor e grava `evidencias/subida-manual.md`. Registre o resultado no log.
5. **Feche o log** com o quadro final da skill `fabrica`.

## O que não fazer

- Não marque um CA como aprovado sem a requisição real registrada no arquivo.
- Não altere o resultado esperado de um CA para fazê-lo passar. O esperado vem do pedido.
- Não deixe o servidor rodando no fim.

## Gate da verificação

- [ ] Instalação num `.venv` novo funcionou.
- [ ] `PY -m pytest -q` passa.
- [ ] `evidencias/criterios-aceite.md` existe, com uma linha por `CA-xx` do PRD e a linha `TELA`, todas `PASSOU`.
- [ ] `evidencias/subida-manual.md` existe com as três linhas `PASSOU`.
- [ ] Nenhum processo do servidor ficou rodando.
