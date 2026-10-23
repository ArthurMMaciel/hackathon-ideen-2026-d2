# Kit do Desafio 2 · Desenvolvimento agêntico

Sua entrega é a fábrica: um pacote de skills que leva qualquer agente de um pedido em linguagem natural até um sistema funcionando.

## Estrutura do repositório (`ideen-tech/hackathon-2026-d2-[seu-usuário]`)

| Caminho | O que vai ali |
|---|---|
| `skills/` | o pacote, em arquivos `SKILL.md`, cobrindo concepção, especificação, construção e revisão |
| `gerado/` | o sistema que o pacote produziu a partir do `PEDIDO-TREINO.md` |
| `evidencias/` | agente e modelo usados, o prompt de entrada, log resumido da execução, prints e o resultado dos critérios de aceite |
| `README.md` | o problema, o que você fez, como reproduzir, evidências e onde a IA errou |

## Como a banca vai rodar o seu pacote (finalistas)

O mesmo agente e o mesmo modelo para todos, com as suas skills instaladas, um pedido que você não conhece e este prompt, sem intervenção humana:

> Usando as skills disponíveis, construa o sistema descrito em PEDIDO.md dentro da pasta gerado/. Siga todas as etapas das skills até o sistema rodar e os critérios de aceite serem verificados.

Treine o seu pacote para funcionar com esse prompt.

## Dicas

- Ajuste manual no código gerado é permitido, mas precisa estar registrado em `evidencias/`. Quanto menos ajuste, melhor.
- Teste o pacote do zero, num diretório limpo, antes de entregar.
- Prazo: **segunda, 26/10, às 9h**. Fim de semana é opcional e sem lançamento de horas.
