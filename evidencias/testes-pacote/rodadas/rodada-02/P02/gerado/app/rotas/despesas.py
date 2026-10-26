"""Rotas de despesas e do resumo mensal."""

import sqlite3
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Response
from pydantic import BaseModel, Field

from app import banco
from app.banco import obter_conexao
from app.dominio import despesas as dominio
from app.relogio import obter_agora
from app.repositorio import despesas as repo
from app.tipos import Centavos, Data, Email, Id, Mes, Texto

router = APIRouter(prefix="/api")

Categoria = Literal["TRANSPORTE", "HOSPEDAGEM", "ALIMENTACAO", "OUTROS"]
Situacao = Literal["PENDENTE", "APROVADA", "RECUSADA", "PAGA"]
Conexao = Annotated[sqlite3.Connection, Depends(obter_conexao)]
Agora = Annotated[datetime, Depends(obter_agora)]
IdDespesa = Annotated[Id, Path()]


class NovaDespesa(BaseModel):
    colaborador_nome: Texto
    colaborador_email: Email
    data: Data
    categoria: Categoria
    valor_centavos: Centavos
    descricao: Texto
    comprovante: Texto


class Recusa(BaseModel):
    # Opcional no modelo; RN-08 exige no domínio, para a recusa sair com código de negócio.
    motivo: str | None = Field(default=None, max_length=200)


class DespesaSaida(BaseModel):
    id: int
    colaborador_nome: str
    colaborador_email: str
    data: str
    categoria: Categoria
    valor_centavos: int
    descricao: str
    comprovante: str
    situacao: Situacao
    motivo_recusa: str | None


class Resumo(BaseModel):
    mes: str
    totais_centavos: dict[str, int]
    total_geral_centavos: int


@router.post("/despesas", status_code=201, response_model=DespesaSaida)
def lancar(dados: NovaDespesa, conn: Conexao, agora: Agora):
    dominio.validar_valor(dados.categoria, dados.valor_centavos)
    dominio.validar_data(dados.data, agora)
    registro = dados.model_dump()
    registro["colaborador_email"] = dominio.normalizar_email(dados.colaborador_email)
    registro["data"] = dados.data.isoformat()
    registro["situacao"] = dominio.SITUACAO_INICIAL
    with banco.transacao(conn):
        dominio.verificar_duplicidade(
            repo.existe_comprovante(conn, registro["colaborador_email"], registro["comprovante"])
        )
        novo_id = repo.inserir(conn, registro)
    return repo.buscar(conn, novo_id)


@router.get("/despesas", response_model=list[DespesaSaida])
def listar(
    conn: Conexao,
    email: Annotated[Email | None, Query()] = None,
    situacao: Annotated[Situacao | None, Query()] = None,
):
    return repo.listar(conn, dominio.normalizar_email(email) if email else None, situacao)


def _mudar(conn: sqlite3.Connection, id_: int, nova: str, motivo: str | None = None) -> dict:
    with banco.transacao(conn):
        despesa = repo.buscar(conn, id_)
        dominio.garantir_existe(despesa)
        dominio.validar_transicao(despesa["situacao"], nova)
        repo.mudar_situacao(conn, id_, nova, motivo)
    return repo.buscar(conn, id_)


@router.post("/despesas/{id}/aprovar", response_model=DespesaSaida)
def aprovar(id: IdDespesa, conn: Conexao):
    return _mudar(conn, id, "APROVADA")


@router.post("/despesas/{id}/recusar", response_model=DespesaSaida)
def recusar(id: IdDespesa, conn: Conexao, corpo: Recusa | None = None):
    dominio.garantir_existe(repo.buscar(conn, id))
    # PR-12: RN-08 é conferida antes de RN-07.
    motivo = dominio.validar_motivo(corpo.motivo if corpo else None)
    return _mudar(conn, id, "RECUSADA", motivo)


@router.post("/despesas/{id}/pagar", response_model=DespesaSaida)
def pagar(id: IdDespesa, conn: Conexao):
    return _mudar(conn, id, "PAGA")


@router.delete("/despesas/{id}", status_code=204)
def excluir(id: IdDespesa, conn: Conexao):
    with banco.transacao(conn):
        despesa = repo.buscar(conn, id)
        dominio.garantir_existe(despesa)
        dominio.validar_exclusao(despesa["situacao"])
        repo.excluir(conn, id)
    return Response(status_code=204)


@router.get("/relatorios/mensal", response_model=Resumo)
def resumo_mensal(mes: Annotated[Mes, Query()], conn: Conexao):
    inicio, fim = dominio.intervalo_do_mes(mes)
    somas = repo.somar_mes(conn, inicio, fim, dominio.SITUACOES_NO_RESUMO)
    return dominio.montar_resumo(mes, somas)
