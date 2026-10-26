"""Testes de ataque: injeção de SQL, XSS armazenado, limites de entrada e vazamento de erro."""

from tests.apoio import INICIO_PADRAO, criar_turma

INJECAO = "'; DROP TABLE turmas; --"
XSS = "<script>alert(1)</script>"


def corpo_turma(**extra):
    return {
        "titulo": "Turma segura",
        "inicio": INICIO_PADRAO.isoformat(),
        "duracao_minutos": 60,
        "modalidade": "ONLINE",
        "vagas": 5,
        **extra,
    }


def test_injecao_sql_nos_campos_de_texto_e_gravada_literalmente(cliente):
    r = cliente.post("/api/turmas", json=corpo_turma(titulo=INJECAO))
    assert r.status_code == 201
    assert r.json()["titulo"] == INJECAO
    turma_id = r.json()["id"]
    r = cliente.post(f"/api/turmas/{turma_id}/inscricoes", json={"nome": INJECAO, "email": "x@exemplo.test"})
    assert r.status_code == 201
    assert r.json()["nome"] == INJECAO
    # E-mail com aspas e ponto e vírgula é recusado pelo formato ou gravado literalmente; nunca executado.
    r = cliente.post(f"/api/turmas/{turma_id}/inscricoes", json={"nome": "A", "email": "a';DROP@x.test"})
    assert r.status_code in (201, 422)
    # Tabelas intactas.
    assert cliente.get("/api/turmas").status_code == 200
    assert len(cliente.get(f"/api/turmas/{turma_id}/inscricoes").json()) >= 1


def test_injecao_sql_em_parametros_de_caminho(cliente):
    for url in ["/api/turmas/1%20OR%201=1", "/api/turmas/1;DROP%20TABLE%20turmas", "/api/inscricoes/1'--/cancelar"]:
        r = cliente.get(url) if "cancelar" not in url else cliente.post(url)
        assert 400 <= r.status_code < 500, url
    assert cliente.get("/api/turmas").status_code == 200


def test_xss_e_devolvido_como_texto_literal(cliente):
    turma = criar_turma(cliente, titulo=XSS)
    assert turma["titulo"] == XSS
    r = cliente.post(f"/api/turmas/{turma['id']}/inscricoes", json={"nome": XSS, "email": "xss@exemplo.test"})
    assert r.json()["nome"] == XSS
    assert cliente.get(f"/api/turmas/{turma['id']}/inscricoes").json()[0]["nome"] == XSS


def test_tela_nao_usa_innerhtml_com_dados(cliente):
    html = cliente.get("/").text
    codigo = html.split("<script>", 1)[1]
    linhas_com_innerhtml = [linha for linha in codigo.splitlines() if "innerHTML" in linha and "//" not in linha]
    assert linhas_com_innerhtml == []


def test_texto_acima_do_limite_e_numero_negativo_recusados(cliente):
    assert cliente.post("/api/turmas", json=corpo_turma(titulo="x" * 201)).status_code == 422
    assert cliente.post("/api/turmas", json=corpo_turma(vagas=-5)).status_code == 422
    assert cliente.post("/api/turmas", json=corpo_turma(duracao_minutos=-1)).status_code == 422
    turma = criar_turma(cliente)
    url = f"/api/turmas/{turma['id']}/inscricoes"
    assert cliente.post(url, json={"nome": "x" * 10_000, "email": "a@x.test"}).status_code == 422
    assert cliente.post(url, json={"nome": "A", "email": "a" * 300 + "@x.test"}).status_code == 422


def test_json_malformado_nao_vaza_detalhes(cliente):
    r = cliente.post("/api/turmas", content=b"{titulo: ", headers={"Content-Type": "application/json"})
    assert 400 <= r.status_code < 500
    texto = r.text.lower()
    for vazamento in ["traceback", "sqlite", "select ", "insert ", 'file "']:
        assert vazamento not in texto


def test_erro_de_negocio_nao_vaza_sql(cliente):
    turma = criar_turma(cliente)
    url = f"/api/turmas/{turma['id']}/inscricoes"
    cliente.post(url, json={"nome": "A", "email": "a@x.test"})
    r = cliente.post(url, json={"nome": "A", "email": "a@x.test"})
    assert r.status_code == 409
    assert set(r.json()) == {"erro", "mensagem"}
    assert "sqlite" not in r.text.lower() and "unique" not in r.text.lower()


def test_sem_cors_liberado(cliente):
    r = cliente.get("/api/turmas", headers={"Origin": "http://site-malicioso.test"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_tela_ignora_cabecalho_range(cliente):
    # CVE-2025-62727: a tela não passa pelo FileResponse, então Range malicioso não tem efeito.
    faixas = ",".join(f"{i}-{i + 1}" for i in range(0, 2000, 2))
    r = cliente.get("/", headers={"Range": f"bytes={faixas}"})
    assert r.status_code == 200
    assert "<html" in r.text.lower()
