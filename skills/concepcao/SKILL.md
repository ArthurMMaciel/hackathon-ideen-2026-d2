---
name: concepcao
description: Etapa 1 da fábrica. Transforma um pedido em linguagem natural num PRD de uma página (gerado/docs/PRD.md) com requisitos funcionais (RF-xx), regras de negócio (RN-xx), premissas (PR-xx), fora de escopo e critérios de aceite rastreáveis. Use depois da preparação da skill fabrica e antes de qualquer especificação ou código.
---

# Concepção · PRD de uma página

Objetivo: entender o pedido por completo e registrar o que será construído, sem decidir ainda como. O PRD é o contrato com o cliente. Tudo que vier depois aponta para os códigos dele.

Leia antes, se ainda não leu: `../fabrica/referencias/regras-transversais.md`.

## Entrada e saída

- **Entrada:** o arquivo do pedido localizado na etapa 0.
- **Saída:** `gerado/docs/PRD.md`, no formato de [modelo-prd.md](modelo-prd.md).
- **Evidência:** a tabela de cobertura do pedido, no log de execução.

## Passo a passo

1. **Leia o pedido inteiro duas vezes.** Na segunda leitura, separe três coisas: a fala do cliente (o problema), a lista do que o sistema precisa fazer e os critérios de aceite.
2. **Escreva o problema em uma ou duas frases**, com as palavras do cliente. Inclua a dor atual (por exemplo, "conflitos porque tudo está numa planilha").
3. **Quebre o pedido em itens atômicos.** Percorra frase por frase. Cada comportamento vira um `RF-xx`. Cada restrição, validação, limite ou cálculo vira um `RN-xx`. Uma frase pode gerar vários itens.
   - `RF` começa com verbo e descreve uma capacidade: "Cadastrar sala com nome, local, capacidade e recursos."
   - `RN` traz o número e a borda explícitos: "Duração mínima de 15 minutos e máxima de 4 horas, inclusive."
   - Interfaces pedidas (API, tela, relatório, exportação) também viram `RF`, com as palavras do próprio pedido ("API REST", "tela web", "banco local").
   - Dados que "já começam cadastrados" viram `RF` de carga inicial, com quantidade e distribuição.
4. **Liste as entidades** com seus atributos e valores fixos (enums) exatamente como o pedido escreve, incluindo maiúsculas e sem acento.
5. **Preencha as lacunas com premissas `PR-xx`.** Ninguém vai responder perguntas. Para cada lacuna, escolha a interpretação mais simples que atende ao pedido e aos critérios de aceite e escreva a premissa numa frase. Confira obrigatoriamente cada item da lista abaixo e registre no log uma linha por item, com a `PR-xx` ou `RN-xx` que o resolve, ou "não se aplica" com o motivo:
   - fuso horário e formato de data
   - bordas de limites (inclusivo ou exclusivo)
   - o que "cadastro" cobre (criar, listar, consultar, editar, excluir)
   - unicidade de nomes ou identificadores
   - formato e validação de campos (e-mail, texto vazio, números negativos)
   - o que acontece com registros relacionados quando um muda de status
   - definição de período em consultas e relatórios ("dia", "mês", horário de funcionamento)
   - arredondamento e unidade de resultados calculados
   - ordenação de listagens
6. **Escreva o fora de escopo.** Inclua o que o pedido exclui ("não precisa de login") e o que o próprio desafio exclui: deploy, integração com sistema real e dados reais.
7. **Mapeie os critérios de aceite.** Copie cada `CA-xx` do pedido, com o mesmo código, o cenário e o resultado esperado em colunas separadas, e indique os `RF`/`RN` que ele verifica. Se o pedido não trouxer critérios, crie `CA-01` em diante: um caminho feliz por `RF` e uma recusa por `RN`.
8. **Monte a tabela de cobertura do pedido** no log de execução: cada trecho do pedido e os códigos que o cobrem. Trecho sem código é lacuna. Volte ao passo 3 ou 5.
9. **Confira o gate** abaixo.

## O que não fazer

- Não invente funcionalidade que o pedido não citou (notificação, login, exportação, perfis de acesso). Se parecer útil, ela vai para o fora de escopo.
- Não escolha tecnologia no PRD (linguagem, framework, produto de banco, formato de dado). Stack, formatos e endpoints são da especificação. Termos que o próprio pedido usa podem aparecer.
- Não pergunte ao usuário. Lacuna vira premissa.
- Não reescreva nem renumere os critérios de aceite do pedido.

## Gate da concepção

- [ ] `gerado/docs/PRD.md` existe com até 60 linhas de itens (linhas de tabela e de lista; títulos, cabeçalhos e separadores de tabela não contam).
- [ ] Todo trecho do pedido aparece na tabela de cobertura do log com pelo menos um código.
- [ ] Cada item da lista de lacunas comuns tem uma linha no log, com código ou "não se aplica" e motivo.
- [ ] Toda `RN` tem número e borda explícitos quando envolve limite.
- [ ] Todo `CA-xx` do pedido está no PRD, com o código original, cenário, resultado esperado e os `RF`/`RN` que verifica.
- [ ] A seção "Fora de escopo" existe.
- [ ] Nenhuma linguagem, framework, produto de banco, formato de dado, endpoint ou tabela no PRD.
