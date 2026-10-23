"""Modelos Pydantic de entrada e saída e conversão das linhas do banco."""

import sqlite3
from datetime import datetime
from typing import Annotated, Literal

from fastapi import Path
from pydantic import AwareDatetime, BaseModel, Field, StringConstraints, field_validator

from app.dominio import inscricoes as regras_inscricao
from app.dominio import turmas as regras_turma
from app.relogio import do_banco

PADRAO_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Identificadores no caminho: inteiro positivo que cabe no INTEGER do SQLite (evita erro 500 com número enorme).
Id = Annotated[int, Path(ge=1, le=9_223_372_036_854_775_807)]
# RN-03: texto obrigatório, sem contar espaços nas pontas, até 200 caracteres.
Texto200 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
ANO_MINIMO, ANO_MAXIMO = 2000, 2999


class TurmaEntrada(BaseModel):
    titulo: Texto200  # RN-03
    inicio: AwareDatetime  # horário sem fuso é recusado com 422
    duracao_minutos: int = Field(ge=1, le=1440)  # RN-02
    modalidade: Literal["PRESENCIAL", "ONLINE"]
    vagas: int = Field(ge=1, le=50)  # RN-01

    @field_validator("inicio")
    @classmethod
    def ano_razoavel(cls, valor: datetime) -> datetime:
        # Faixa de anos evita estouro de data ao converter para UTC ou subtrair 24 h.
        if not ANO_MINIMO <= valor.year <= ANO_MAXIMO:
            raise ValueError(f"o ano do início deve estar entre {ANO_MINIMO} e {ANO_MAXIMO}")
        return valor


class TurmaSaida(BaseModel):
    id: int
    titulo: str
    inicio: datetime
    duracao_minutos: int
    modalidade: str
    vagas: int
    vagas_restantes: int


class InscricaoEntrada(BaseModel):
    nome: Texto200  # RN-03
    email: str = Field(min_length=3, max_length=254, pattern=PADRAO_EMAIL)  # RN-03

    @field_validator("email")
    @classmethod
    def minusculas(cls, valor: str) -> str:
        return valor.lower()  # PR-04


class InscricaoSaida(BaseModel):
    id: int
    turma_id: int
    nome: str
    email: str
    situacao: str
    criada_em: datetime
    posicao_espera: int | None


class PresencaEntrada(BaseModel):
    situacao: Literal["PRESENTE", "AUSENTE"]  # RN-11


class CancelamentoSaida(BaseModel):
    cancelada: InscricaoSaida
    promovida: InscricaoSaida | None


class TaxaPresencaSaida(BaseModel):
    turma_id: int
    presentes: int
    ausentes: int
    taxa_presenca: float | None


def turma_saida(linha: sqlite3.Row) -> TurmaSaida:
    return TurmaSaida(
        id=linha["id"],
        titulo=linha["titulo"],
        inicio=do_banco(linha["inicio"]),
        duracao_minutos=linha["duracao_minutos"],
        modalidade=linha["modalidade"],
        vagas=linha["vagas"],
        vagas_restantes=regras_turma.vagas_restantes(linha["vagas"], linha["ocupadas"]),
    )


def inscricao_saida(linha: sqlite3.Row, ids_espera: list[int]) -> InscricaoSaida:
    return InscricaoSaida(
        id=linha["id"],
        turma_id=linha["turma_id"],
        nome=linha["nome"],
        email=linha["email"],
        situacao=linha["situacao"],
        criada_em=do_banco(linha["criada_em"]),
        posicao_espera=regras_inscricao.posicao_na_espera(linha["id"], ids_espera),
    )
