"""Cálculo puro de ocupação diária."""

from datetime import datetime


def ocupacao(intervalos: list[tuple[datetime, datetime]], janela_inicio: datetime,
             janela_fim: datetime) -> tuple[int, float]:
    # RN-06
    minutos = sum(max(0, int((min(fim, janela_fim) - max(inicio, janela_inicio)).total_seconds() / 60))
                  for inicio, fim in intervalos)
    minutos = min(600, minutos)
    return minutos, round(minutos * 100 / 600, 2)
