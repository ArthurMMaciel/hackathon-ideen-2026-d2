"""Modelos Pydantic de entrada e saída da API."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, AwareDatetime, BaseModel, Field, StringConstraints, field_validator

# Identificadores cabem no inteiro de 64 bits do SQLite; acima disso o driver estoura (erro 500).
ID_MAXIMO = 2**63 - 1
Id = Annotated[int, Field(ge=1, le=ID_MAXIMO)]

# PR-10: datas aceitas entre os anos 2000 e 2100; fora disso a conversão para UTC pode estourar.
ANO_MINIMO, ANO_MAXIMO = 2000, 2100


def _ano_suportado(valor):
    if not ANO_MINIMO <= valor.year <= ANO_MAXIMO:
        raise ValueError(f"o ano precisa estar entre {ANO_MINIMO} e {ANO_MAXIMO}")
    return valor


DataHora = Annotated[AwareDatetime, AfterValidator(_ano_suportado)]
Data = Annotated[date, AfterValidator(_ano_suportado)]

Local = Literal["SAO_PAULO", "ARARAQUARA", "COWORKING"]
Recurso = Literal["TV", "VIDEOCONFERENCIA", "QUADRO"]
Status = Literal["ATIVA", "CANCELADA"]
# PR-09: textos livres com até 200 caracteres, sem aceitar só espaços.
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
# RN-11: e-mail no formato texto@dominio.ext, até 254 caracteres.
Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]


class SalaEntrada(BaseModel):
    nome: Texto
    local: Local
    capacidade: int = Field(ge=1, le=500)  # RN-10
    recursos: list[Recurso] = Field(default_factory=list, max_length=3)

    @field_validator("recursos")
    @classmethod
    def sem_repeticao(cls, recursos: list[str]) -> list[str]:
        # RN-10: recursos sem repetição.
        if len(set(recursos)) != len(recursos):
            raise ValueError("recursos não podem se repetir")
        return recursos


class SalaSaida(BaseModel):
    id: int
    nome: str
    local: Local
    capacidade: int
    recursos: list[Recurso]


class ReservaEntrada(BaseModel):
    sala_id: Id
    responsavel_nome: Texto
    responsavel_email: Email
    titulo: Texto
    participantes: int = Field(ge=1, le=1000)  # RN-04 (limite inferior)
    inicio: DataHora
    fim: DataHora


class ReservaSaida(BaseModel):
    id: int
    sala_id: int
    responsavel_nome: str
    responsavel_email: str
    titulo: str
    participantes: int
    inicio: datetime
    fim: datetime
    status: Status
    criada_em: datetime
    cancelada_em: datetime | None


class OcupacaoSala(BaseModel):
    sala_id: int
    nome: str
    local: Local
    minutos_ocupados: int
    taxa_ocupacao: float


class RelatorioOcupacao(BaseModel):
    data: date
    janela_inicio: str
    janela_fim: str
    minutos_janela: int
    salas: list[OcupacaoSala]
