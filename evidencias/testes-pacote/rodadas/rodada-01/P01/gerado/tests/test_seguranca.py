"""Testes de ataque: injeção de SQL, XSS, validação de entrada e vazamento de informação."""

INJECAO = "'; DROP TABLE equipamentos; --"
SCRIPT = "<script>alert(1)</script>"


def _emprestimo(**extra):
    return {"equipamento_id": 1, "nome": "Ana Exemplo", "email": "ana@exemplo.test", "data_prevista": "2030-01-08", **extra}


def test_injecao_sql_em_campos_de_texto_fica_literal(cliente):
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0200", "tipo": "NOTEBOOK", "descricao": INJECAO})
    assert r.status_code == 201
    assert r.json()["descricao"] == INJECAO

    r = cliente.post("/api/emprestimos", json=_emprestimo(nome=INJECAO))
    assert r.status_code == 201
    assert r.json()["nome"] == INJECAO

    # E-mail com aspas e ponto e vírgula não passa no formato; recusa com 422.
    assert cliente.post("/api/emprestimos", json=_emprestimo(equipamento_id=2, email=INJECAO)).status_code == 422
    # Patrimônio com injeção: recusado pela regra de formato.
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0001' OR '1'='1", "tipo": "NOTEBOOK", "descricao": "x"})
    assert r.status_code == 422

    # Tabelas intactas: listagens continuam funcionando.
    assert len(cliente.get("/api/equipamentos").json()) == 9
    assert len(cliente.get("/api/emprestimos").json()) == 1


def test_injecao_sql_em_parametros_de_consulta(cliente):
    assert cliente.get("/api/equipamentos", params={"tipo": INJECAO}).status_code == 422
    assert cliente.get("/api/equipamentos", params={"situacao": INJECAO}).status_code == 422
    assert cliente.get("/api/emprestimos", params={"status": INJECAO}).status_code == 422
    assert cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": INJECAO}).status_code == 422
    assert cliente.get("/api/equipamentos/1 OR 1=1").status_code == 422
    assert len(cliente.get("/api/equipamentos").json()) == 8


def test_xss_texto_devolvido_literal(cliente):
    r = cliente.post("/api/emprestimos", json=_emprestimo(nome=SCRIPT))
    assert r.status_code == 201
    assert r.json()["nome"] == SCRIPT
    abertos = cliente.get("/api/emprestimos", params={"status": "ABERTO"}).json()
    assert abertos[0]["nome"] == SCRIPT


def test_tela_nao_usa_innerhtml_com_dados(cliente):
    html = cliente.get("/").text
    codigo = html.replace("nunca innerHTML", "")
    assert "innerHTML" not in codigo
    assert "outerHTML" not in codigo
    assert "document.write" not in codigo


def test_texto_acima_do_limite_retorna_422(cliente):
    longo = "a" * 201
    assert cliente.post("/api/emprestimos", json=_emprestimo(nome=longo)).status_code == 422
    assert cliente.post("/api/emprestimos", json=_emprestimo(email="a" * 195 + "@x.com")).status_code == 422
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0300", "tipo": "HEADSET", "descricao": longo})
    assert r.status_code == 422
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-" + "0" * 30, "tipo": "HEADSET", "descricao": "x"})
    assert r.status_code == 422


def test_numero_negativo_retorna_422(cliente):
    assert cliente.post("/api/emprestimos", json=_emprestimo(equipamento_id=-1)).status_code == 422
    assert cliente.post("/api/emprestimos", json=_emprestimo(equipamento_id=0)).status_code == 422
    assert cliente.get("/api/equipamentos/-5").status_code == 422
    assert cliente.post("/api/emprestimos/-5/devolver").status_code == 422


def test_json_malformado_sem_stack_trace(cliente):
    for caminho in ["/api/emprestimos", "/api/equipamentos", "/api/emprestimos/1/devolver"]:
        r = cliente.post(caminho, content="{nao e json", headers={"Content-Type": "application/json"})
        assert 400 <= r.status_code < 500, caminho
        texto = r.text
        assert "Traceback" not in texto
        assert "sqlite" not in texto.lower()
        assert "File \"" not in texto


def test_sem_debug_e_sem_cors_aberto(cliente):
    assert cliente.app.debug is False
    r = cliente.get("/api/saude", headers={"Origin": "http://atacante.test"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_tela_ignora_cabecalho_range(cliente):
    # Mitigação da CVE-2025-62727 (starlette 0.41.3): a tela não passa por FileResponse.
    faixas = ",".join(f"{i}-{i + 1}" for i in range(0, 2000, 2))
    r = cliente.get("/", headers={"Range": f"bytes={faixas}"})
    assert r.status_code == 200
    assert "<html" in r.text.lower()
    assert "content-range" not in {k.lower() for k in r.headers}
