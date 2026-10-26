"""Relógio injetável. Regras de negócio recebem `agora` daqui, nunca de datetime.now()."""

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")


def agora() -> datetime:
    """Hora atual no fuso padrão. APP_AGORA (ISO 8601 com offset) fixa o relógio do servidor real."""
    fixo = os.environ.get("APP_AGORA")
    if fixo:
        return datetime.fromisoformat(fixo).astimezone(FUSO)
    return datetime.now(FUSO)


def obter_agora() -> datetime:
    """Dependência do FastAPI. Os testes substituem com app.dependency_overrides[obter_agora]."""
    return agora()


def para_banco(momento: datetime) -> str:
    """Grava sempre em UTC, no mesmo formato, para comparar texto com texto no SQL."""
    return momento.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def do_banco(texto: str) -> datetime:
    return datetime.fromisoformat(texto).astimezone(FUSO)
