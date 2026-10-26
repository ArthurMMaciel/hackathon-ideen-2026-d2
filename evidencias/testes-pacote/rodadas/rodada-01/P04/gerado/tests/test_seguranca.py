"""Testes de ataque: injeção de SQL, XSS, limites de entrada e vazamento de erro."""

import pytest
from fastapi.testclient import TestClient

from app.main import criar_app

INJECAO = "'; DROP TABLE colaboradores; --"
XSS = "<script>alert(1)</script>"


def test_injecao_sql_em_campos_de_texto_grava_literal(cliente):
    r = cliente.post("/api/colaboradores", json={"nome": INJECAO, "email": "inj@exemplo.test", "equipe": "DADOS"})
    assert r.status_code == 201
    assert r.json()["nome"] == INJECAO
    lista = cliente.get("/api/colaboradores")
    assert lista.status_code == 200 and len(lista.json()) == 10
    # e-mail com aspas é recusado pelo formato, sem tocar no banco
    r = cliente.post("/api/colaboradores", json={"nome": "X", "email": INJECAO, "equipe": "DADOS"})
    assert r.status_code == 422
    assert cliente.get("/api/solicitacoes").status_code == 200


@pytest.mark.parametrize("parametros", [
    {"situacao": INJECAO},
    {"colaborador_id": INJECAO},
    {"colaborador_id": "1 OR 1=1"},
])
def test_injecao_sql_em_parametros_de_consulta(cliente, parametros):
    r = cliente.get("/api/solicitacoes", params=parametros)
    assert r.status_code == 422
    assert len(cliente.get("/api/colaboradores").json()) == 9


def test_injecao_sql_no_mes_e_nas_datas(cliente):
    r = cliente.get("/api/calendario", params={"mes": "2030-03' OR '1'='1"})
    assert r.status_code == 422
    r = cliente.post("/api/solicitacoes", json={"colaborador_id": 1, "inicio": INJECAO, "fim": "2030-03-10"})
    assert r.status_code == 422
    assert len(cliente.get("/api/colaboradores").json()) == 9


def test_xss_texto_volta_literal(cliente):
    r = cliente.post("/api/colaboradores", json={"nome": XSS, "email": "xss@exemplo.test", "equipe": "SUPORTE"})
    assert r.status_code == 201
    assert r.json()["nome"] == XSS
    assert any(c["nome"] == XSS for c in cliente.get("/api/colaboradores").json())


def test_tela_nao_usa_innerhtml(cliente):
    html = cliente.get("/").text
    assert "innerHTML" not in html.replace("nunca innerHTML", "")


@pytest.mark.parametrize("corpo", [
    {"nome": "x" * 121, "email": "a@exemplo.test", "equipe": "DADOS"},
    {"nome": "X", "email": "a" * 195 + "@ex.test", "equipe": "DADOS"},
    {"nome": "X", "email": "a@exemplo.test", "equipe": "DADOS", "saldo": -5},
    {"nome": "X", "email": "a@exemplo.test", "equipe": "DADOS", "saldo": 10**12},
    {"nome": "   ", "email": "a@exemplo.test", "equipe": "DADOS"},
])
def test_limites_de_entrada_colaborador(cliente, corpo):
    assert cliente.post("/api/colaboradores", json=corpo).status_code == 422


def test_numero_negativo_na_solicitacao(cliente):
    r = cliente.post("/api/solicitacoes", json={"colaborador_id": -1, "inicio": "2030-03-01", "fim": "2030-03-10"})
    assert r.status_code == 422


def test_json_malformado_sem_stack_trace(tmp_path):
    app = criar_app(str(tmp_path / "s.db"))
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.post("/api/solicitacoes", content=b"{nao e json", headers={"Content-Type": "application/json"})
        assert r.status_code == 422
        texto = r.text
        assert "Traceback" not in texto and "sqlite" not in texto.lower() and "SELECT" not in texto


def test_app_sem_debug(cliente):
    assert cliente.app.debug is False


def test_sem_cors_liberado(cliente):
    r = cliente.get("/api/saude", headers={"Origin": "http://malicioso.test"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_tela_ignora_cabecalho_range(cliente):
    # Mitigação de CVE-2025-62727: a tela não passa pelo parser de Range do FileResponse.
    r = cliente.get("/", headers={"Range": "bytes=" + ",".join(f"{i}-{i + 1}" for i in range(0, 4000, 2))})
    assert r.status_code == 200
    assert "<html" in r.text.lower()
