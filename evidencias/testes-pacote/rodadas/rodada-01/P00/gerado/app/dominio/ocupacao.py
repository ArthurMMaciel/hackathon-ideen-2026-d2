"""Relatório de ocupação. Função pura."""

from collections.abc import Iterable
from datetime import date, datetime, time

from app.dominio.reservas import bloqueia_horario
from app.relogio import FUSO

# RN-08: janela de 08:00 a 18:00 (600 minutos) no dia civil do fuso padrão (PR-04).
JANELA_INICIO = time(8, 0)
JANELA_FIM = time(18, 0)


def janela(dia: date) -> tuple[datetime, datetime]:
    return datetime.combine(dia, JANELA_INICIO, FUSO), datetime.combine(dia, JANELA_FIM, FUSO)


def calcular(salas: Iterable[dict], reservas: Iterable[dict], dia: date) -> list[dict]:
    """RN-08: minutos de reservas ativas dentro da janela / 600 x 100, com 1 casa decimal (PR-05)."""
    abre, fecha = janela(dia)
    minutos_janela = (fecha - abre).total_seconds() / 60
    minutos: dict[int, float] = {}
    for r in reservas:
        if not bloqueia_horario(r["status"]):  # RN-06
            continue
        inicio, fim = max(r["inicio"], abre), min(r["fim"], fecha)
        if fim > inicio:
            minutos[r["sala_id"]] = minutos.get(r["sala_id"], 0) + (fim - inicio).total_seconds() / 60
    resultado = []
    for s in salas:
        ocupados = minutos.get(s["id"], 0)
        resultado.append(
            {
                "sala_id": s["id"],
                "nome": s["nome"],
                "local": s["local"],
                "minutos_ocupados": int(round(ocupados)),
                "taxa_ocupacao": round(ocupados / minutos_janela * 100, 1),
            }
        )
    return resultado
