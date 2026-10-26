"""Intervalos semiabertos [inicio, fim)."""

from datetime import datetime


def sobrepoe(a_inicio: datetime, a_fim: datetime, b_inicio: datetime, b_fim: datetime) -> bool:
    # RN-01: encostar (a.fim == b.inicio) não é sobrepor.
    return a_inicio < b_fim and b_inicio < a_fim


def minutos_em_comum(a_inicio: datetime, a_fim: datetime, b_inicio: datetime, b_fim: datetime) -> float:
    inicio = max(a_inicio, b_inicio)
    fim = min(a_fim, b_fim)
    if fim <= inicio:
        return 0.0
    return (fim - inicio).total_seconds() / 60
