"""Rotas de empréstimos: emprestar, listar, atrasados e devolver."""

import sqlite3
from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, StrictBool

from app.banco import obter_conexao, transacao
from app.dominio import emprestimos as regras
from app.dominio.erros import nao_encontrado
from app.relogio import obter_agora
from app.repositorio import emprestimos as repo
from app.repositorio import equipamentos as repo_equipamentos
from app.tipos import Data, Email, Id, Texto

router = APIRouter(prefix="/api/emprestimos", tags=["emprestimos"])

Status = Literal["ABERTO", "DEVOLVIDO"]
Conexao = Annotated[sqlite3.Connection, Depends(obter_conexao)]
Agora = Annotated[datetime, Depends(obter_agora)]


class EmprestimoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    equipamento_id: Id
    nome: Texto
    email: Email
    data_prevista: Data


class DevolucaoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    defeito: StrictBool = False


class EmprestimoSaida(BaseModel):
    id: int
    equipamento_id: int
    patrimonio: str
    tipo: str
    nome: str
    email: str
    data_retirada: str
    data_prevista: str
    data_devolucao: str | None
    defeito: bool | None
    status: Status


class AtrasadoSaida(EmprestimoSaida):
    dias_atraso: int


@router.post("", status_code=201, response_model=EmprestimoSaida)
def emprestar(dados: EmprestimoEntrada, conn: Conexao, agora: Agora):
    retirada = regras.data_hoje(agora)  # RN-03
    email = regras.normalizar_email(dados.email)  # PR-04
    with transacao(conn):
        equipamento = repo_equipamentos.obter(conn, dados.equipamento_id)
        if equipamento is None:
            raise nao_encontrado("EQUIPAMENTO_NAO_ENCONTRADO", "Equipamento não encontrado.")
        regras.validar_disponivel(equipamento["situacao"])  # RN-02
        regras.validar_prazo(equipamento["tipo"], retirada, dados.data_prevista)  # RN-04, RN-05
        regras.validar_limite_pessoa(repo.contar_abertos_da_pessoa(conn, email))  # RN-06
        novo_id = repo.inserir(conn, dados.equipamento_id, dados.nome, email, retirada, dados.data_prevista)
        repo_equipamentos.mudar_situacao(conn, dados.equipamento_id, "EMPRESTADO")
    return repo.obter(conn, novo_id)


@router.get("", response_model=list[EmprestimoSaida])
def listar(conn: Conexao, status: Annotated[Status | None, Query()] = None):
    return repo.listar(conn, status)


@router.get("/atrasados", response_model=list[AtrasadoSaida])
def atrasados(conn: Conexao, agora: Agora):
    hoje = regras.data_hoje(agora)
    itens = [
        {**e, "dias_atraso": regras.dias_atraso(date.fromisoformat(e["data_prevista"]), hoje)}  # RN-09
        for e in repo.listar_atrasados(conn, hoje)
    ]
    itens.sort(key=lambda e: (-e["dias_atraso"], e["id"]))  # PR-07
    return itens


@router.post("/{id}/devolver", response_model=EmprestimoSaida)
def devolver(id: Annotated[Id, Path()], conn: Conexao, agora: Agora, dados: DevolucaoEntrada | None = None):
    defeito = dados.defeito if dados else False
    with transacao(conn):
        emprestimo = repo.obter(conn, id)
        if emprestimo is None:
            raise nao_encontrado("EMPRESTIMO_NAO_ENCONTRADO", "Empréstimo não encontrado.")
        regras.validar_devolucao(emprestimo["status"])  # RN-07
        repo.registrar_devolucao(conn, id, regras.data_hoje(agora), defeito)
        nova_situacao = regras.situacao_apos_devolucao(defeito)  # RN-08
        repo_equipamentos.mudar_situacao(conn, emprestimo["equipamento_id"], nova_situacao)
    return repo.obter(conn, id)
