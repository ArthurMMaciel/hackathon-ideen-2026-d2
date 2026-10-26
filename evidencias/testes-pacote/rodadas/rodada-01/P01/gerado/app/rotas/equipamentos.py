"""Rotas de equipamentos: cadastro, listagem (com filtro de disponíveis) e consulta."""

import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, StringConstraints

from app import banco
from app.banco import obter_conexao
from app.dominio import equipamentos as dominio
from app.erros import nao_encontrado
from app.repositorio import equipamentos as repo

router = APIRouter(prefix="/api/equipamentos", tags=["equipamentos"])

Tipo = Literal["NOTEBOOK", "PROJETOR", "HEADSET"]
Situacao = Literal["DISPONIVEL", "EMPRESTADO", "MANUTENCAO"]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
# Maior inteiro que o SQLite guarda; acima disso o driver estoura (erro 500).
IdCaminho = Annotated[int, Path(ge=1, le=2**63 - 1)]


class EquipamentoEntrada(BaseModel):
    patrimonio: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
    tipo: Tipo
    descricao: Texto


class Equipamento(BaseModel):
    id: int
    patrimonio: str
    tipo: Tipo
    descricao: str
    situacao: Situacao


def _obter(conn: sqlite3.Connection, equipamento_id: int) -> dict:
    equipamento = repo.buscar(conn, equipamento_id)
    if equipamento is None:
        raise nao_encontrado("EQUIPAMENTO_NAO_ENCONTRADO", f"Equipamento {equipamento_id} não encontrado.")
    return equipamento


@router.post("", status_code=201, response_model=Equipamento)
def cadastrar(entrada: EquipamentoEntrada, conn: sqlite3.Connection = Depends(obter_conexao)):
    dominio.validar_patrimonio(entrada.patrimonio)
    with banco.transacao(conn):
        dominio.garantir_patrimonio_unico(repo.existe_patrimonio(conn, entrada.patrimonio), entrada.patrimonio)
        novo_id = repo.inserir(conn, entrada.patrimonio, entrada.tipo, entrada.descricao)
    return repo.buscar(conn, novo_id)


@router.get("", response_model=list[Equipamento])
def listar(
    tipo: Tipo | None = Query(default=None),
    situacao: Situacao | None = Query(default=None),
    conn: sqlite3.Connection = Depends(obter_conexao),
):
    return repo.listar(conn, tipo=tipo, situacao=situacao)


@router.get("/{equipamento_id}", response_model=Equipamento)
def consultar(equipamento_id: IdCaminho, conn: sqlite3.Connection = Depends(obter_conexao)):
    return _obter(conn, equipamento_id)
