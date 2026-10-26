"""Testes de ataque da revisão de segurança."""

import pytest

INJECAO = "'; DROP TABLE chamados; --"
XSS = "<script>alert(1)</script>"
VALIDO = {
    "titulo": "Teste", "descricao": "Desc", "solicitante_nome": "Ana",
    "solicitante_email": "ana@example.com", "categoria": "ACESSO", "prioridade": "ALTA",
}


@pytest.mark.parametrize("campo", ["titulo", "descricao", "solicitante_nome"])
def test_injecao_sql_em_campos_de_texto(cliente, campo):
    r = cliente.post("/api/chamados", json={**VALIDO, campo: INJECAO})
    assert r.status_code == 201
    assert r.json()[campo] == INJECAO
    assert cliente.get("/api/chamados").status_code == 200
    assert any(c[campo] == INJECAO for c in cliente.get("/api/chamados").json())


def test_injecao_sql_em_email_categoria_e_transicoes(cliente):
    assert cliente.post("/api/chamados", json={**VALIDO, "solicitante_email": INJECAO}).status_code == 422
    assert cliente.post("/api/chamados", json={**VALIDO, "categoria": INJECAO}).status_code == 422
    cid = cliente.post("/api/chamados", json=VALIDO).json()["id"]
    r = cliente.post(f"/api/chamados/{cid}/assumir", json={"responsavel": INJECAO})
    assert r.status_code == 200 and r.json()["responsavel"] == INJECAO
    r = cliente.post(f"/api/chamados/{cid}/resolver", json={"solucao": INJECAO})
    assert r.status_code == 200 and r.json()["solucao"] == INJECAO
    assert cliente.get("/api/chamados/fila").status_code == 200


def test_injecao_sql_em_parametros_de_consulta(cliente):
    r = cliente.get("/api/relatorios/prazo", params={"data_inicial": INJECAO, "data_final": "2030-01-07"})
    assert r.status_code == 422
    assert cliente.get("/api/chamados/1 OR 1=1").status_code == 422
    assert len(cliente.get("/api/chamados").json()) == 6


def test_xss_gravado_literal(cliente):
    r = cliente.post("/api/chamados", json={**VALIDO, "titulo": XSS})
    assert r.status_code == 201
    assert r.json()["titulo"] == XSS
    assert cliente.get(f"/api/chamados/{r.json()['id']}").json()["titulo"] == XSS


def test_tela_nao_usa_innerhtml(cliente):
    assert "innerHTML =" not in cliente.get("/").text
    assert ".innerHTML" not in cliente.get("/").text.replace("nunca innerHTML", "")


@pytest.mark.parametrize("campo,limite", [
    ("titulo", 200), ("descricao", 2000), ("solicitante_nome", 100), ("solicitante_email", 200),
])
def test_texto_acima_do_limite_422(cliente, campo, limite):
    valor = "a" * (limite + 1)
    if campo == "solicitante_email":
        valor = "a" * (limite - 11) + "@example.com"
    assert cliente.post("/api/chamados", json={**VALIDO, campo: valor}).status_code == 422


def test_textos_das_transicoes_acima_do_limite_422(cliente):
    cid = cliente.post("/api/chamados", json=VALIDO).json()["id"]
    assert cliente.post(f"/api/chamados/{cid}/assumir", json={"responsavel": "a" * 101}).status_code == 422
    cliente.post(f"/api/chamados/{cid}/assumir", json={"responsavel": "Carla"})
    assert cliente.post(f"/api/chamados/{cid}/resolver", json={"solucao": "a" * 2001}).status_code == 422


def test_numero_negativo_422(cliente):
    assert cliente.get("/api/chamados/-1").status_code == 422
    assert cliente.post("/api/chamados/-5/reabrir").status_code == 422


def test_json_malformado_sem_stack_trace(cliente):
    r = cliente.post("/api/chamados", content=b"{titulo: sem aspas", headers={"Content-Type": "application/json"})
    assert 400 <= r.status_code < 500
    texto = r.text.lower()
    for proibido in ("traceback", "sqlite", "select ", "insert ", 'file "'):
        assert proibido not in texto


def test_erro_de_negocio_sem_detalhe_interno(cliente):
    r = cliente.get("/api/chamados/999")
    assert r.status_code == 404
    assert set(r.json()) == {"erro", "mensagem"}


def test_sem_cors_liberado(cliente):
    r = cliente.get("/api/saude", headers={"Origin": "http://malicioso.example"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_tela_ignora_cabecalho_range(cliente):
    # Mitigação de CVE-2025-62727 (Range no FileResponse do starlette 0.41.3).
    r = cliente.get("/", headers={"Range": "bytes=0-0," + ",".join(f"{i}-{i}" for i in range(1, 2000))})
    assert r.status_code == 200
    assert "<html" in r.text.lower()
    assert "content-range" not in {k.lower() for k in r.headers}
