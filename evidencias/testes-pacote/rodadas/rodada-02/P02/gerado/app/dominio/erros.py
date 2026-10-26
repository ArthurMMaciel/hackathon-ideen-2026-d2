"""Erros de negócio. Módulo puro: o domínio levanta daqui sem depender de FastAPI.

Escolha do status (regras transversais):
- 409: a mesma requisição seria aceita se o estado guardado fosse outro (já emprestado, já cancelado,
  transição inválida, duplicidade, sobreposição, limite de itens em aberto).
- 422: a requisição é inválida em qualquer estado (prazo, valor, duração, campo obrigatório de negócio).
- 404: o recurso não existe.
"""


class ErroNegocio(Exception):
    def __init__(self, status: int, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.status = status
        self.codigo = codigo
        self.mensagem = mensagem


def regra_violada(codigo: str, mensagem: str) -> ErroNegocio:
    return ErroNegocio(422, codigo, mensagem)


def conflito(codigo: str, mensagem: str) -> ErroNegocio:
    return ErroNegocio(409, codigo, mensagem)


def nao_encontrado(codigo: str, mensagem: str) -> ErroNegocio:
    return ErroNegocio(404, codigo, mensagem)
