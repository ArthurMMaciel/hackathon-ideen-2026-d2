"""Testes de ataque da revisão de segurança."""

from tests.test_despesas import despesa

INJECAO = "'; DROP TABLE despesas; --"
SCRIPT = "<script>alert(1)</script>"
CAMPOS_TEXTO = ("colaborador_nome", "descricao", "numero_comprovante")


def test_injecao_sql_em_campos_de_texto_grava_literal(cliente):
    for i, campo in enumerate(CAMPOS_TEXTO):
        corpo = despesa(numero_comprovante=f"SEG-{i}")
        corpo[campo] = INJECAO
        r = cliente.post("/api/despesas", json=corpo)
        assert r.status_code == 201, r.text
        assert r.json()[campo] == INJECAO
    # E-mail com aspas: recusado pelo formato ou gravado literal; tabela intacta.
    r = cliente.post("/api/despesas", json=despesa(colaborador_email="x'--@empresa.example", numero_comprovante="SEG-E"))
    assert r.status_code in (201, 422)
    assert cliente.get("/api/despesas").status_code == 200
    assert len(cliente.get("/api/despesas").json()) >= 5 + 3


def test_injecao_sql_em_parametros_de_consulta(cliente):
    r = cliente.get("/api/despesas", params={"email": "' OR '1'='1"})
    assert r.status_code == 200
    assert r.json() == []
    assert cliente.get("/api/despesas", params={"situacao": INJECAO}).status_code == 422
    assert cliente.get("/api/relatorios/mensal", params={"mes": INJECAO}).status_code == 422
    r = cliente.post("/api/despesas/1/recusar", json={"motivo": INJECAO})
    assert r.status_code == 200
    assert r.json()["motivo_recusa"] == INJECAO
    assert len(cliente.get("/api/despesas").json()) == 5


def test_xss_texto_devolvido_literal(cliente):
    r = cliente.post("/api/despesas", json=despesa(descricao=SCRIPT, colaborador_nome=SCRIPT))
    assert r.status_code == 201
    assert r.json()["descricao"] == SCRIPT
    lida = cliente.get(f"/api/despesas/{r.json()['id']}").json()
    assert lida["colaborador_nome"] == SCRIPT


def test_texto_acima_do_limite_e_numero_negativo_422(cliente):
    for campo in CAMPOS_TEXTO + ("colaborador_email",):
        corpo = despesa()
        corpo[campo] = "a" * 201 if campo != "colaborador_email" else "a" * 190 + "@empresa.example"
        assert cliente.post("/api/despesas", json=corpo).status_code == 422, campo
    assert cliente.post("/api/despesas", json=despesa(valor=-50)).status_code == 422
    assert cliente.post("/api/despesas", json=despesa(valor=10**12)).status_code == 422
    assert cliente.post("/api/despesas/1/recusar", json={"motivo": "m" * 501}).status_code == 422
    assert cliente.get("/api/despesas", params={"email": "a" * 201}).status_code == 422
    assert cliente.post("/api/despesas", json={**despesa(), "situacao": "PAGA"}).status_code == 422


def test_json_malformado_sem_vazamento(cliente):
    r = cliente.post("/api/despesas", content=b'{"colaborador_nome": ', headers={"Content-Type": "application/json"})
    assert 400 <= r.status_code < 500
    texto = r.text.lower()
    for indicio in ("traceback", "sqlite", "select ", "insert ", 'file "'):
        assert indicio not in texto


def test_aplicacao_sem_debug_e_sem_cors_aberto(cliente):
    assert cliente.app.debug is False
    r = cliente.get("/api/despesas", headers={"Origin": "http://atacante.example"})
    assert "access-control-allow-origin" not in r.headers


def test_tela_ignora_cabecalho_range(cliente):
    # Mitigação de CVE-2025-62727 (Range no FileResponse do starlette 0.41.3).
    r = cliente.get("/", headers={"Range": "bytes=" + ",".join(f"{i}-{i}" for i in range(0, 4000, 2))})
    assert r.status_code == 200
    assert "accept-ranges" not in r.headers
    assert "<html" in r.text.lower()
