"""Rotas de despesas e do relatório mensal."""

import re
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app import banco
from app.banco import obter_conexao
from app.dominio import despesas as dominio
from app.erros import conflito, nao_encontrado
from app.relogio import obter_agora
from app.repositorio import despesas as repo

router = APIRouter(prefix="/api")

PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PADRAO_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Mês AAAA-MM com ano entre 1900 e 2999: evita datas fora da faixa do Python (ano 0 ou 10000).
PADRAO_MES = r"^(19|2\d)\d{2}-(0[1-9]|1[0-2])$"

# Identificador dentro da faixa do INTEGER do SQLite; fora dela, 422 em vez de erro 500.
IdDespesa = Annotated[int, Path(ge=1, le=2**63 - 1)]


class Categoria(str, Enum):
    TRANSPORTE = "TRANSPORTE"
    HOSPEDAGEM = "HOSPEDAGEM"
    ALIMENTACAO = "ALIMENTACAO"
    OUTROS = "OUTROS"


class Situacao(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADA = "APROVADA"
    RECUSADA = "RECUSADA"
    PAGA = "PAGA"


def _texto_obrigatorio(valor: str) -> str:
    valor = valor.strip()
    if not valor:
        raise ValueError("não pode ficar em branco")
    return valor


class DespesaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    colaborador_nome: str = Field(min_length=1, max_length=200)
    colaborador_email: str = Field(min_length=3, max_length=200)
    data_despesa: date
    categoria: Categoria
    valor: Decimal = Field(max_digits=12, decimal_places=2, allow_inf_nan=False)
    descricao: str = Field(min_length=1, max_length=200)
    numero_comprovante: str = Field(min_length=1, max_length=200)

    @field_validator("colaborador_nome", "descricao", "numero_comprovante")
    @classmethod
    def _sem_branco(cls, valor: str) -> str:
        return _texto_obrigatorio(valor)

    @field_validator("colaborador_email")
    @classmethod
    def _email(cls, valor: str) -> str:
        # PR-03: e-mail com formato válido, comparado sem diferenciar maiúsculas.
        valor = valor.strip().lower()
        if not PADRAO_EMAIL.match(valor):
            raise ValueError("e-mail em formato inválido")
        return valor

    @field_validator("data_despesa", mode="before")
    @classmethod
    def _so_data(cls, valor):
        # PR-02: a data da despesa é só o dia, no formato AAAA-MM-DD.
        if not isinstance(valor, str) or not PADRAO_DATA.match(valor):
            raise ValueError("use o formato AAAA-MM-DD")
        return valor


class RecusaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motivo: str | None = Field(default=None, max_length=500)


class DespesaSaida(BaseModel):
    id: int
    colaborador_nome: str
    colaborador_email: str
    data_despesa: date
    categoria: Categoria
    valor: float
    descricao: str
    numero_comprovante: str
    situacao: Situacao
    motivo_recusa: str | None
    criada_em: datetime
    atualizada_em: datetime


class ResumoSaida(BaseModel):
    mes: str
    situacoes_consideradas: list[Situacao]
    totais_por_categoria: dict[Categoria, float]
    total_geral: float
    quantidade: int


def _saida(despesa: dict) -> DespesaSaida:
    return DespesaSaida(**{k: v for k, v in despesa.items() if k != "valor_centavos"},
                        valor=despesa["valor_centavos"] / 100)


def _obter_ou_404(conn: sqlite3.Connection, despesa_id: int) -> dict:
    despesa = repo.obter(conn, despesa_id)
    if despesa is None:
        raise nao_encontrado("DESPESA_NAO_ENCONTRADA", f"Despesa {despesa_id} não encontrada.")
    return despesa


@router.post("/despesas", status_code=201, response_model=DespesaSaida)
def lancar(entrada: DespesaEntrada, conn=Depends(obter_conexao), agora=Depends(obter_agora)):
    valor_centavos = int(entrada.valor * 100)
    dominio.validar_valor(valor_centavos)  # RN-01
    dominio.validar_limite(entrada.categoria.value, valor_centavos)  # RN-02
    dominio.validar_data(entrada.data_despesa, agora)  # RN-03, RN-04
    with banco.transacao(conn):
        # RN-05: conferir duplicidade e inserir na mesma transação.
        dominio.validar_comprovante_unico(
            repo.existe_comprovante(conn, entrada.colaborador_email, entrada.numero_comprovante)
        )
        try:
            novo_id = repo.inserir(
                conn,
                {
                    "colaborador_nome": entrada.colaborador_nome,
                    "colaborador_email": entrada.colaborador_email,
                    "data_despesa": entrada.data_despesa,
                    "categoria": entrada.categoria.value,
                    "valor_centavos": valor_centavos,
                    "descricao": entrada.descricao,
                    "numero_comprovante": entrada.numero_comprovante,
                    "situacao": dominio.SITUACAO_INICIAL,  # RN-06
                },
                agora,
            )
        except sqlite3.IntegrityError:
            raise conflito("COMPROVANTE_DUPLICADO",
                           "Este número de comprovante já foi lançado por este colaborador.")
    return _saida(repo.obter(conn, novo_id))


@router.get("/despesas", response_model=list[DespesaSaida])
def listar(
    email: str | None = Query(default=None, max_length=200),
    situacao: Situacao | None = None,
    conn=Depends(obter_conexao),
):
    email_normalizado = email.strip().lower() if email and email.strip() else None
    return [_saida(d) for d in repo.listar(conn, email_normalizado, situacao.value if situacao else None)]


@router.get("/despesas/{despesa_id}", response_model=DespesaSaida)
def obter(despesa_id: IdDespesa, conn=Depends(obter_conexao)):
    return _saida(_obter_ou_404(conn, despesa_id))


def _mudar(conn, despesa_id: int, nova: str, agora, motivo: str | None = None) -> DespesaSaida:
    with banco.transacao(conn):
        despesa = _obter_ou_404(conn, despesa_id)
        dominio.validar_transicao(despesa["situacao"], nova)  # RN-07
        repo.mudar_situacao(conn, despesa_id, nova, motivo, agora)
    return _saida(repo.obter(conn, despesa_id))


@router.post("/despesas/{despesa_id}/aprovar", response_model=DespesaSaida)
def aprovar(despesa_id: IdDespesa, conn=Depends(obter_conexao), agora=Depends(obter_agora)):
    return _mudar(conn, despesa_id, "APROVADA", agora)


@router.post("/despesas/{despesa_id}/recusar", response_model=DespesaSaida)
def recusar(
    despesa_id: IdDespesa,
    entrada: RecusaEntrada | None = Body(default=None),
    conn=Depends(obter_conexao),
    agora=Depends(obter_agora),
):
    _obter_ou_404(conn, despesa_id)
    motivo = dominio.validar_motivo(entrada.motivo if entrada else None)  # RN-08
    return _mudar(conn, despesa_id, "RECUSADA", agora, motivo)


@router.post("/despesas/{despesa_id}/pagar", response_model=DespesaSaida)
def pagar(despesa_id: IdDespesa, conn=Depends(obter_conexao), agora=Depends(obter_agora)):
    return _mudar(conn, despesa_id, "PAGA", agora)


@router.delete("/despesas/{despesa_id}", status_code=204)
def excluir(despesa_id: IdDespesa, conn=Depends(obter_conexao)):
    with banco.transacao(conn):
        despesa = _obter_ou_404(conn, despesa_id)
        dominio.validar_exclusao(despesa["situacao"])  # RN-09
        repo.excluir(conn, despesa_id)
    return Response(status_code=204)


@router.get("/relatorios/mensal", response_model=ResumoSaida)
def resumo_mensal(
    mes: str = Query(pattern=PADRAO_MES),
    conn=Depends(obter_conexao),
):
    ano, numero = (int(parte) for parte in mes.split("-"))
    inicio, fim = dominio.intervalo_do_mes(ano, numero)  # PR-08
    resumo = dominio.resumir_mes(repo.do_periodo(conn, inicio, fim))  # RN-10
    return ResumoSaida(
        mes=mes,
        situacoes_consideradas=list(dominio.SITUACOES_NO_RESUMO),
        totais_por_categoria={c: v / 100 for c, v in resumo["totais_centavos"].items()},
        total_geral=resumo["total_centavos"] / 100,
        quantidade=resumo["quantidade"],
    )
