"""Rotas de chamados, fila e relatório de prazo."""

import sqlite3
from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app import banco
from app.banco import obter_conexao
from app.dominio import chamados as dominio
from app.dominio import relatorio as dom_relatorio
from app.erros import nao_encontrado
from app.relogio import obter_agora
from app.repositorio import chamados as repo

router = APIRouter(prefix="/api")

Categoria = Literal["ACESSO", "HARDWARE", "SOFTWARE"]
Prioridade = Literal["BAIXA", "MEDIA", "ALTA", "CRITICA"]
Situacao = Literal["ABERTO", "EM_ATENDIMENTO", "RESOLVIDO", "FECHADO"]

EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Faixa do INTEGER do SQLite: fora dela o driver levantaria OverflowError (500).
IdChamado = Annotated[int, Path(ge=1, le=2**63 - 1)]


class NovoChamado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(min_length=1, max_length=200)
    descricao: str = Field(min_length=1, max_length=2000)
    solicitante_nome: str = Field(min_length=1, max_length=100)
    solicitante_email: str = Field(min_length=3, max_length=200, pattern=EMAIL)
    categoria: Categoria
    prioridade: Prioridade

    @field_validator("titulo", "descricao", "solicitante_nome")
    @classmethod
    def nao_vazio(cls, valor: str) -> str:
        # RN-09: texto obrigatório não pode ser só espaços.
        valor = valor.strip()
        if not valor:
            raise ValueError("não pode ser vazio")
        return valor


class Assumir(BaseModel):
    responsavel: str | None = Field(default=None, max_length=100)


class Resolver(BaseModel):
    solucao: str | None = Field(default=None, max_length=2000)


class ChamadoSaida(BaseModel):
    id: int
    titulo: str
    descricao: str
    solicitante_nome: str
    solicitante_email: str
    categoria: Categoria
    prioridade: Prioridade
    situacao: Situacao
    aberto_em: datetime
    prazo: datetime
    responsavel: str | None
    solucao: str | None
    resolvido_em: datetime | None
    dentro_do_prazo: bool | None


class ItemFila(ChamadoSaida):
    indicacao: Literal["ATRASADO"] | None


class LinhaRelatorio(BaseModel):
    prioridade: Prioridade
    resolvidos: int
    dentro_do_prazo: int
    percentual_dentro_do_prazo: float | None


class Relatorio(BaseModel):
    data_inicial: date
    data_final: date
    prioridades: list[LinhaRelatorio]


def _saida(chamado: dict) -> dict:
    return {**chamado, "dentro_do_prazo": dominio.dentro_do_prazo(chamado["resolvido_em"], chamado["prazo"])}


def _carregar(conn: sqlite3.Connection, chamado_id: int) -> dict:
    chamado = repo.obter(conn, chamado_id)
    if chamado is None:
        raise nao_encontrado("CHAMADO_NAO_ENCONTRADO", f"Chamado {chamado_id} não encontrado.")
    return chamado


@router.post("/chamados", status_code=201, response_model=ChamadoSaida)
def abrir(dados: NovoChamado, conn=Depends(obter_conexao), agora: datetime = Depends(obter_agora)):
    with banco.transacao(conn):
        novo_id = repo.inserir(conn, {
            **dados.model_dump(),
            "situacao": "ABERTO",
            "aberto_em": agora,
            "prazo": dominio.calcular_prazo(dados.prioridade, agora),  # RN-01 / RN-02
        })
    return _saida(repo.obter(conn, novo_id))


@router.get("/chamados", response_model=list[ChamadoSaida])
def listar(conn=Depends(obter_conexao)):
    return [_saida(c) for c in repo.listar(conn)]


@router.get("/chamados/fila", response_model=list[ItemFila])
def fila(conn=Depends(obter_conexao), agora: datetime = Depends(obter_agora)):
    return [
        {**_saida(c), "indicacao": dominio.indicacao_fila(c["prazo"], agora)}  # RN-08
        for c in repo.listar_fila(conn)
    ]


@router.get("/chamados/{chamado_id}", response_model=ChamadoSaida)
def consultar(chamado_id: IdChamado, conn=Depends(obter_conexao)):
    return _saida(_carregar(conn, chamado_id))


@router.post("/chamados/{chamado_id}/assumir", response_model=ChamadoSaida)
def assumir(chamado_id: IdChamado, dados: Assumir | None = None, conn=Depends(obter_conexao)):
    with banco.transacao(conn):
        chamado = _carregar(conn, chamado_id)
        dominio.validar_transicao(chamado["situacao"], "assumir")  # RN-07
        responsavel = dominio.exigir_responsavel(dados.responsavel if dados else None)  # RN-04
        repo.atualizar_situacao(conn, chamado_id, "EM_ATENDIMENTO", responsavel, None, None)
    return _saida(repo.obter(conn, chamado_id))


@router.post("/chamados/{chamado_id}/resolver", response_model=ChamadoSaida)
def resolver(
    chamado_id: IdChamado,
    dados: Resolver | None = None,
    conn=Depends(obter_conexao),
    agora: datetime = Depends(obter_agora),
):
    with banco.transacao(conn):
        chamado = _carregar(conn, chamado_id)
        dominio.validar_transicao(chamado["situacao"], "resolver")  # RN-07
        solucao = dominio.exigir_solucao(dados.solucao if dados else None)  # RN-05
        repo.atualizar_situacao(conn, chamado_id, "RESOLVIDO", chamado["responsavel"], solucao, agora)
    return _saida(repo.obter(conn, chamado_id))


@router.post("/chamados/{chamado_id}/fechar", response_model=ChamadoSaida)
def fechar(chamado_id: IdChamado, conn=Depends(obter_conexao)):
    with banco.transacao(conn):
        chamado = _carregar(conn, chamado_id)
        dominio.validar_transicao(chamado["situacao"], "fechar")  # RN-07
        repo.atualizar_situacao(
            conn, chamado_id, "FECHADO", chamado["responsavel"], chamado["solucao"], chamado["resolvido_em"]
        )
    return _saida(repo.obter(conn, chamado_id))


@router.post("/chamados/{chamado_id}/reabrir", response_model=ChamadoSaida)
def reabrir(chamado_id: IdChamado, conn=Depends(obter_conexao), agora: datetime = Depends(obter_agora)):
    with banco.transacao(conn):
        chamado = _carregar(conn, chamado_id)
        dominio.validar_transicao(chamado["situacao"], "reabrir")  # RN-07
        dominio.verificar_reabertura(chamado["resolvido_em"], agora)  # RN-06
        # PR-06: limpa solução e resolução, mantém responsável; RN-02: prazo não é tocado.
        repo.atualizar_situacao(conn, chamado_id, "EM_ATENDIMENTO", chamado["responsavel"], None, None)
    return _saida(repo.obter(conn, chamado_id))


@router.get("/relatorios/prazo", response_model=Relatorio)
def relatorio_prazo(
    data_inicial: date = Query(...),
    data_final: date = Query(...),
    conn=Depends(obter_conexao),
):
    inicio, fim = dom_relatorio.periodo(data_inicial, data_final)  # RN-10
    resolvidos = [
        (prioridade, dominio.dentro_do_prazo(resolvido_em, prazo))  # RN-03
        for prioridade, resolvido_em, prazo in repo.resolvidos_no_periodo(conn, inicio, fim)
    ]
    return {"data_inicial": data_inicial, "data_final": data_final, "prioridades": dom_relatorio.montar(resolvidos)}
