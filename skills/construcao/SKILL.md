---
name: construcao
description: Etapa 3 da fábrica. Constrói o sistema em gerado/ a partir de gerado/docs/SPEC.md, partindo do modelo de projeto testado (modelo-projeto/), com testes escritos antes do código para cada CA-xx e RN-xx, até todos passarem. Use depois do gate da especificação.
---

# Construção · código e testes

Objetivo: implementar exatamente o que a SPEC descreve, com cada critério de aceite coberto por teste automatizado.

Leia antes: `../fabrica/referencias/regras-transversais.md`, `../fabrica/referencias/stack-padrao.md` e `gerado/docs/SPEC.md`.

## Passo a passo

1. **Copie o modelo.** Copie todo o conteúdo de [modelo-projeto/](modelo-projeto/) para `gerado/`, mantendo `gerado/docs/`. Não copie `.venv`, `dados/` nem `__pycache__`.
2. **Prepare o ambiente** com os comandos da stack padrão (criar `.venv`, instalar). Rode `PY -m pytest -q`: os 2 testes do modelo precisam passar antes de qualquer mudança. Se falharem, o problema é de ambiente; registre e corrija antes de seguir.
3. **Banco.** Coloque o DDL da SPEC em `banco.ESQUEMA` e implemente `banco.carga_inicial` (só insere se a tabela estiver vazia).
4. **Para cada linha do plano de testes da SPEC, na ordem:**
   1. Escreva o teste em `tests/` com o nome do plano (`test_ca_XX_...` ou `test_rn_XX_...`). Use as fixtures `cliente` e `relogio` do `conftest.py` e a função `iso()` para horários.
   2. Rode só esse teste e confirme que falha pelo motivo esperado.
   3. Implemente o mínimo para passar, nesta divisão:
      - `app/dominio/`: regras puras, recebem dados e `agora`, levantam `regra_violada`, `conflito` ou `nao_encontrado`. Comentário `# RN-xx` em cada regra.
      - `app/repositorio/`: SQL parametrizado, conversão de datas com `relogio.para_banco` e `relogio.do_banco`.
      - `app/rotas/`: um `APIRouter` por recurso, modelos Pydantic de entrada e saída, `Depends(obter_conexao)` e `Depends(obter_agora)`. Registre o router em `criar_app`.
   4. Rode a suíte inteira. Tudo verde antes de ir para a próxima linha.
5. **Validação de entrada com Pydantic.** Datas com `AwareDatetime` (recusa horário sem fuso). Inteiros com `Field(ge=..., le=...)`. Textos obrigatórios com `Field(min_length=1)`. E-mail validado por expressão regular simples no modelo, sem dependência nova.
6. **Concorrência.** Toda escrita que depende de uma leitura (conferir conflito e inserir, conferir status e cancelar) roda dentro de `with banco.transacao(conn):`.
7. **Tela.** Complete `app/estatico/index.html` conforme a seção Tela da SPEC. Use a função `api()` que já está no modelo. Mostre dados com `textContent` ou criando elementos, nunca com `innerHTML` de dados da API. Mostre a mensagem de erro da API quando uma ação for recusada.
8. **Verificação via HTTP.** Em `verificacao/verificar_ca.py`, escreva um bloco por `CA-xx`: requisições reais contra `servidor(...)` e `v.registrar(...)` com o resultado. Para cenários em que o tempo precisa passar, feche o servidor e abra outro com `APP_AGORA` posterior e o mesmo banco. Esse script roda na etapa de verificação, mas é escrito aqui.
9. **README do sistema.** Escreva `gerado/README.md`: o que faz, comandos de instalar, testar, rodar e verificar, e o endereço da tela.
10. **Confira o gate.**

## Quando um teste não passa

- Corrija o código. Altere o teste só se ele contradiz a SPEC, e registre no log o motivo.
- Se a SPEC estiver errada ou incompleta, volte à especificação, corrija a SPEC e registre a volta no log.
- Nunca use `skip`, `xfail` ou asserção enfraquecida para fechar o gate.

## Gate da construção

- [ ] `PY -m pip install -r requirements.txt` funciona num `.venv` novo.
- [ ] `PY -m pytest -q` passa sem falhas. Registre no log a última linha da saída (ex.: `24 passed`).
- [ ] Existe pelo menos um teste `test_ca_XX_...` para cada `CA-xx` do PRD.
- [ ] Existe teste de borda para cada `RN-xx` com limite numérico.
- [ ] Todo endpoint da SPEC está implementado; nenhum endpoint fora da SPEC.
- [ ] Nenhum `datetime.now()` fora de `app/relogio.py`.
- [ ] `verificacao/verificar_ca.py` tem um bloco por `CA-xx`.
- [ ] `gerado/README.md` existe com os comandos.
