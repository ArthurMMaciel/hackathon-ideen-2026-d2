"""Regras de reserva. Funções puras: recebem dados e `agora`, sem FastAPI e sem SQL."""

from collections.abc import Iterable
from datetime import datetime, timedelta

from app.erros import conflito, regra_violada

ATIVA = "ATIVA"
CANCELADA = "CANCELADA"
DURACAO_MINIMA = timedelta(minutes=15)
DURACAO_MAXIMA = timedelta(hours=4)


def sobrepoe(a_inicio: datetime, a_fim: datetime, b_inicio: datetime, b_fim: datetime) -> bool:
    # RN-01: intervalos semiabertos [início, fim); encostar não é sobrepor.
    return a_inicio < b_fim and b_inicio < a_fim


def bloqueia_horario(status: str) -> bool:
    # RN-06: reserva cancelada não ocupa horário.
    return status == ATIVA


def validar_intervalo(inicio: datetime, fim: datetime) -> None:
    # RN-09
    if fim <= inicio:
        raise regra_violada("INTERVALO_INVALIDO", "O fim precisa ser posterior ao início.")


def validar_duracao(inicio: datetime, fim: datetime) -> None:
    # RN-02: entre 15 minutos e 4 horas, inclusive.
    duracao = fim - inicio
    if duracao < DURACAO_MINIMA or duracao > DURACAO_MAXIMA:
        raise regra_violada(
            "DURACAO_INVALIDA", "A reserva precisa durar no mínimo 15 minutos e no máximo 4 horas."
        )


def validar_inicio_futuro(inicio: datetime, agora: datetime) -> None:
    # RN-03: início >= agora (PR-03).
    if inicio < agora:
        raise regra_violada("INICIO_NO_PASSADO", "Não é possível reservar com início no passado.")


def validar_participantes(participantes: int, capacidade: int) -> None:
    # RN-04: participantes até a capacidade da sala, inclusive.
    if participantes > capacidade:
        raise regra_violada(
            "CAPACIDADE_EXCEDIDA",
            f"A sala comporta no máximo {capacidade} participantes.",
        )


def verificar_conflito(existentes: Iterable[dict], inicio: datetime, fim: datetime) -> None:
    # RN-01 com RN-06: só reservas ativas da mesma sala bloqueiam.
    for r in existentes:
        if bloqueia_horario(r["status"]) and sobrepoe(r["inicio"], r["fim"], inicio, fim):
            raise conflito(
                "CONFLITO_HORARIO",
                "Conflito de horário: a sala já tem reserva ativa que se sobrepõe a este intervalo.",
            )


def validar_cancelamento(status: str, inicio: datetime, agora: datetime) -> None:
    # RN-05: só reserva ativa e futura (início > agora) pode ser cancelada.
    if status == CANCELADA:
        raise conflito("RESERVA_JA_CANCELADA", "Esta reserva já está cancelada.")
    if inicio <= agora:
        raise regra_violada(
            "CANCELAMENTO_NAO_PERMITIDO", "Só reservas futuras podem ser canceladas."
        )
