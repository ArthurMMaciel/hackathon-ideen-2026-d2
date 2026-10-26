"""Testes de ataque: injeção de SQL, XSS, limites de entrada e vazamento de erro."""

import pytest

INJECAO = "'; DROP TABLE despesas; --"
XSS = "<script>alert(1)</script>"


def despesa(**campos) -> dict:
    base = {
        "colaborador_nome": "Segurança Teste",
        "colaborador_email": "seguranca@empresa.example",
        "data": "2030-01-05",
        "categoria": "OUTROS",
        "valor_centavos": 1000,
        "descricao": "Teste de segurança",
        "comprovante": "SEG-1",
    }
    base.update(campos)
    return base


@pytest.mark.parametrize("campo", ["colaborador_nome", "descricao", "comprovante"])
def test_injecao_sql_em_texto_gravada_literalmente(cliente, campo):
    r = cliente.post("/api/despesas", json=despesa(**{campo: INJECAO}))
    assert r.status_code == 201
    assert r.json()[campo] == INJECAO
    lista = cliente.get("/api/despesas")
    assert lista.status_code == 200
    assert any(d[campo] == INJECAO for d in lista.json())


def test_injecao_sql_no_motivo_da_recusa(cliente):
    d = cliente.post("/api/despesas", json=despesa()).json()
    r = cliente.post(f"/api/despesas/{d['id']}/recusar", json={"motivo": INJECAO})
    assert r.status_code == 200
    assert r.json()["motivo_recusa"] == INJECAO
    assert cliente.get("/api/despesas").status_code == 200


@pytest.mark.parametrize(
    "params",
    [
        {"email": "x@y.com' OR '1'='1"},
        {"situacao": "PENDENTE' OR '1'='1"},
        {"email": INJECAO},
    ],
)
def test_injecao_sql_nos_filtros(cliente, params):
    r = cliente.get("/api/despesas", params=params)
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        assert r.json() == []
    assert len(cliente.get("/api/despesas").json()) == 5  # tabela intacta com a carga inicial


def test_injecao_sql_no_mes_do_resumo(cliente):
    assert cliente.get("/api/relatorios/mensal", params={"mes": "2030-01' OR 1=1 --"}).status_code == 422
    assert cliente.get("/api/relatorios/mensal", params={"mes": "2030-01"}).status_code == 200


def test_xss_devolvido_literal(cliente):
    r = cliente.post("/api/despesas", json=despesa(descricao=XSS, colaborador_nome=XSS))
    assert r.status_code == 201
    assert r.json()["descricao"] == XSS
    assert any(d["descricao"] == XSS for d in cliente.get("/api/despesas").json())


def test_tela_nao_usa_innerhtml_com_dados(cliente):
    html = cliente.get("/").text
    codigo = [linha for linha in html.splitlines() if "innerHTML" in linha and not linha.strip().startswith("//")]
    assert codigo == []


@pytest.mark.parametrize("campo", ["colaborador_nome", "descricao", "comprovante"])
def test_texto_acima_do_limite_422(cliente, campo):
    assert cliente.post("/api/despesas", json=despesa(**{campo: "a" * 201})).status_code == 422


def test_motivo_acima_do_limite_422(cliente):
    d = cliente.post("/api/despesas", json=despesa()).json()
    r = cliente.post(f"/api/despesas/{d['id']}/recusar", json={"motivo": "a" * 201})
    assert r.status_code == 422


def test_valor_negativo_422(cliente):
    assert cliente.post("/api/despesas", json=despesa(valor_centavos=-100)).status_code == 422


def test_json_malformado_sem_vazamento(cliente):
    r = cliente.post("/api/despesas", content=b'{"colaborador_nome": ', headers={"Content-Type": "application/json"})
    assert 400 <= r.status_code < 500
    texto = r.text.lower()
    for proibido in ("traceback", "sqlite", "select ", "insert ", 'file "'):
        assert proibido not in texto


def test_erro_de_negocio_sem_vazamento(cliente):
    r = cliente.post("/api/despesas/999999/aprovar")
    assert r.status_code == 404
    assert set(r.json()) == {"erro", "mensagem"}
    assert "traceback" not in r.text.lower()


def test_app_sem_debug(cliente):
    assert cliente.app.debug is False


# ---------- Evolução 1: edição (PUT /api/despesas/{id}) ----------

def test_edicao_injecao_sql_na_descricao_gravada_literalmente(cliente):
    d = cliente.post("/api/despesas", json=despesa(comprovante="SEG-ED-1")).json()
    r = cliente.put(f"/api/despesas/{d['id']}", json={"categoria": "OUTROS", "valor_centavos": 1000, "descricao": INJECAO})
    assert r.status_code == 200
    assert r.json()["descricao"] == INJECAO
    assert cliente.get("/api/despesas").status_code == 200


@pytest.mark.parametrize("corpo", [
    {"categoria": "OUTROS", "valor_centavos": 10**12, "descricao": "x"},
    {"categoria": "OUTROS", "valor_centavos": -1, "descricao": "x"},
    {"categoria": "OUTROS", "valor_centavos": 1000, "descricao": "a" * 201},
    {"categoria": "'; DROP TABLE despesas; --", "valor_centavos": 1000, "descricao": "x"},
])
def test_edicao_valores_extremos_422(cliente, corpo):
    d = cliente.post("/api/despesas", json=despesa(comprovante="SEG-ED-2")).json()
    assert cliente.put(f"/api/despesas/{d['id']}", json=corpo).status_code == 422


def test_edicao_id_gigante_422(cliente):
    r = cliente.put("/api/despesas/99999999999999999999", json={"categoria": "OUTROS", "valor_centavos": 1, "descricao": "x"})
    assert r.status_code == 422
