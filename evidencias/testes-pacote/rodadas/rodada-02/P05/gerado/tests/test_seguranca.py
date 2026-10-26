"""Testes de ataque: injeção de SQL, XSS armazenado, limites de entrada e vazamento de erro."""

import pytest

INJECAO = "'; DROP TABLE chamados; --"
SCRIPT = "<script>alert(1)</script>"


def _corpo(**extra):
    return {
        "titulo": "Chamado de teste",
        "descricao": "Descrição de teste.",
        "solicitante_nome": "Ana Souza",
        "solicitante_email": "ana.souza@empresa.example",
        "categoria": "ACESSO",
        "prioridade": "ALTA",
        **extra,
    }


@pytest.mark.parametrize("campo", ["titulo", "descricao", "solicitante_nome"])
def test_injecao_sql_em_campos_de_texto_gravada_literalmente(cliente, campo):
    resposta = cliente.post("/api/chamados", json=_corpo(**{campo: INJECAO}))
    assert resposta.status_code == 201
    id_ = resposta.json()["id"]
    assert cliente.get(f"/api/chamados/{id_}").json()[campo] == INJECAO
    assert cliente.get("/api/chamados").status_code == 200
    assert cliente.get("/api/fila").status_code == 200


def test_injecao_sql_em_responsavel_e_solucao(cliente):
    id_ = cliente.post("/api/chamados", json=_corpo()).json()["id"]
    assert cliente.post(f"/api/chamados/{id_}/assumir", json={"responsavel": INJECAO}).json()["responsavel"] == INJECAO
    assert cliente.post(f"/api/chamados/{id_}/resolver", json={"solucao": INJECAO}).json()["solucao"] == INJECAO
    assert len(cliente.get("/api/chamados").json()) >= 7


@pytest.mark.parametrize(
    "params",
    [
        {"data_inicial": INJECAO, "data_final": "2030-01-07"},
        {"data_inicial": "2030-01-07", "data_final": INJECAO},
    ],
)
def test_injecao_sql_em_parametros_de_consulta(cliente, params):
    assert cliente.get("/api/relatorio", params=params).status_code == 422
    assert cliente.get("/api/chamados").status_code == 200


def test_injecao_sql_no_caminho(cliente):
    assert cliente.get("/api/chamados/1 OR 1=1").status_code == 422
    assert cliente.post("/api/chamados/1;DROP TABLE chamados/fechar").status_code in (404, 422)
    assert len(cliente.get("/api/chamados").json()) == 6


def test_xss_texto_devolvido_literal(cliente):
    resposta = cliente.post("/api/chamados", json=_corpo(titulo=SCRIPT, descricao=SCRIPT))
    assert resposta.status_code == 201
    assert resposta.json()["titulo"] == SCRIPT
    assert any(item["titulo"] == SCRIPT for item in cliente.get("/api/fila").json())


def test_tela_nao_usa_innerhtml_com_dados(cliente):
    html = cliente.get("/").text
    codigo = [linha for linha in html.splitlines() if "innerHTML" in linha and not linha.strip().startswith("//")]
    assert codigo == []


@pytest.mark.parametrize(
    "campo, valor",
    [("titulo", "x" * 201), ("solicitante_nome", "x" * 201), ("descricao", "x" * 2001),
     ("solicitante_email", "a" * 250 + "@b.example"), ("prioridade", -1), ("categoria", 5)],
)
def test_entrada_acima_do_limite_ou_tipo_errado_recusada(cliente, campo, valor):
    assert cliente.post("/api/chamados", json=_corpo(**{campo: valor})).status_code == 422


def test_id_negativo_e_gigante_recusados(cliente):
    assert cliente.get("/api/chamados/-1").status_code == 422
    assert cliente.get("/api/chamados/99999999999999999999").status_code == 422


def test_json_malformado_sem_stack_trace(cliente):
    resposta = cliente.post(
        "/api/chamados", content=b'{"titulo": ', headers={"Content-Type": "application/json"}
    )
    assert resposta.status_code == 422
    texto = resposta.text.lower()
    for proibido in ("traceback", "sqlite", "select ", "insert ", 'file "'):
        assert proibido not in texto


def test_erro_de_negocio_sem_detalhe_interno(cliente):
    resposta = cliente.post("/api/chamados/999999/fechar")
    assert resposta.status_code == 404
    assert set(resposta.json()) == {"erro", "mensagem"}
    assert "sqlite" not in resposta.text.lower()


def test_sem_cors_liberado(cliente):
    resposta = cliente.get("/api/fila", headers={"Origin": "http://atacante.example"})
    assert "access-control-allow-origin" not in resposta.headers
