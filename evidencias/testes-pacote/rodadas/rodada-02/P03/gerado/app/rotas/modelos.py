"""Modelos Pydantic de entrada e saída, com os tipos de app/tipos.py."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.tipos import ID_MAXIMO, DataHora, Email, Texto

# Faixa larga só para evitar estouro; a regra de negócio (RN-01, RN-02) fica no domínio.
# strict: no corpo JSON, true/false, 1.5 e "10" são tipo errado (422), não viram número.
InteiroLimitado = Annotated[int, Field(ge=-1_000_000, le=1_000_000, strict=True)]
IdNoCorpo = Annotated[int, Field(ge=1, le=ID_MAXIMO, strict=True)]
Modalidade = Literal["PRESENCIAL", "ONLINE"]
Situacao = Literal["CONFIRMADA", "ESPERA", "CANCELADA", "PRESENTE", "AUSENTE"]


class TurmaEntrada(BaseModel):
    titulo: Texto
    inicio: DataHora
    duracao_minutos: InteiroLimitado
    modalidade: Modalidade
    vagas: InteiroLimitado


class TurmaSaida(BaseModel):
    id: int
    titulo: str
    inicio: datetime
    duracao_minutos: int
    modalidade: Modalidade
    vagas: int
    vagas_restantes: int


class InscricaoEntrada(BaseModel):
    turma_id: IdNoCorpo
    nome: Texto
    email: Email


class InscricaoSaida(BaseModel):
    id: int
    turma_id: int
    nome: str
    email: str
    situacao: Situacao
    criada_em: datetime
    posicao_espera: int | None


class CancelamentoSaida(BaseModel):
    inscricao: InscricaoSaida
    promovida: InscricaoSaida | None


class PresencaEntrada(BaseModel):
    situacao: Literal["PRESENTE", "AUSENTE"]


class RelatorioPresencaSaida(BaseModel):
    turma_id: int
    presentes: int
    ausentes: int
    taxa_presenca_percentual: float | None
