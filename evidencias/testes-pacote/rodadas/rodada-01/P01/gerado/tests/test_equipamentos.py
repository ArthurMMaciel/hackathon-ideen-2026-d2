"""Testes de cadastro e consulta de equipamentos (RF-01, RF-02, RF-05, RF-12, RN-01)."""


def test_rf_12_carga_inicial(cliente):
    r = cliente.get("/api/equipamentos")
    assert r.status_code == 200
    equipamentos = r.json()
    assert len(equipamentos) == 8
    por_tipo = {}
    for e in equipamentos:
        por_tipo[e["tipo"]] = por_tipo.get(e["tipo"], 0) + 1
    assert por_tipo == {"NOTEBOOK": 3, "PROJETOR": 2, "HEADSET": 3}
    manutencao = [e for e in equipamentos if e["situacao"] == "MANUTENCAO"]
    assert [(e["patrimonio"], e["tipo"]) for e in manutencao] == [("EQ-0008", "HEADSET")]
    assert [e["patrimonio"] for e in equipamentos] == sorted(e["patrimonio"] for e in equipamentos)


def test_rf_12_carga_inicial_idempotente(tmp_path):
    from fastapi.testclient import TestClient

    from app.main import criar_app

    caminho = str(tmp_path / "idem.db")
    for _ in range(2):
        with TestClient(criar_app(caminho)) as c:
            assert len(c.get("/api/equipamentos").json()) == 8


def test_rf_01_cadastrar_equipamento(cliente):
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0100", "tipo": "HEADSET", "descricao": "Headset extra"})
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["patrimonio"] == "EQ-0100"
    assert corpo["situacao"] == "DISPONIVEL"
    assert cliente.get(f"/api/equipamentos/{corpo['id']}").json() == corpo


def test_rn_01_patrimonio_formato_invalido(cliente):
    for patrimonio in ["EQ-123", "EQ-12345", "eq-0001", "XX-0001", "EQ0001", "EQ-12a4"]:
        r = cliente.post("/api/equipamentos", json={"patrimonio": patrimonio, "tipo": "NOTEBOOK", "descricao": "Teste"})
        assert r.status_code == 422, patrimonio
        assert r.json()["erro"] == "PATRIMONIO_INVALIDO"


def test_rn_01_patrimonio_duplicado(cliente):
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0001", "tipo": "NOTEBOOK", "descricao": "Outro"})
    assert r.status_code == 409
    assert r.json()["erro"] == "PATRIMONIO_DUPLICADO"


def test_rf_01_validacao_entrada(cliente):
    casos = [
        {"patrimonio": "EQ-0101", "tipo": "TABLET", "descricao": "Tipo fora do enum"},
        {"patrimonio": "EQ-0101", "tipo": "NOTEBOOK", "descricao": ""},
        {"patrimonio": "EQ-0101", "tipo": "NOTEBOOK"},
    ]
    for corpo in casos:
        assert cliente.post("/api/equipamentos", json=corpo).status_code == 422, corpo


def test_rf_02_consultar_equipamento_inexistente(cliente):
    r = cliente.get("/api/equipamentos/999")
    assert r.status_code == 404
    assert r.json()["erro"] == "EQUIPAMENTO_NAO_ENCONTRADO"


def test_rf_05_disponiveis_filtro_tipo(cliente):
    cliente.post(
        "/api/emprestimos",
        json={"equipamento_id": 1, "nome": "Ana Exemplo", "email": "ana@exemplo.test", "data_prevista": "2030-01-08"},
    )
    r = cliente.get("/api/equipamentos", params={"situacao": "DISPONIVEL", "tipo": "NOTEBOOK"})
    assert r.status_code == 200
    assert [e["patrimonio"] for e in r.json()] == ["EQ-0002", "EQ-0003"]
    disponiveis = cliente.get("/api/equipamentos", params={"situacao": "DISPONIVEL"}).json()
    assert len(disponiveis) == 6
    headsets = cliente.get("/api/equipamentos", params={"tipo": "HEADSET"}).json()
    assert len(headsets) == 3
    assert cliente.get("/api/equipamentos", params={"tipo": "TABLET"}).status_code == 422
