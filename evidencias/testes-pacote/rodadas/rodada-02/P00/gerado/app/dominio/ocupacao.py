"""Relatório de ocupação por sala num dia."""

from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

from app.dominio.intervalos import minutos_em_comum

JANELA_INICIO = time(8, 0)
JANELA_FIM = time(18, 0)
MINUTOS_JANELA = 600


def _uma_casa(valor: float) -> float:
    # PR-07: 1 casa decimal, meio para cima.
    return float(Decimal(str(valor)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def janela(dia: date, fuso: ZoneInfo) -> tuple[datetime, datetime]:
    return datetime.combine(dia, JANELA_INICIO, fuso), datetime.combine(dia, JANELA_FIM, fuso)


def calcular(dia: date, fuso: ZoneInfo, salas: list[dict], reservas: list[dict]) -> dict:
    # RN-08: minutos de reservas ATIVAS dentro de [08:00, 18:00) / 600 * 100.
    # RN-06: `reservas` chega só com as ATIVAS; a conferência abaixo garante.
    inicio_janela, fim_janela = janela(dia, fuso)
    minutos: dict[int, float] = {s["id"]: 0.0 for s in salas}
    for r in reservas:
        if r["status"] != "ATIVA" or r["sala_id"] not in minutos:
            continue
        minutos[r["sala_id"]] += minutos_em_comum(r["inicio"], r["fim"], inicio_janela, fim_janela)
    linhas = []
    for s in salas:
        ocupados = minutos[s["id"]]
        linhas.append(
            {
                "sala_id": s["id"],
                "sala_nome": s["nome"],
                "local": s["local"],
                "minutos_ocupados": _uma_casa(ocupados),
                "taxa_ocupacao": _uma_casa(ocupados * 100 / MINUTOS_JANELA),
            }
        )
    return {
        "dia": dia.isoformat(),
        "janela_inicio": JANELA_INICIO.strftime("%H:%M"),
        "janela_fim": JANELA_FIM.strftime("%H:%M"),
        "minutos_janela": MINUTOS_JANELA,
        "salas": linhas,
    }
