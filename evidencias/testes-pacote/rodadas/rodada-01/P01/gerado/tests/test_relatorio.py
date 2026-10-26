"""Relatório mensal de empréstimos por tipo (RF-07, RN-12)."""

from datetime import datetime

from app.relogio import FUSO


def emprestar(cliente, equipamento_id, data_prevista, email):
    r = cliente.post(
        "/api/emprestimos",
        json={"equipamento_id": equipamento_id, "nome": "Pessoa Exemplo", "email": email, "data_prevista": data_prevista},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_rf_07_relatorio_por_tipo_no_mes(cliente, relogio):
    primeiro = emprestar(cliente, 1, "2030-01-10", "ana@exemplo.test")
    emprestar(cliente, 2, "2030-01-10", "bruno@exemplo.test")
    emprestar(cliente, 4, "2030-01-10", "carla@exemplo.test")
    cliente.post(f"/api/emprestimos/{primeiro['id']}/devolver", json={"defeito": False})
    relogio.agora = datetime(2030, 2, 1, 0, 30, tzinfo=FUSO)  # primeiro minuto útil de fevereiro
    emprestar(cliente, 6, "2030-02-02", "davi@exemplo.test")

    janeiro = cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": "2030-01"})
    assert janeiro.status_code == 200
    assert janeiro.json() == {
        "mes": "2030-01",
        "itens": [
            {"tipo": "NOTEBOOK", "quantidade": 2},
            {"tipo": "PROJETOR", "quantidade": 1},
            {"tipo": "HEADSET", "quantidade": 0},
        ],
        "total": 3,
    }
    fevereiro = cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": "2030-02"}).json()
    assert [i["quantidade"] for i in fevereiro["itens"]] == [0, 0, 1]
    assert fevereiro["total"] == 1


def test_rf_07_mes_invalido(cliente):
    for mes in ["2030-13", "2030-00", "2030-1", "janeiro"]:
        assert cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": mes}).status_code == 422, mes
    assert cliente.get("/api/relatorios/emprestimos-por-tipo").status_code == 422


def test_rf_07_mes_so_aceita_digitos_ascii(cliente):
    # Dígitos de largura total (U+FF10..) não são aceitos como mês.
    r = cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": "\uff12\uff10\uff13\uff10-01"})
    assert r.status_code == 422
    assert cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": "9999-12"}).status_code == 422
