"""Regras puras de reservas."""

from datetime import datetime, timedelta

from app.dominio.erros import conflito, regra_violada


def validar_duracao(inicio: datetime, fim: datetime) -> None:
    # RN-02
    duracao = fim - inicio
    if not timedelta(minutes=15) <= duracao <= timedelta(hours=4):
        raise regra_violada("DURACAO_INVALIDA", "A duração deve ficar entre 15 minutos e 4 horas.")


def validar_inicio(inicio: datetime, agora: datetime) -> None:
    # RN-03
    if inicio < agora:
        raise regra_violada("INICIO_PASSADO", "Não é possível reservar com início no passado.")


def validar_participantes(participantes: int, capacidade: int) -> None:
    # RN-04
    if participantes > capacidade:
        raise regra_violada("CAPACIDADE_EXCEDIDA", "Participantes excedem a capacidade da sala.")


def verificar_conflito(existe: bool) -> None:
    # RN-01
    if existe:
        raise conflito("CONFLITO_HORARIO", "Há conflito de horário nesta sala.")


def validar_cancelamento(status: str, inicio: datetime, agora: datetime) -> None:
    # RN-05
    if status == "CANCELADA":
        raise conflito("RESERVA_JA_CANCELADA", "A reserva já está cancelada.")
    if inicio <= agora:
        raise regra_violada("CANCELAMENTO_FORA_DO_PRAZO", "Só reservas futuras podem ser canceladas.")


def validar_intervalo(inicio: datetime, fim: datetime) -> None:
    if inicio >= fim:
        raise regra_violada("INTERVALO_INVALIDO", "O início deve ser anterior ao fim.")
