# PRD · Inscrição em treinamentos

## Problema
"Fazemos treinamentos internos e as inscrições são por formulário. Sempre lota, alguém desiste e a vaga fica parada." Falta lista de espera automática e controle de quem compareceu.

## Usuários
- Pessoa colaboradora: vê turmas, se inscreve, cancela a própria inscrição.
- Organização dos treinamentos: cadastra turmas, vê inscritos, marca presença e consulta a taxa de presença.

## Objetivo
Turmas com vagas preenchidas automaticamente pela lista de espera e presença registrada. Sucesso: todos os critérios de aceite verificados.

## Entidades
| Entidade | Atributos | Valores fixos |
|---|---|---|
| Turma | título, data e hora de início, duração em minutos, modalidade, quantidade de vagas | PRESENCIAL, ONLINE |
| Inscrição | turma, nome, e-mail, situação, momento da inscrição | CONFIRMADA, ESPERA, CANCELADA, PRESENTE, AUSENTE |

## Requisitos funcionais
| Código | Requisito |
|---|---|
| RF-01 | Cadastrar turma com título, data e hora de início, duração em minutos, modalidade e quantidade de vagas. |
| RF-02 | Consultar uma turma pelo identificador, com vagas restantes. |
| RF-03 | Iniciar o sistema com 3 turmas futuras já cadastradas (PR-11). |
| RF-04 | Inscrever pessoa (nome e e-mail) numa turma. |
| RF-05 | Listar os inscritos de uma turma, com situação e posição na espera. |
| RF-06 | Cancelar uma inscrição. |
| RF-07 | Marcar presença de uma inscrição como PRESENTE ou AUSENTE. |
| RF-08 | Consultar turmas futuras com a quantidade de vagas restantes. |
| RF-09 | Emitir a taxa de presença de uma turma, em percentual. |
| RF-10 | Oferecer API REST para todas as operações. |
| RF-11 | Oferecer tela web simples para ver as turmas, se inscrever e ver os inscritos de uma turma. |
| RF-12 | Guardar os dados em banco local, sem login. |

## Regras de negócio
| Código | Regra |
|---|---|
| RN-01 | Quantidade de vagas inteira de 1 a 50, inclusive. |
| RN-02 | Duração inteira de 1 a 1440 minutos, inclusive (PR-03). |
| RN-03 | Título e nome com 1 a 200 caracteres; e-mail em formato nome@dominio, até 254 caracteres. |
| RN-04 | Turma só pode ser cadastrada com início posterior ao momento do cadastro. |
| RN-05 | Inscrição nasce CONFIRMADA se ocupadas < vagas; senão nasce ESPERA. Ocupadas = CONFIRMADA + PRESENTE + AUSENTE. |
| RN-06 | A espera segue a ordem de chegada: a mais antiga é a posição 1. |
| RN-07 | O mesmo e-mail não pode ter duas inscrições ativas (CONFIRMADA ou ESPERA) na mesma turma. |
| RN-08 | Inscrição aceita só se o momento for anterior a início − 24 h; a partir de exatamente 24 h antes, recusada. |
| RN-09 | Cancelamento aceito só antes do início (momento < início) e só para CONFIRMADA ou ESPERA. |
| RN-10 | Ao cancelar uma CONFIRMADA, a posição 1 da espera passa a CONFIRMADA. |
| RN-11 | Presença só com momento ≥ início e só para inscrição CONFIRMADA; valor PRESENTE ou AUSENTE. |
| RN-12 | Taxa de presença = presentes ÷ (presentes + ausentes) × 100, com 1 casa decimal. |
| RN-13 | Vagas restantes = vagas − ocupadas, nunca menor que 0. |

## Premissas
| Código | Premissa |
|---|---|
| PR-01 | Fuso America/Sao_Paulo, horários sempre com fuso explícito. |
| PR-02 | Cadastro de turma cobre criar, listar e consultar; sem edição nem exclusão. |
| PR-03 | O pedido não limita a duração; adotado de 1 minuto a 24 horas. |
| PR-04 | E-mail comparado sem diferenciar maiúsculas e guardado em minúsculas. |
| PR-05 | Depois de cancelar, o mesmo e-mail pode se inscrever de novo e entra no fim da fila, se lotada. |
| PR-06 | Cancelar uma ESPERA só a retira da fila; ninguém é promovido. |
| PR-07 | A promoção da espera vale até o início da turma, inclusive dentro das 24 h finais. |
| PR-08 | Presença é marcada uma vez; PRESENTE e AUSENTE não mudam depois. CANCELADA não volta. |
| PR-09 | Turma futura = início posterior ao momento da consulta. Turmas ordenadas por início; inscritos por ordem de chegada. |
| PR-10 | Taxa com arredondamento meio para cima; sem presença marcada, a taxa fica vazia. |
| PR-11 | Carga inicial: 3 turmas fictícias a 7, 14 e 21 dias do primeiro início do sistema, às 09:00. |
| PR-12 | Títulos de turma e nomes de pessoa podem se repetir; a fila de espera não tem limite. |

## Fora de escopo
- Login, perfis de acesso e identificação de quem opera (o pedido dispensa login).
- Notificações por e-mail ou mensagem sobre promoção da espera.
- Edição e exclusão de turmas; exportação de relatórios.
- Deploy, integração com sistemas reais e uso de dados reais.

## Critérios de aceite
| Código | Cenário | Resultado esperado | Verifica |
|---|---|---|---|
| CA-01 | Inscrever em turma com vaga | Inscrição `CONFIRMADA` | RF-04, RN-05 |
| CA-02 | Inscrever em turma lotada | Inscrição `ESPERA`, primeira da fila | RF-04, RN-05, RN-06 |
| CA-03 | Cancelar inscrição confirmada numa turma com fila de espera | A primeira da espera passa a `CONFIRMADA` | RF-06, RN-09, RN-10 |
| CA-04 | Inscrever o mesmo e-mail duas vezes na mesma turma | Segunda recusada | RF-04, RN-07 |
| CA-05 | Inscrever 23 horas antes do início | Recusa | RF-04, RN-08 |
| CA-06 | Cancelar inscrição depois do início da turma | Recusa | RF-06, RN-09 |
| CA-07 | Marcar presença antes do início da turma | Recusa | RF-07, RN-11 |
| CA-08 | Marcar presença de uma inscrição em `ESPERA` | Recusa | RF-07, RN-11 |
| CA-09 | Consultar turmas futuras depois de lotar uma turma | Turma lotada aparece com 0 vagas restantes | RF-08, RN-13 |
| CA-10 | Taxa de presença com 3 presentes e 1 ausente | 75% | RF-09, RN-12 |
