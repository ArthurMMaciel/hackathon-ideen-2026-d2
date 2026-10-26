"""Testes de ataque: injeção de SQL, XSS armazenado, limites de entrada e vazamento de erro."""

from datetime import timedelta

import pytest

from app.main import criar_app

INJECAO = "'; DROP TABLE emprestimos; --"
XSS = "<script>alert(1)</script>"


def _prevista(relogio, dias=1):
    return (relogio.agora.date() + timedelta(days=dias)).isoformat()


def _tabelas_intactas(cliente):
    assert cliente.get("/api/equipamentos").status_code == 200
    assert len(cliente.get("/api/equipamentos").json()) >= 8
    assert cliente.get("/api/emprestimos").status_code == 200


def test_injecao_sql_em_textos_gravada_literalmente(cliente, relogio):
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0900", "tipo": "NOTEBOOK", "descricao": INJECAO})
    assert r.status_code == 201
    assert r.json()["descricao"] == INJECAO
    r = cliente.post(
        "/api/emprestimos",
        json={"equipamento_id": r.json()["id"], "nome": INJECAO, "email": "x@exemplo.com", "data_prevista": _prevista(relogio)},
    )
    assert r.status_code == 201
    assert r.json()["nome"] == INJECAO
    _tabelas_intactas(cliente)


@pytest.mark.parametrize(
    "caminho,campo",
    [
        ("/api/equipamentos", "patrimonio"),
        ("/api/emprestimos", "email"),
    ],
)
def test_injecao_sql_em_campos_com_formato_recusada(cliente, relogio, caminho, campo):
    corpo = {
        "/api/equipamentos": {"patrimonio": "EQ-0901", "tipo": "NOTEBOOK", "descricao": "x"},
        "/api/emprestimos": {"equipamento_id": 1, "nome": "x", "email": "x@exemplo.com", "data_prevista": _prevista(relogio)},
    }[caminho]
    corpo[campo] = INJECAO
    assert cliente.post(caminho, json=corpo).status_code == 422
    _tabelas_intactas(cliente)


@pytest.mark.parametrize(
    "url,parametros",
    [
        ("/api/equipamentos/disponiveis", {"tipo": INJECAO}),
        ("/api/emprestimos", {"status": INJECAO}),
        ("/api/relatorios/emprestimos-por-tipo", {"mes": INJECAO}),
    ],
)
def test_injecao_sql_em_parametros_de_consulta(cliente, url, parametros):
    assert cliente.get(url, params=parametros).status_code == 422
    _tabelas_intactas(cliente)


def test_injecao_sql_no_caminho(cliente):
    assert cliente.get("/api/equipamentos/1 OR 1=1").status_code == 422
    assert cliente.post("/api/emprestimos/1;DROP/devolver", json={}).status_code in (404, 422)
    _tabelas_intactas(cliente)


def test_xss_devolvido_como_texto_literal(cliente, relogio):
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0902", "tipo": "HEADSET", "descricao": XSS})
    assert r.status_code == 201
    r = cliente.post(
        "/api/emprestimos",
        json={"equipamento_id": r.json()["id"], "nome": XSS, "email": "y@exemplo.com", "data_prevista": _prevista(relogio)},
    )
    assert r.status_code == 201
    assert r.json()["nome"] == XSS
    assert any(e["descricao"] == XSS for e in cliente.get("/api/equipamentos").json())


def test_tela_nao_usa_innerhtml_com_dados(cliente):
    html = cliente.get("/").text
    script = html.split("<script>", 1)[1]
    # a única ocorrência é o comentário que proíbe o uso
    assert script.count("innerHTML") == 1
    assert "nunca por innerHTML" in script


@pytest.mark.parametrize(
    "corpo",
    [
        {"nome": "a" * 201},
        {"email": "a" * 250 + "@x.com"},
        {"equipamento_id": -1},
        {"equipamento_id": 0},
        {"equipamento_id": 2_147_483_648},
    ],
)
def test_texto_acima_do_limite_e_numero_negativo_recusados(cliente, relogio, corpo):
    base = {"equipamento_id": 1, "nome": "Ana", "email": "a@exemplo.com", "data_prevista": _prevista(relogio)}
    assert cliente.post("/api/emprestimos", json={**base, **corpo}).status_code == 422


def test_descricao_acima_do_limite_recusada(cliente):
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0903", "tipo": "NOTEBOOK", "descricao": "a" * 201})
    assert r.status_code == 422


def test_json_malformado_sem_stack_trace(cliente):
    r = cliente.post("/api/emprestimos", content=b'{"equipamento_id": 1,', headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    texto = r.text.lower()
    for proibido in ("traceback", "sqlite", "select ", "insert ", 'file "'):
        assert proibido not in texto


def test_erro_de_negocio_sem_detalhe_interno(cliente):
    r = cliente.post("/api/emprestimos/999999/devolver", json={})
    assert r.status_code == 404
    assert set(r.json()) == {"erro", "mensagem"}


def test_app_sem_debug_e_sem_cors_aberto(tmp_path):
    app = criar_app(str(tmp_path / "s.db"))
    assert app.debug is False
    assert not any("CORSMiddleware" in str(m.cls) for m in app.user_middleware)
