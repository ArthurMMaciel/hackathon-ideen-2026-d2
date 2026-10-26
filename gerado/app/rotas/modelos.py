"""Modelos Pydantic de entrada e saída, com os tipos de app/tipos.py."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

from app.tipos import DataHora, Email, Id, Texto

Local = Literal["SAO_PAULO", "ARARAQUARA", "COWORKING"]
Recurso = Literal["TV", "VIDEOCONFERENCIA", "QUADRO"]
Capacidade = Annotated[int, Field(ge=1, le=1000)]  # RN-09
Participantes = Annotated[int, Field(ge=1, le=1000)]  # RN-04 (mínimo 1)

# Frações de segundo são descartadas na entrada: o valor validado é o mesmo que vai ao banco (SPEC).
HorarioReserva = Annotated[DataHora, AfterValidator(lambda valor: valor.replace(microsecond=0))]


class SalaEntrada(BaseModel):
    nome: Texto
    local: Local
    capacidade: Capacidade
    recursos: Annotated[list[Recurso], Field(max_length=3)] = []


class Sala(BaseModel):
    id: int
    nome: str
    local: str
    capacidade: int
    recursos: list[str]


class ReservaEntrada(BaseModel):
    sala_id: Id
    responsavel_nome: Texto
    responsavel_email: Email
    titulo: Texto
    participantes: Participantes
    inicio: HorarioReserva
    fim: HorarioReserva


class Reserva(BaseModel):
    id: int
    sala_id: int
    sala_nome: str
    responsavel_nome: str
    responsavel_email: str
    titulo: str
    participantes: int
    inicio: datetime
    fim: datetime
    status: str


class OcupacaoSala(BaseModel):
    sala_id: int
    sala_nome: str
    local: str
    minutos_ocupados: float
    taxa_ocupacao: float


class Ocupacao(BaseModel):
    dia: str
    janela_inicio: str
    janela_fim: str
    minutos_janela: int
    salas: list[OcupacaoSala]
