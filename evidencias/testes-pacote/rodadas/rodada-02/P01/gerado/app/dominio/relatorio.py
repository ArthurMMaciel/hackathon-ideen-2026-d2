"""Relatório mensal por tipo. Módulo puro."""

import calendar
from datetime import date

from app.dominio.equipamentos import TIPOS


def periodo_do_mes(ano: int, mes: int) -> tuple[date, date]:
    # RN-10: do dia 1 ao último dia do mês, inclusive
    return date(ano, mes, 1), date(ano, mes, calendar.monthrange(ano, mes)[1])


def montar_relatorio(ano: int, mes: int, contagens: dict[str, int]) -> dict:
    # RN-10: sempre os 3 tipos, na ordem do pedido; tipo sem empréstimo aparece com 0
    return {
        "mes": f"{ano:04d}-{mes:02d}",
        "itens": [{"tipo": tipo, "quantidade": contagens.get(tipo, 0)} for tipo in TIPOS],
    }
