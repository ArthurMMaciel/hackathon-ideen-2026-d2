# Regras transversais

Valem para todas as etapas e para qualquer pedido.

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

## Erros da API

- Validação de formato (campo faltando, tipo errado): `422`, padrão do framework.
- Regra de negócio violada: `422`, com corpo `{"erro": "<CODIGO>", "mensagem": "<texto em português>"}`.
- Conflito com estado existente (sobreposição, duplicidade): `409`, mesmo formato de corpo.
- Recurso inexistente: `404`, mesmo formato de corpo.
- A mensagem cita a regra violada em linguagem simples. Não exponha stack trace nem SQL.

## Estado e histórico

- Não apague registros de negócio. Cancelamento e inativação mudam o status e mantêm o histórico.
- Status como enum em texto maiúsculo, com os nomes do pedido (`ATIVA`, `CANCELADA`).

## Dados iniciais

- Se o pedido fala em dados que "já começam cadastrados", crie uma carga inicial idempotente que roda ao iniciar a aplicação com banco vazio.
- Dados iniciais são fictícios e plausíveis. Nada de nome, e-mail ou documento de pessoa real.

## Idioma

- Documentos, mensagens de erro e tela em português do Brasil.
- Código (nomes de módulos, funções, variáveis) pode seguir os termos do domínio do pedido em português, sem acento.
