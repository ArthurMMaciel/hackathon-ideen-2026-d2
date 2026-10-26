"""Cada teste recebe banco novo e relógio fixo que pode avançar."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from app.relogio import FUSO, obter_agora

# Segunda-feira, 09:00, bem no futuro. Ajuste se o pedido exigir outro dia ou horário.
AGORA_INICIAL = datetime(2030, 1, 7, 9, 0, tzinfo=FUSO)


class RelogioDeTeste:
    def __init__(self, inicio: datetime):
        self.agora = inicio

    def __call__(self) -> datetime:
        return self.agora

    def avancar(self, **delta) -> None:
        """Ex.: relogio.avancar(hours=3) para tornar passado o que era futuro."""
        self.agora += timedelta(**delta)


@pytest.fixture
def relogio() -> RelogioDeTeste:
    return RelogioDeTeste(AGORA_INICIAL)


@pytest.fixture
def cliente(tmp_path, relogio):
    app = criar_app(str(tmp_path / "teste.db"))
    app.dependency_overrides[obter_agora] = relogio
    with TestClient(app) as c:
        yield c


def iso(dia: datetime, hora: int, minuto: int = 0) -> str:
    """Monta horário ISO 8601 com offset no mesmo dia de `dia`."""
    return dia.replace(hour=hora, minute=minuto, second=0, microsecond=0).isoformat()
