from tests.conftest import iso


def test_injecao_textos_e_consulta(cliente, relogio):
    ataque = "'; DROP TABLE salas; --"
    sala = cliente.post("/api/salas", json={"nome": ataque, "local": "COWORKING",
                                             "capacidade": 2, "recursos": []})
    assert sala.status_code == 201 and sala.json()["nome"] == ataque
    reserva = cliente.post("/api/reservas", json={
        "sala_id": sala.json()["id"], "responsavel_nome": ataque,
        "responsavel_email": "x@example.test", "titulo": ataque,
        "participantes": 1, "inicio": iso(relogio.agora, 10),
        "fim": iso(relogio.agora, 11)})
    assert reserva.status_code == 201 and reserva.json()["titulo"] == ataque
    assert cliente.get("/api/salas/livres", params={"inicio": iso(relogio.agora, 10),
                      "fim": iso(relogio.agora, 11), "local": ataque}).status_code == 422
    assert cliente.get("/api/salas").status_code == 200


def test_xss_literal(cliente):
    script = "<script>alert(1)</script>"
    r = cliente.post("/api/salas", json={"nome": script, "local": "SAO_PAULO",
                                         "capacidade": 2, "recursos": []})
    assert r.status_code == 201 and r.json()["nome"] == script
    tela = cliente.get("/").text
    assert "innerHTML" not in tela


def test_limites_e_json_malformado(cliente):
    for nome, capacidade in [("x" * 201, 1), ("Teste", -1), ("   ", 1)]:
        r = cliente.post("/api/salas", json={"nome": nome, "local": "SAO_PAULO",
                                             "capacidade": capacidade, "recursos": []})
        assert r.status_code == 422
    r = cliente.post("/api/salas", content="{ inválido", headers={"Content-Type": "application/json"})
    assert r.status_code == 422 and "Traceback" not in r.text and "SELECT" not in r.text


def test_extremos_rotas(cliente, relogio):
    for id_ruim in ["99999999999999999999", "１２"]:
        assert cliente.get(f"/api/reservas/{id_ruim}").status_code == 422
        assert cliente.post(f"/api/reservas/{id_ruim}/cancelar").status_code == 422
    for dia in ["9999-01-01", "0001-01-01", "２０３０-01-07"]:
        assert cliente.get("/api/relatorios/ocupacao", params={"dia": dia}).status_code == 422
        assert cliente.get("/api/reservas", params={"dia": dia}).status_code == 422
    assert cliente.get("/api/reservas/99999").status_code == 404
    assert cliente.post("/api/reservas", json={"sala_id": 1}).status_code == 422
    assert cliente.get("/api/salas/livres", params={"inicio": iso(relogio.agora, 11),
        "fim": iso(relogio.agora, 10), "capacidade_minima": -1}).status_code == 422
