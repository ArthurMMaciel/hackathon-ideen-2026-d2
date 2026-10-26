"""Entradas inválidas comuns devolvem 4xx, nunca 500 (achados R-01 e R-02 da revisão)."""

import pytest

from tests.test_criterios_aceite import reserva

GRANDE = 99999999999999999999  # maior que o inteiro de 64 bits do SQLite


@pytest.mark.parametrize(
    "metodo,caminho,params",
    [
        ("GET", f"/api/salas/{GRANDE}", None),
        ("GET", f"/api/reservas/{GRANDE}", None),
        ("POST", f"/api/reservas/{GRANDE}/cancelar", None),
        ("GET", "/api/reservas", {"data": "2030-01-08", "sala_id": GRANDE}),
        ("GET", "/api/reservas", {"data": "9999-12-31"}),
        ("GET", "/api/relatorios/ocupacao", {"data": "0001-01-01"}),
        ("GET", "/api/salas/livres", {"inicio": "9999-12-31T22:00:00-03:00", "fim": "9999-12-31T23:00:00-03:00"}),
        ("GET", "/api/salas/livres", {"inicio": "0001-01-01T00:00:00+05:00", "fim": "0001-01-01T01:00:00+05:00"}),
        ("GET", "/api/salas/abc", None),
    ],
)
def test_robustez_parametros_fora_da_faixa(cliente, metodo, caminho, params):
    r = cliente.request(metodo, caminho, params=params)
    assert r.status_code == 422


@pytest.mark.parametrize(
    "alteracao",
    [
        {"sala_id": GRANDE},
        {"inicio": "9999-12-31T22:00:00-03:00", "fim": "9999-12-31T23:00:00-03:00"},
        {"participantes": "abc"},
        {"sala_id": "um"},
    ],
)
def test_robustez_corpo_invalido(cliente, alteracao):
    assert cliente.post("/api/reservas", json=reserva(**alteracao)).status_code == 422


def test_robustez_campo_faltando(cliente):
    corpo = reserva()
    del corpo["titulo"]
    r = cliente.post("/api/reservas", json=corpo)
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["body", "titulo"]
