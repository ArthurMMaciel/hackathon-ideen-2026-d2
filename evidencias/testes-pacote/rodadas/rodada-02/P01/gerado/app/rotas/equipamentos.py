"""Rotas de equipamentos: cadastro, listagem, consulta e disponíveis."""

import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, StringConstraints

from app.banco import obter_conexao, transacao
from app.dominio import equipamentos as regras
from app.dominio.erros import nao_encontrado
from app.repositorio import equipamentos as repo
from app.tipos import Id, Texto

router = APIRouter(prefix="/api/equipamentos", tags=["equipamentos"])

Tipo = Literal["NOTEBOOK", "PROJETOR", "HEADSET"]
Situacao = Literal["DISPONIVEL", "EMPRESTADO", "MANUTENCAO"]
# RN-01: formato EQ-0000 (só dígitos ASCII)
Patrimonio = Annotated[str, StringConstraints(pattern=regras.PADRAO_PATRIMONIO, max_length=7)]
Conexao = Annotated[sqlite3.Connection, Depends(obter_conexao)]


class EquipamentoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patrimonio: Patrimonio
    tipo: Tipo
    descricao: Texto


class EquipamentoSaida(BaseModel):
    id: int
    patrimonio: str
    tipo: Tipo
    descricao: str
    situacao: Situacao


@router.post("", status_code=201, response_model=EquipamentoSaida)
def cadastrar(dados: EquipamentoEntrada, conn: Conexao):
    with transacao(conn):
        regras.validar_patrimonio_unico(dados.patrimonio, repo.existe_patrimonio(conn, dados.patrimonio))  # RN-01
        novo_id = repo.inserir(conn, dados.patrimonio, dados.tipo, dados.descricao)
    return repo.obter(conn, novo_id)


@router.get("", response_model=list[EquipamentoSaida])
def listar(conn: Conexao):
    return repo.listar(conn)


@router.get("/disponiveis", response_model=list[EquipamentoSaida])
def disponiveis(conn: Conexao, tipo: Annotated[Tipo | None, Query()] = None):
    return repo.listar_disponiveis(conn, tipo)


@router.get("/{id}", response_model=EquipamentoSaida)
def consultar(id: Annotated[Id, Path()], conn: Conexao):
    equipamento = repo.obter(conn, id)
    if equipamento is None:
        raise nao_encontrado("EQUIPAMENTO_NAO_ENCONTRADO", "Equipamento não encontrado.")
    return equipamento
