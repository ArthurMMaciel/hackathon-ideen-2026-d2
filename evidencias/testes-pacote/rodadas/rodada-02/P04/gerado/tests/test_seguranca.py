"""Testes de ataque da revisão de segurança."""

import pytest

INJECAO = "'; DROP TABLE colaboradores; --"
XSS = "<script>alert(1)</script>"


def test_injecao_sql_em_campos_de_texto_gravada_literalmente(cliente):
    r = cliente.post("/api/colaboradores", json={"nome": INJECAO, "email": "inj@exemplo.com", "equipe": "DADOS"})
    assert r.status_code == 201
    assert r.json()["nome"] == INJECAO
    # E-mail com injeção: o formato recusa ou grava literal; nunca quebra o banco.
    r = cliente.post("/api/colaboradores", json={"nome": "Pessoa", "email": "x'--@exemplo.com", "equipe": "DADOS"})
    assert r.status_code in (201, 422)
    lista = cliente.get("/api/colaboradores")
    assert lista.status_code == 200
    assert any(c["nome"] == INJECAO for c in lista.json())
    assert cliente.get("/api/solicitacoes").status_code == 200


@pytest.mark.parametrize(
    "caminho,params",
    [
        ("/api/calendario", {"mes": INJECAO}),
        ("/api/calendario", {"mes": "2030-02' OR '1'='1"}),
    ],
)
def test_injecao_sql_em_parametros_de_consulta(cliente, caminho, params):
    assert cliente.get(caminho, params=params).status_code == 422
    assert len(cliente.get("/api/colaboradores").json()) == 9


def test_injecao_sql_em_campos_de_solicitacao(cliente):
    r = cliente.post("/api/solicitacoes", json={"colaborador_id": "1 OR 1=1", "inicio": INJECAO, "fim": "2030-02-25"})
    assert r.status_code == 422
    assert cliente.get("/api/solicitacoes").status_code == 200


def test_xss_devolvido_literal_pela_api(cliente):
    r = cliente.post("/api/colaboradores", json={"nome": XSS, "email": "xss@exemplo.com", "equipe": "PRODUTO"})
    assert r.status_code == 201
    cid = r.json()["id"]
    assert cliente.get(f"/api/colaboradores/{cid}").json()["nome"] == XSS


def test_tela_nao_usa_innerhtml_com_dados(cliente):
    html = cliente.get("/").text
    linhas = [l for l in html.splitlines() if "innerHTML" in l]
    assert all(l.strip().startswith("//") for l in linhas)


@pytest.mark.parametrize(
    "corpo",
    [
        {"nome": "a" * 201, "email": "longo@exemplo.com", "equipe": "DADOS"},
        {"nome": "Pessoa", "email": "a" * 250 + "@exemplo.com", "equipe": "DADOS"},
        {"nome": "Pessoa", "email": "neg@exemplo.com", "equipe": "DADOS", "saldo": -1},
    ],
)
def test_texto_acima_do_limite_e_numero_negativo_recusados(cliente, corpo):
    assert cliente.post("/api/colaboradores", json=corpo).status_code == 422


def test_id_negativo_recusado(cliente):
    assert cliente.get("/api/solicitacoes/-1").status_code == 422
    r = cliente.post("/api/solicitacoes", json={"colaborador_id": -1, "inicio": "2030-02-16", "fim": "2030-02-25"})
    assert r.status_code == 422


def test_json_malformado_sem_stack_trace(cliente):
    r = cliente.post("/api/solicitacoes", content=b'{"colaborador_id": 1,', headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    texto = r.text.lower()
    for termo in ("traceback", "sqlite", "select ", "insert ", 'file "'):
        assert termo not in texto


def test_erro_de_negocio_sem_detalhe_interno(cliente):
    r = cliente.get("/api/solicitacoes/999999")
    assert r.status_code == 404
    assert set(r.json()) == {"erro", "mensagem"}


def test_app_sem_debug_e_sem_cors_aberto(cliente):
    app = cliente.app
    assert app.debug is False
    assert not any("CORSMiddleware" in str(m.cls) for m in app.user_middleware)
    r = cliente.get("/api/saude", headers={"Origin": "http://malicioso.exemplo"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}
