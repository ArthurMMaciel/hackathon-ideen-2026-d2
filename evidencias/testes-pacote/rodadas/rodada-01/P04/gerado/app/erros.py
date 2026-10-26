"""Erros de negócio no formato {"erro": CODIGO, "mensagem": texto}."""

from fastapi import Request
from fastapi.responses import JSONResponse


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


async def tratar_erro_negocio(request: Request, exc: ErroNegocio) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"erro": exc.codigo, "mensagem": exc.mensagem})
