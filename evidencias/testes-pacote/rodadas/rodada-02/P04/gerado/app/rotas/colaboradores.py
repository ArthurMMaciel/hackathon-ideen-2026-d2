"""RF-01, RF-02: cadastro e consulta de colaboradores com saldo."""

import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field

from app import banco
from app.banco import obter_conexao
from app.dominio import colaboradores as regras
from app.dominio.erros import nao_encontrado
from app.repositorio import ferias as repo
from app.tipos import Email, Id, Texto

router = APIRouter(prefix="/api/colaboradores", tags=["colaboradores"])

Equipe = Literal["DADOS", "PRODUTO", "SUPORTE"]


class ColaboradorEntrada(BaseModel):
    nome: Texto
    email: Email
    equipe: Equipe
    saldo: Annotated[int, Field(ge=0, le=365)] = 30  # RN-11


class ColaboradorSaida(BaseModel):
    id: int
    nome: str
    email: str
    equipe: str
    saldo: int
    saldo_disponivel: int


def buscar_colaborador(conn: sqlite3.Connection, colaborador_id: int) -> dict:
    colaborador = repo.obter_colaborador(conn, colaborador_id)
    if colaborador is None:
        raise nao_encontrado("COLABORADOR_NAO_ENCONTRADO", "Colaborador não encontrado.")
    return colaborador


@router.post("", status_code=201, response_model=ColaboradorSaida)
def cadastrar(dados: ColaboradorEntrada, conn: sqlite3.Connection = Depends(obter_conexao)):
    with banco.transacao(conn):
        regras.validar_email_livre(repo.email_existe(conn, dados.email))
        novo_id = repo.inserir_colaborador(conn, dados.nome, dados.email, dados.equipe, dados.saldo)
    return repo.obter_colaborador(conn, novo_id)


@router.get("", response_model=list[ColaboradorSaida])
def listar(conn: sqlite3.Connection = Depends(obter_conexao)):
    return repo.listar_colaboradores(conn)


@router.get("/{id}", response_model=ColaboradorSaida)
def consultar(id: Annotated[Id, Path()], conn: sqlite3.Connection = Depends(obter_conexao)):
    return buscar_colaborador(conn, id)
