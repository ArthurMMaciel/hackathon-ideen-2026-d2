"""Testes de ataque: injeção de SQL, XSS armazenado, limites de entrada e vazamento de erro."""

import pytest

from tests.test_criterios_aceite import D1, reserva
from tests.conftest import iso

INJECAO = "'; DROP TABLE reservas; --"
XSS = "<script>alert(1)</script>"


@pytest.mark.parametrize("campo", ["responsavel_nome", "titulo"])
def test_seguranca_injecao_sql_campos_de_reserva(cliente, campo):
    r = cliente.post("/api/reservas", json=reserva(**{campo: INJECAO}))
    assert r.status_code == 201
    assert r.json()[campo] == INJECAO  # gravado literalmente
    agenda = cliente.get("/api/reservas", params={"data": "2030-01-08"})
    assert agenda.status_code == 200 and len(agenda.json()) == 1  # tabela intacta
    assert len(cliente.get("/api/salas").json()) == 6


def test_seguranca_injecao_sql_email(cliente):
    r = cliente.post("/api/reservas", json=reserva(responsavel_email="x'--@exemplo.com"))
    assert r.status_code == 201 and r.json()["responsavel_email"] == "x'--@exemplo.com"


def test_seguranca_injecao_sql_nome_da_sala(cliente):
    r = cliente.post("/api/salas", json={"nome": "'; DROP TABLE salas; --", "local": "COWORKING", "capacidade": 3})
    assert r.status_code == 201 and r.json()["nome"] == "'; DROP TABLE salas; --"
    assert len(cliente.get("/api/salas").json()) == 7


@pytest.mark.parametrize(
    "caminho,params",
    [
        ("/api/salas/livres", {"inicio": iso(D1, 10), "fim": iso(D1, 11), "local": "SAO_PAULO' OR '1'='1"}),
        ("/api/salas/livres", {"inicio": iso(D1, 10), "fim": iso(D1, 11), "capacidade_minima": "1 OR 1=1"}),
        ("/api/reservas", {"data": "2030-01-08' OR '1'='1"}),
        ("/api/reservas", {"data": "2030-01-08", "sala_id": "1 OR 1=1"}),
        ("/api/relatorios/ocupacao", {"data": INJECAO}),
        ("/api/salas/1 OR 1=1", None),
    ],
)
def test_seguranca_injecao_sql_parametros(cliente, caminho, params):
    r = cliente.get(caminho, params=params)
    assert r.status_code == 422
    assert len(cliente.get("/api/salas").json()) == 6


def test_seguranca_xss_texto_literal(cliente):
    r = cliente.post("/api/reservas", json=reserva(titulo=XSS, responsavel_nome=XSS))
    assert r.status_code == 201
    corpo = cliente.get(f"/api/reservas/{r.json()['id']}").json()
    assert corpo["titulo"] == XSS and corpo["responsavel_nome"] == XSS


def test_seguranca_tela_nao_usa_innerhtml(cliente):
    html = cliente.get("/").text
    assert "innerHTML" not in html.replace("nunca innerHTML", "")
    assert "textContent" in html


@pytest.mark.parametrize(
    "alteracao",
    [
        {"titulo": "x" * 201},
        {"responsavel_nome": "x" * 201},
        {"responsavel_email": "a" * 250 + "@ex.com"},
        {"participantes": -1},
        {"sala_id": -1},
    ],
)
def test_seguranca_limites_reserva(cliente, alteracao):
    assert cliente.post("/api/reservas", json=reserva(**alteracao)).status_code == 422


@pytest.mark.parametrize(
    "corpo",
    [
        {"nome": "x" * 201, "local": "COWORKING", "capacidade": 3},
        {"nome": "Sala X", "local": "COWORKING", "capacidade": -5},
        {"nome": "Sala X", "local": "COWORKING", "capacidade": 3, "recursos": ["TV"] * 50},
    ],
)
def test_seguranca_limites_sala(cliente, corpo):
    assert cliente.post("/api/salas", json=corpo).status_code == 422


def test_seguranca_limite_capacidade_minima_negativa(cliente):
    r = cliente.get("/api/salas/livres", params={"inicio": iso(D1, 10), "fim": iso(D1, 11), "capacidade_minima": -1})
    assert r.status_code == 422


@pytest.mark.parametrize("caminho", ["/api/reservas", "/api/salas"])
def test_seguranca_json_malformado_sem_vazamento(cliente, caminho):
    r = cliente.post(caminho, content=b'{"titulo": "abc",', headers={"Content-Type": "application/json"})
    assert 400 <= r.status_code < 500
    texto = r.text.lower()
    for proibido in ("traceback", "sqlite", "select ", "insert ", 'file "'):
        assert proibido not in texto


def test_seguranca_sem_debug_e_sem_cors(cliente):
    assert cliente.app.debug is False
    r = cliente.get("/api/salas", headers={"Origin": "http://atacante.exemplo"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_seguranca_tela_ignora_cabecalho_range(cliente):
    # CVE-2025-62727: a tela não passa pelo parser de Range do FileResponse.
    faixas = "bytes=" + ",".join(f"{i}-{i}" for i in range(0, 4000, 2))
    r = cliente.get("/", headers={"Range": faixas})
    assert r.status_code == 200
    assert "accept-ranges" not in {k.lower() for k in r.headers}
