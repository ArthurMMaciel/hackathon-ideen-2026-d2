"""Testes de ataque: injeção de SQL, XSS, validação de entrada e vazamento de erro."""

import pytest

from tests.apoio import criar_turma, inscrever

INJECAO = "'; DROP TABLE turmas; --"
XSS = "<script>alert(1)</script>"


def test_injecao_sql_em_titulo_gravada_literalmente(cliente):
    turma = criar_turma(cliente, titulo=INJECAO)
    assert turma["titulo"] == INJECAO
    assert cliente.get(f"/api/turmas/{turma['id']}").json()["titulo"] == INJECAO
    r = cliente.get("/api/turmas")
    assert r.status_code == 200
    assert len(r.json()) == 4  # 3 iniciais + a criada: tabela intacta


def test_injecao_sql_em_nome_e_email(cliente):
    turma = criar_turma(cliente)
    r = inscrever(cliente, turma["id"], nome=INJECAO)
    assert r.status_code == 201
    assert r.json()["nome"] == INJECAO
    r = inscrever(cliente, turma["id"], email="x'--@exemplo.test")
    assert r.status_code == 201
    assert r.json()["email"] == "x'--@exemplo.test"
    r = inscrever(cliente, turma["id"], email="'; DROP TABLE inscricoes; --")
    assert r.status_code == 422
    assert cliente.get(f"/api/turmas/{turma['id']}/inscricoes").status_code == 200


@pytest.mark.parametrize("caminho", [
    "/api/turmas/1%20OR%201=1",
    "/api/turmas/1;DROP%20TABLE%20turmas",
    "/api/turmas/1'--/inscricoes",
])
def test_injecao_sql_em_parametros_de_caminho(cliente, caminho):
    assert cliente.get(caminho).status_code in (404, 422)
    assert cliente.get("/api/turmas").status_code == 200


def test_injecao_sql_em_parametro_de_consulta_ignorado(cliente):
    r = cliente.get("/api/turmas", params={"id": INJECAO})
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_xss_devolvido_literal(cliente):
    turma = criar_turma(cliente, titulo=XSS)
    assert turma["titulo"] == XSS
    r = inscrever(cliente, turma["id"], nome=XSS)
    assert r.json()["nome"] == XSS


def test_tela_nao_usa_innerhtml_com_dados(cliente):
    html = cliente.get("/").text
    # Única ocorrência é o comentário que proíbe o uso.
    assert html.count("innerHTML") == 1
    assert "nunca por innerHTML" in html


@pytest.mark.parametrize("campo, valor", [("titulo", "x" * 201), ("vagas", -1), ("duracao_minutos", -1)])
def test_texto_acima_do_limite_e_negativo(cliente, campo, valor):
    corpo = {"titulo": "T", "inicio": "2030-01-10T09:00:00-03:00", "duracao_minutos": 60,
             "modalidade": "ONLINE", "vagas": 5, campo: valor}
    assert cliente.post("/api/turmas", json=corpo).status_code == 422


def test_nome_acima_do_limite(cliente):
    turma = criar_turma(cliente)
    assert inscrever(cliente, turma["id"], nome="x" * 201).status_code == 422


def test_json_malformado_sem_vazamento(cliente):
    r = cliente.post("/api/inscricoes", content=b'{"turma_id": 1, "nome": ', headers={"content-type": "application/json"})
    assert 400 <= r.status_code < 500
    texto = r.text.lower()
    for proibido in ("traceback", "sqlite", "select ", "insert ", 'file "'):
        assert proibido not in texto


def test_erro_de_negocio_sem_vazamento(cliente):
    r = cliente.get("/api/turmas/123456")
    assert r.status_code == 404
    assert set(r.json()) == {"erro", "mensagem"}
    assert "sqlite" not in r.text.lower()


def test_app_sem_debug():
    from app.main import app
    assert app.debug is False
