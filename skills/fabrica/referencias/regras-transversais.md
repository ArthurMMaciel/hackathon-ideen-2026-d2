# Regras transversais

Valem para todas as etapas e para qualquer pedido.

## Precedência

**O pedido prevalece sobre estas regras.** Se o pedido manda algo diferente (ex.: "só despesa pendente pode ser excluída" contra "não apague registros"), siga o pedido e registre a escolha como premissa `PR-xx`.

## Faixas de valores

Use os tipos de `app/tipos.py`. Eles já aplicam estas faixas e evitam HTTP 500:

- ids entre 1 e 2.147.483.647;
- anos entre 2000 e 2100 em datas e datas com hora;
- textos sem espaços nas pontas, não vazios, até 200 caracteres (`TextoLongo`: 2000);
- dinheiro em centavos, inteiro.

## Rastreabilidade

| Prefixo | O que é | Onde nasce |
|---|---|---|
| `RF-xx` | requisito funcional | PRD |
| `RN-xx` | regra de negócio (validação, restrição, cálculo) | PRD |
| `PR-xx` | premissa assumida por falta de informação | PRD |
| `CA-xx` | critério de aceite | pedido; se o pedido não trouxer, a especificação cria |

- Use os códigos `CA-xx` do pedido exatamente como vieram. Não renumere.
- Todo teste de critério de aceite leva o código no nome: `test_ca_02_recusa_conflito`.
- Toda regra de negócio no código tem comentário curto com o código da regra: `# RN-03`.

## Tempo e datas

- Fuso padrão `America/Sao_Paulo`, salvo se o pedido disser outro. No PRD, registre como premissa só "fuso America/Sao_Paulo, horários sempre com fuso explícito".
- Na especificação e no código: datas e horas na API em ISO 8601 com offset (`2026-10-26T10:00:00-03:00`). Rejeite horário sem fuso com erro de validação. No banco, grave em UTC.
- Intervalos são semiabertos `[início, fim)`. Dois intervalos se sobrepõem quando `a.inicio < b.fim e b.inicio < a.fim`. Encostar não é sobrepor.
- **Nunca leia o relógio do sistema direto nas regras.** Use o relógio injetável do modelo de projeto (`obter_agora`), que os testes substituem e que a variável `APP_AGORA` fixa no servidor real. Toda regra com "passado", "futuro" ou "hoje" depende disso.
- Durações e limites com borda explícita nos testes: o valor mínimo, o máximo, um abaixo e um acima.

## Datas sem horário

Quando o pedido fala em dias de calendário (data de despesa, período de férias, prazo em dias):

- Use o tipo `Data` (`AAAA-MM-DD`, sem horário e sem fuso). Grave como texto `AAAA-MM-DD`, sem converter para UTC.
- "Hoje" é `agora.date()` no fuso padrão, com `agora` vindo do relógio injetável.
- Períodos de dias são fechados `[início, fim]` quando o pedido conta o primeiro e o último dia. Sobreposição: `a.inicio <= b.fim e b.inicio <= a.fim`. Dias seguidos (`fim + 1 dia == início`) não se sobrepõem.
- Quantidade de dias de um período fechado: `(fim - inicio).days + 1`.

## Erros da API

- Validação de formato (campo faltando, tipo errado, fora da faixa): `422`, padrão do framework.
- Para decidir entre `409` e `422` numa regra de negócio, pergunte: **a mesma requisição seria aceita se o estado guardado fosse outro?**
  - Sim → `409` (`conflito`): já emprestado, já cancelado, transição de situação inválida, duplicidade, sobreposição, limite de itens em aberto, fila cheia.
  - Não → `422` (`regra_violada`): duração, prazo, valor acima do limite, data no passado, campo obrigatório de negócio vazio.
- Corpo de erro de negócio: `{"erro": "<CODIGO>", "mensagem": "<texto em português>"}`.
- Recurso inexistente: `404`, mesmo formato de corpo.
- Campo que o pedido diz ser exigido só em uma ação (ex.: motivo da recusa) é opcional no modelo Pydantic e validado no domínio, para a recusa sair com código de negócio.
- A mensagem cita a regra violada em linguagem simples. Não exponha stack trace nem SQL.

## Estado e histórico

- Não apague registros de negócio, salvo se o pedido mandar excluir. Cancelamento e inativação mudam o status e mantêm o histórico.
- Status como enum em texto maiúsculo, com os nomes do pedido (`ATIVA`, `CANCELADA`).

## Dados iniciais

- Se o pedido fala em dados que "já começam cadastrados", crie uma carga inicial idempotente que roda ao iniciar a aplicação com banco vazio.
- Datas dos dados iniciais são relativas ao `agora` que `carga_inicial(conn, agora)` recebe. Nunca fixe datas absolutas nem leia o relógio do sistema ali.
- Testes não dependem dos dados iniciais além do que o pedido garante (quantidade e distribuição). Cada teste cria os registros que confere.
- Dados iniciais são fictícios e plausíveis. Nada de nome, e-mail ou documento de pessoa real.

## Idioma

- Documentos, mensagens de erro e tela em português do Brasil.
- Código (nomes de módulos, funções, variáveis) pode seguir os termos do domínio do pedido em português, sem acento.
