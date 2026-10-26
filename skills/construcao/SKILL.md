---
name: construcao
description: Etapa 3 da fábrica. Constrói o sistema em gerado/ a partir de gerado/docs/SPEC.md, partindo do modelo de projeto testado (modelo-projeto/), com todos os testes do plano escritos e vistos falhando antes da implementação, até todos passarem. Use depois do gate da especificação.
---

# Construção · código e testes

Objetivo: implementar exatamente o que a SPEC descreve, com cada critério de aceite coberto por teste automatizado.

Leia antes: `../fabrica/referencias/regras-transversais.md`, `../fabrica/referencias/stack-padrao.md` e `gerado/docs/SPEC.md`.

## Passo a passo

1. **Copie o modelo.** Copie todo o conteúdo de [modelo-projeto/](modelo-projeto/) para `gerado/`, inclusive `.gitignore`, mantendo `gerado/docs/`. Não copie `.venv`, `dados/` nem `__pycache__`.
2. **Prepare o ambiente** com os comandos da stack padrão (criar `.venv`, instalar). Rode `PY -m pytest -q`: os testes do modelo precisam passar antes de qualquer mudança. Se falharem, o problema é de ambiente; registre e corrija antes de seguir.
3. **Banco.** Coloque o DDL da SPEC em `banco.ESQUEMA` e implemente `banco.carga_inicial(conn, agora)`: só insere se a tabela estiver vazia, e toda data relativa ("futura", "atrasado") é calculada a partir de `agora`.
4. **Testes primeiro, em lote.** Escreva em `tests/` todos os testes do plano da SPEC, com os nomes do plano (`test_ca_XX_...`, `test_rn_XX_...`). Use as fixtures `cliente` e `relogio` e a função `iso()` do `conftest.py`. Rode a suíte e **registre no log a última linha da saída** (ex.: `41 failed, 12 passed`). Essa é a evidência de que os testes falham antes do código. Testes que já passam sem implementação estão errados: corrija-os.
5. **Implemente**, nesta divisão:
   - `app/dominio/`: regras puras, recebem dados e `agora`, levantam `regra_violada`, `conflito` ou `nao_encontrado` de `app/dominio/erros.py`. Comentário `# RN-xx` em cada regra. Sem import de FastAPI nem `sqlite3`.
   - `app/repositorio/`: SQL parametrizado em constantes de módulo; conversão de datas com `relogio.para_banco` e `relogio.do_banco` (datas sem horário: texto `AAAA-MM-DD`).
   - `app/rotas/`: um `APIRouter` por recurso, modelos Pydantic de entrada e saída com os tipos de `app/tipos.py`, `Depends(obter_conexao)` e `Depends(obter_agora)`. Parâmetros de caminho e consulta sempre como `Annotated[Tipo, Path()]` ou `Annotated[Tipo, Query()]`. Registre o router em `criar_app`.

   Rode a suíte a cada grupo de regras implementado, até tudo passar.
6. **Concorrência.** Toda escrita que depende de uma leitura (conferir conflito e inserir, conferir status e mudar) roda dentro de `with banco.transacao(conn):`.
7. **Tela.** Substitua o conteúdo de `<main>` em `app/estatico/index.html` conforme a seção Tela da SPEC, mantendo o CSS e as funções prontas (`api`, `mostrarMensagem`, `lerFormulario`, `desenharTabela`). Use `<section>` por bloco e `<form>` com `name` nos campos. Mostre dados só por `textContent` ou `desenharTabela`. Mostre sucesso e erro com `mostrarMensagem`. Troque o título "Sistema gerado" pelo nome do sistema.
8. **Verificação via HTTP.** Em `verificacao/verificar_ca.py`, escreva um bloco por `CA-xx`: requisições reais contra `servidor(...)` e `v.registrar(...)` com `resumo(resposta, <campos conferidos>)`, para a evidência mostrar o que prova o critério. Para cenários em que o tempo precisa passar, abra outro `servidor` com `APP_AGORA` posterior e o mesmo banco. Pode rodar o script como ensaio; a etapa de verificação roda de novo e sobrescreve a evidência.
9. **README do sistema.** Escreva `gerado/README.md`: o que faz, comandos de instalar, testar, rodar e verificar em três blocos separados (Windows, Linux e macOS, com `python3` nos dois últimos) e o endereço da tela.
10. **Confira o gate.**

## Quando um teste não passa

- Corrija o código. Altere o teste só se ele contradiz a SPEC, e registre no log o motivo.
- Se a SPEC estiver errada ou incompleta, volte à especificação, corrija a SPEC e registre a volta no log.
- Nunca use `skip`, `xfail` ou asserção enfraquecida para fechar o gate.

## Gate da construção

- [ ] `PY -m pip install -r requirements.txt` funciona num `.venv` novo.
- [ ] O log registra a rodada de testes antes da implementação, com falhas.
- [ ] `PY -m pytest -q` passa sem falhas. Registre no log a última linha da saída.
- [ ] Existe pelo menos um teste `test_ca_XX_...` para cada `CA-xx` do PRD.
- [ ] Existe teste de borda para cada `RN-xx` com limite numérico.
- [ ] Todo endpoint da SPEC está implementado; nenhum endpoint fora da SPEC (`/docs` e `/openapi.json` do FastAPI são permitidos).
- [ ] Nenhum `datetime.now()` em `app/` fora de `app/relogio.py`.
- [ ] `verificacao/verificar_ca.py` tem um bloco por `CA-xx`.
- [ ] `gerado/README.md` existe com os comandos.
