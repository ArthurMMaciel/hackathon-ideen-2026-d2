"""Regras da reserva. Funções puras: recebem dados e `agora`, levantam erros de negócio."""

from datetime import datetime, timedelta

from app.dominio.erros import conflito, regra_violada
from app.dominio.intervalos import sobrepoe

ATIVA = "ATIVA"
CANCELADA = "CANCELADA"

DURACAO_MINIMA = timedelta(minutes=15)
DURACAO_MAXIMA = timedelta(hours=4)


def validar_duracao(inicio: datetime, fim: datetime) -> None:
    # RN-02: entre 15 minutos e 4 horas, inclusive.
    duracao = fim - inicio
    if duracao < DURACAO_MINIMA or duracao > DURACAO_MAXIMA:
        raise regra_violada(
            "DURACAO_INVALIDA",
            "A reserva precisa durar no mínimo 15 minutos e no máximo 4 horas, com o fim depois do início.",
        )


def validar_inicio(inicio: datetime, agora: datetime) -> None:
    # RN-03: não reservar no passado; início igual ao momento atual é aceito.
    if inicio < agora:
        raise regra_violada("INICIO_NO_PASSADO", "Não é possível reservar com início no passado.")


def validar_participantes(participantes: int, capacidade: int) -> None:
    # RN-04: participantes não passam da capacidade da sala.
    if participantes > capacidade:
        raise regra_violada(
            "CAPACIDADE_EXCEDIDA",
            f"A sala comporta {capacidade} pessoas; a reserva tem {participantes} participantes.",
        )


def verificar_conflito(inicio: datetime, fim: datetime, existentes: list[tuple[datetime, datetime]]) -> None:
    # RN-01: reservas ATIVAS da mesma sala não se sobrepõem (as canceladas já vêm filtradas, RN-06).
    for outro_inicio, outro_fim in existentes:
        if sobrepoe(inicio, fim, outro_inicio, outro_fim):
            raise conflito(
                "CONFLITO_HORARIO",
                "Conflito de horário: a sala já tem reserva ativa que se sobrepõe a este intervalo.",
            )


def validar_cancelamento(status: str, inicio: datetime, agora: datetime) -> None:
    # RN-05: só reserva ATIVA e futura (início depois de agora) pode ser cancelada.
    if status == CANCELADA:
        raise conflito("RESERVA_JA_CANCELADA", "Esta reserva já está cancelada.")
    if inicio <= agora:
        raise conflito(
            "RESERVA_NAO_FUTURA", "Só reservas futuras podem ser canceladas; esta já começou ou já passou."
        )
