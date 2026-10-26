"""Testes de ataque: injeção de SQL, XSS, validação de entrada e vazamento de erro."""

import re

import pytest

from tests.apoio import amanha, criar_sala, dados_reserva

INJECAO = "'; DROP TABLE reservas; --"
SCRIPT = "<script>alert(1)</script>"


def _tabelas_intactas(cliente):
    assert cliente.get("/api/salas").status_code == 200
    assert cliente.get("/api/reservas", params={"dia": "2030-01-08"}).status_code == 200
    assert cliente.get("/api/relatorios/ocupacao", params={"dia": "2030-01-08"}).status_code == 200


def test_injecao_sql_em_campos_de_texto_da_sala(cliente):
    r = cliente.post("/api/salas", json={"nome": INJECAO, "local": "SAO_PAULO", "capacidade": 4})
    assert r.status_code == 201
    assert r.json()["nome"] == INJECAO
    _tabelas_intactas(cliente)


@pytest.mark.parametrize("campo", ["responsavel_nome", "titulo"])
def test_injecao_sql_em_campos_de_texto_da_reserva(cliente, campo):
    sala = criar_sala(cliente)
    corpo = dados_reserva(sala["id"], amanha(10), amanha(11))
    corpo[campo] = INJECAO
    r = cliente.post("/api/reservas", json=corpo)
    assert r.status_code == 201
    assert r.json()[campo] == INJECAO
    _tabelas_intactas(cliente)
    assert len(cliente.get("/api/reservas", params={"dia": "2030-01-08"}).json()) == 1


def test_injecao_sql_no_email(cliente):
    sala = criar_sala(cliente)
    corpo = dados_reserva(sala["id"], amanha(10), amanha(11))
    corpo["responsavel_email"] = "x'--@exemplo.com"
    r = cliente.post("/api/reservas", json=corpo)
    assert r.status_code == 201
    assert r.json()["responsavel_email"] == "x'--@exemplo.com"
    _tabelas_intactas(cliente)


@pytest.mark.parametrize(
    "caminho,params",
    [
        ("/api/salas/livres", {"inicio": INJECAO, "fim": INJECAO}),
        ("/api/salas/livres", {"inicio": "2030-01-08T10:00:00-03:00", "fim": "2030-01-08T11:00:00-03:00",
                               "local": INJECAO}),
        ("/api/salas/livres", {"inicio": "2030-01-08T10:00:00-03:00", "fim": "2030-01-08T11:00:00-03:00",
                               "capacidade_minima": INJECAO}),
        ("/api/reservas", {"dia": INJECAO}),
        ("/api/reservas", {"dia": "2030-01-08", "sala_id": INJECAO}),
        ("/api/relatorios/ocupacao", {"dia": INJECAO}),
    ],
)
def test_injecao_sql_em_parametros_de_consulta(cliente, caminho, params):
    assert cliente.get(caminho, params=params).status_code == 422
    _tabelas_intactas(cliente)


def test_injecao_sql_no_caminho(cliente):
    assert cliente.get("/api/salas/1 OR 1=1").status_code == 422
    assert cliente.post("/api/reservas/1;DROP/cancelar").status_code in (404, 422)
    _tabelas_intactas(cliente)


def test_xss_texto_devolvido_literal(cliente):
    sala = criar_sala(cliente, nome=SCRIPT)
    assert sala["nome"] == SCRIPT
    corpo = dados_reserva(sala["id"], amanha(10), amanha(11))
    corpo["titulo"] = SCRIPT
    r = cliente.post("/api/reservas", json=corpo)
    assert r.status_code == 201
    agenda = cliente.get("/api/reservas", params={"dia": "2030-01-08"}).json()
    assert agenda[0]["titulo"] == SCRIPT
    assert agenda[0]["sala_nome"] == SCRIPT


def test_tela_nao_usa_innerhtml_com_dados(cliente):
    html = cliente.get("/").text
    # O único "innerHTML" permitido é o comentário do modelo; nenhuma atribuição ou inserção de HTML.
    assert not re.search(r"\.(innerHTML|outerHTML)\s*[+]?=|insertAdjacentHTML|document\.write", html)
    assert "textContent" in html


def test_texto_acima_do_limite_recusado(cliente):
    sala = criar_sala(cliente)
    corpo = dados_reserva(sala["id"], amanha(10), amanha(11))
    corpo["titulo"] = "x" * 201
    assert cliente.post("/api/reservas", json=corpo).status_code == 422
    r = cliente.post("/api/salas", json={"nome": "x" * 201, "local": "SAO_PAULO", "capacidade": 4})
    assert r.status_code == 422


def test_numero_negativo_recusado(cliente):
    sala = criar_sala(cliente)
    assert cliente.post("/api/reservas", json=dados_reserva(sala["id"], amanha(10), amanha(11), -3)).status_code == 422
    r = cliente.post("/api/salas", json={"nome": "Neg", "local": "SAO_PAULO", "capacidade": -1})
    assert r.status_code == 422


def test_json_malformado_sem_vazamento(cliente):
    r = cliente.post("/api/reservas", content=b'{"sala_id": 1, "titulo": ', headers={"Content-Type": "application/json"})
    assert 400 <= r.status_code < 500
    corpo = r.text
    for proibido in ("Traceback", "sqlite3", "SELECT", "INSERT", 'File "'):
        assert proibido not in corpo


def test_erro_de_negocio_sem_vazamento(cliente):
    r = cliente.post("/api/reservas/999/cancelar")
    assert r.status_code == 404
    assert set(r.json()) == {"erro", "mensagem"}


def test_sem_cors_liberado(cliente):
    r = cliente.get("/api/salas", headers={"Origin": "http://atacante.exemplo"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_app_sem_debug():
    from app.main import app

    assert app.debug is False
