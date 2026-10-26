"""Rotas de empréstimos: registrar, listar, atrasados e devolver."""

import re
import sqlite3
from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic import BaseModel, BeforeValidator, Field, StringConstraints

from app import banco
from app.banco import obter_conexao
from app.dominio import emprestimos as dominio
from app.erros import nao_encontrado
from app.relogio import obter_agora
from app.repositorio import emprestimos as repo
from app.repositorio import equipamentos as repo_equipamentos

router = APIRouter(prefix="/api/emprestimos", tags=["emprestimos"])

Status = Literal["ABERTO", "DEVOLVIDO"]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
# PR-04: formato simples texto@texto.texto, sem espaços
Email = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
]

# Maior inteiro que o SQLite guarda; acima disso o driver estoura (erro 500).
ID_MAXIMO = 2**63 - 1


def _exigir_data_iso(valor):
    """Aceita só texto AAAA-MM-DD; recusa número (timestamp) e data com hora."""
    if not isinstance(valor, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", valor):
        raise ValueError("data deve estar no formato AAAA-MM-DD")
    return valor


DataISO = Annotated[date, BeforeValidator(_exigir_data_iso)]
IdCaminho = Annotated[int, Path(ge=1, le=ID_MAXIMO)]


class EmprestimoEntrada(BaseModel):
    equipamento_id: int = Field(ge=1, le=ID_MAXIMO)
    nome: Texto
    email: Email
    data_prevista: DataISO


class DevolucaoEntrada(BaseModel):
    defeito: bool = False


class Emprestimo(BaseModel):
    id: int
    equipamento_id: int
    patrimonio: str
    tipo: str
    nome: str
    email: str
    data_retirada: date
    data_prevista: date
    data_devolucao: date | None
    defeito: bool | None
    status: Status
    situacao_equipamento: str


class EmprestimoAtrasado(Emprestimo):
    dias_atraso: int


def _obter(conn: sqlite3.Connection, emprestimo_id: int) -> dict:
    emprestimo = repo.buscar(conn, emprestimo_id)
    if emprestimo is None:
        raise nao_encontrado("EMPRESTIMO_NAO_ENCONTRADO", f"Empréstimo {emprestimo_id} não encontrado.")
    return emprestimo


@router.post("", status_code=201, response_model=Emprestimo)
def registrar(
    entrada: EmprestimoEntrada,
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    retirada = dominio.hoje(agora)  # RN-03
    email = dominio.normalizar_email(entrada.email)
    with banco.transacao(conn):
        equipamento = repo_equipamentos.buscar(conn, entrada.equipamento_id)
        if equipamento is None:
            raise nao_encontrado(
                "EQUIPAMENTO_NAO_ENCONTRADO", f"Equipamento {entrada.equipamento_id} não encontrado."
            )
        dominio.validar_disponivel(equipamento["situacao"])
        dominio.validar_prazo(equipamento["tipo"], retirada, entrada.data_prevista)
        dominio.validar_limite_pessoa(repo.contar_abertos_por_email(conn, email))
        novo_id = repo.inserir(conn, equipamento["id"], entrada.nome, email, retirada, entrada.data_prevista, agora)
        repo_equipamentos.atualizar_situacao(conn, equipamento["id"], dominio.situacao_ao_emprestar())
    return repo.buscar(conn, novo_id)


@router.get("", response_model=list[Emprestimo])
def listar(status: Status | None = Query(default=None), conn: sqlite3.Connection = Depends(obter_conexao)):
    return repo.listar(conn, status=status)


@router.get("/atrasados", response_model=list[EmprestimoAtrasado])
def atrasados(conn: sqlite3.Connection = Depends(obter_conexao), agora: datetime = Depends(obter_agora)):
    dia = dominio.hoje(agora)
    resultado = []
    for emprestimo in repo.listar_abertos_vencidos(conn, dia):
        prevista = date.fromisoformat(emprestimo["data_prevista"])
        resultado.append({**emprestimo, "dias_atraso": dominio.dias_atraso(prevista, dia)})  # RN-11
    return resultado


@router.post("/{emprestimo_id}/devolver", response_model=Emprestimo)
def devolver(
    emprestimo_id: IdCaminho,
    entrada: DevolucaoEntrada | None = Body(default=None),
    conn: sqlite3.Connection = Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    defeito = entrada.defeito if entrada else False
    with banco.transacao(conn):
        emprestimo = _obter(conn, emprestimo_id)
        dominio.validar_devolucao(emprestimo["status"])  # RN-10
        repo.registrar_devolucao(conn, emprestimo_id, dominio.hoje(agora), defeito)  # RN-08
        repo_equipamentos.atualizar_situacao(
            conn, emprestimo["equipamento_id"], dominio.situacao_apos_devolucao(defeito)  # RN-09
        )
    return repo.buscar(conn, emprestimo_id)
