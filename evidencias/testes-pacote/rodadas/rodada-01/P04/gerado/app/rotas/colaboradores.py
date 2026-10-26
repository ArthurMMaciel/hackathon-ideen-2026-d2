"""Rotas de colaboradores (RF-01, RF-02)."""

import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, ConfigDict, Field

from app import banco
from app.banco import obter_conexao
from app.dominio import colaboradores as dominio
from app.erros import nao_encontrado
from app.repositorio import ferias as repo

router = APIRouter(prefix="/api/colaboradores", tags=["colaboradores"])

Equipe = Literal["DADOS", "PRODUTO", "SUPORTE"]

# Ids acima do inteiro do SQLite causariam erro 500; recusamos antes com 422.
ID_MAXIMO = 2_147_483_647


class ColaboradorEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)  # nome só com espaços vira vazio e é recusado

    nome: str = Field(min_length=1, max_length=120)  # RN-12
    email: str = Field(max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")  # RN-12
    equipe: Equipe
    saldo: int = Field(default=30, ge=0, le=365)  # RN-11


class ColaboradorSaida(BaseModel):
    id: int
    nome: str
    email: str
    equipe: Equipe
    saldo: int
    saldo_disponivel: int


def buscar_colaborador(conn: sqlite3.Connection, colaborador_id: int) -> dict:
    c = repo.obter_colaborador(conn, colaborador_id)
    if c is None:
        raise nao_encontrado("COLABORADOR_NAO_ENCONTRADO", f"Colaborador {colaborador_id} não encontrado.")
    return c


@router.get("", response_model=list[ColaboradorSaida])
def listar(conn: sqlite3.Connection = Depends(obter_conexao)):
    return repo.listar_colaboradores(conn)


@router.get("/{colaborador_id}", response_model=ColaboradorSaida)
def consultar(colaborador_id: int = Path(ge=1, le=ID_MAXIMO), conn: sqlite3.Connection = Depends(obter_conexao)):
    return buscar_colaborador(conn, colaborador_id)


@router.post("", response_model=ColaboradorSaida, status_code=201)
def criar(entrada: ColaboradorEntrada, conn: sqlite3.Connection = Depends(obter_conexao)):
    with banco.transacao(conn):
        dominio.validar_email_unico(repo.email_existe(conn, entrada.email))
        novo_id = repo.inserir_colaborador(conn, entrada.nome, entrada.email, entrada.equipe, entrada.saldo)
    return buscar_colaborador(conn, novo_id)
