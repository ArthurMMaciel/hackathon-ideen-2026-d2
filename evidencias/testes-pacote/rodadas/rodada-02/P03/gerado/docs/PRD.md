# PRD · Inscrição em treinamentos

## Problema
"Fazemos treinamentos internos e as inscrições são por formulário. Sempre lota, alguém desiste e a vaga fica parada." Falta cadastro de turmas, lista de espera automática e registro de quem compareceu.

## Usuários
- Pessoas da empresa: veem turmas, se inscrevem e cancelam a própria inscrição.
- Organização dos treinamentos: cadastra turmas, acompanha inscritos, marca presença e consulta a taxa de presença.

## Objetivo
Turmas cadastradas com inscrição, lista de espera que libera a vaga sozinha e registro de presença. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Turma | título, data e hora de início, duração em minutos, modalidade, quantidade de vagas | PRESENCIAL, ONLINE |
| Inscrição | turma, nome da pessoa, e-mail da pessoa, situação, momento da inscrição | CONFIRMADA, ESPERA, CANCELADA, PRESENTE, AUSENTE |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar turma com título, data e hora de início, duração em minutos, modalidade e quantidade de vagas. |
| RF-02 | Consultar uma turma pelo identificador, com as vagas restantes. |
| RF-03 | Iniciar o sistema com 3 turmas futuras já cadastradas. |
| RF-04 | Inscrever uma pessoa (nome e e-mail) numa turma, com situação definida automaticamente. |
| RF-05 | Listar os inscritos de uma turma, com situação e posição na espera ("ver os inscritos de uma turma"). |
| RF-06 | Cancelar uma inscrição. |
| RF-07 | Promover automaticamente a primeira inscrição da espera quando uma confirmada é cancelada. |
| RF-08 | Marcar presença de uma inscrição como PRESENTE ou AUSENTE. |
| RF-09 | Consultar turmas futuras com a quantidade de vagas restantes. |
| RF-10 | Emitir relatório de taxa de presença de uma turma, em percentual. |
| RF-11 | Oferecer API REST para todas as operações. |
| RF-12 | Oferecer tela web simples para ver as turmas, se inscrever e ver os inscritos de uma turma. |
| RF-13 | Guardar os dados em banco local, sem login. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Quantidade de vagas de 1 a 50, inclusive. |
| RN-02 | Duração de 1 a 1440 minutos, inclusive (PR-03). |
| RN-03 | Inscrição nasce CONFIRMADA se as vagas ocupadas (CONFIRMADA, PRESENTE, AUSENTE) são menores que as vagas da turma; senão nasce ESPERA. |
| RN-04 | A espera segue a ordem de chegada: a mais antiga é a primeira da fila. |
| RN-05 | O mesmo e-mail não pode ter duas inscrições ativas (CONFIRMADA ou ESPERA) na mesma turma. |
| RN-06 | Inscrições aceitas só até 24 horas antes do início, inclusive: aceita se agora ≤ início − 24h. |
| RN-07 | Cancelamento aceito só antes do início: agora < início. No início em diante, recusa. |
| RN-08 | Só inscrição CONFIRMADA ou ESPERA pode ser cancelada. |
| RN-09 | Ao cancelar uma CONFIRMADA, a primeira da ESPERA passa a CONFIRMADA no mesmo ato. |
| RN-10 | Presença só a partir do início da turma: agora ≥ início. |
| RN-11 | Presença só para inscrição CONFIRMADA; o valor marcado é PRESENTE ou AUSENTE. |
| RN-12 | Taxa de presença = presentes ÷ (presentes + ausentes) × 100, arredondada a 2 casas (PR-08). |
| RN-13 | Vagas restantes = vagas − (CONFIRMADA + PRESENTE + AUSENTE), nunca menor que 0. |
| RN-14 | Turma futura é a que tem início depois de agora. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito. |
| PR-02 | "Cadastro" de turma cobre criar, consultar e listar; editar e excluir ficam fora (não pedidos). |
| PR-03 | O pedido não limita a duração; adotado 1 a 1440 minutos (até um dia). |
| PR-04 | Turma nova precisa ter início depois de agora; títulos repetidos são permitidos. |
| PR-05 | E-mail é validado no formato e comparado sem diferenciar maiúsculas; guardado em minúsculas. Nome e título não podem ser vazios, até 200 caracteres. |
| PR-06 | Inscrição cancelada não conta como ativa: o mesmo e-mail pode se inscrever de novo e entra no fim da fila. |
| PR-07 | A promoção da espera vale até o início da turma, mesmo dentro das 24 horas finais em que novas inscrições estão fechadas. |
| PR-08 | Sem presentes nem ausentes, a taxa fica vazia (sem valor), não 0%. |
| PR-09 | Presença marcada é definitiva: PRESENTE ou AUSENTE não volta nem troca, pois a regra exige CONFIRMADA. |
| PR-10 | Turmas futuras listadas por início crescente; inscritos por ordem de chegada. |
| PR-11 | Pessoa é identificada só por nome e e-mail dentro da inscrição; não há cadastro separado de pessoas. |
| PR-12 | Cancelar e marcar presença são feitos pela API; a tela cobre só o que o pedido lista para ela. |

## Fora de escopo
- Login, perfis e controle de acesso ("Não precisa de login").
- Edição e exclusão de turmas; notificações por e-mail; exportação de relatórios.
- Deploy, integração com sistema real e dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Inscrever em turma com vaga | Inscrição `CONFIRMADA` | RF-04, RN-03 |
| CA-02 | Inscrever em turma lotada | Inscrição `ESPERA`, primeira da fila | RF-04, RN-03, RN-04 |
| CA-03 | Cancelar inscrição confirmada numa turma com fila de espera | A primeira da espera passa a `CONFIRMADA` | RF-06, RF-07, RN-09 |
| CA-04 | Inscrever o mesmo e-mail duas vezes na mesma turma | Segunda recusada | RN-05 |
| CA-05 | Inscrever 23 horas antes do início | Recusa | RN-06 |
| CA-06 | Cancelar inscrição depois do início da turma | Recusa | RN-07 |
| CA-07 | Marcar presença antes do início da turma | Recusa | RF-08, RN-10 |
| CA-08 | Marcar presença de uma inscrição em `ESPERA` | Recusa | RN-11 |
| CA-09 | Consultar turmas futuras depois de lotar uma turma | Turma lotada aparece com 0 vagas restantes | RF-09, RN-13, RN-14 |
| CA-10 | Taxa de presença com 3 presentes e 1 ausente | 75% | RF-10, RN-12 |
