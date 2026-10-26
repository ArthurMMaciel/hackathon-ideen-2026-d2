"""Um teste por critério de aceite do pedido (CA-01 a CA-10)."""

from tests.apoio import amanha, criar_sala, hoje, reservar, reservar_ok


def test_ca_01_reserva_criada_ativa(cliente):
    sala = criar_sala(cliente, capacidade=8)
    r = reservar(cliente, sala["id"], amanha(10), amanha(11), participantes=4)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["status"] == "ATIVA"
    assert corpo["sala_id"] == sala["id"]
    assert corpo["inicio"] == "2030-01-08T10:00:00-03:00"
    assert corpo["fim"] == "2030-01-08T11:00:00-03:00"


def test_ca_02_recusa_conflito(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(10), amanha(11))
    r = reservar(cliente, sala["id"], amanha(10, 30), amanha(11, 30))
    assert r.status_code == 409
    assert r.json()["erro"] == "CONFLITO_HORARIO"
    assert "conflito" in r.json()["mensagem"].lower()


def test_ca_03_reserva_encostada_criada(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(10), amanha(11))
    r = reservar(cliente, sala["id"], amanha(11), amanha(12))
    assert r.status_code == 201
    assert r.json()["status"] == "ATIVA"


def test_ca_04_recusa_duracao_10_minutos(cliente):
    sala = criar_sala(cliente)
    r = reservar(cliente, sala["id"], amanha(10), amanha(10, 10))
    assert r.status_code == 422
    assert r.json()["erro"] == "DURACAO_INVALIDA"


def test_ca_04_recusa_duracao_4h01(cliente):
    sala = criar_sala(cliente)
    r = reservar(cliente, sala["id"], amanha(10), amanha(14, 1))
    assert r.status_code == 422
    assert r.json()["erro"] == "DURACAO_INVALIDA"


def test_ca_05_recusa_inicio_no_passado(cliente):
    sala = criar_sala(cliente)
    r = reservar(cliente, sala["id"], hoje(8), hoje(9))
    assert r.status_code == 422
    assert r.json()["erro"] == "INICIO_NO_PASSADO"


def test_ca_06_recusa_participantes_acima_da_capacidade(cliente):
    sala = criar_sala(cliente, capacidade=4)
    r = reservar(cliente, sala["id"], amanha(10), amanha(11), participantes=5)
    assert r.status_code == 422
    assert r.json()["erro"] == "CAPACIDADE_EXCEDIDA"


def test_ca_07_cancelar_futura_libera_horario(cliente):
    sala = criar_sala(cliente)
    reserva = reservar_ok(cliente, sala["id"], amanha(10), amanha(11))
    r = cliente.post(f"/api/reservas/{reserva['id']}/cancelar")
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELADA"
    nova = reservar(cliente, sala["id"], amanha(10), amanha(11))
    assert nova.status_code == 201
    assert nova.json()["status"] == "ATIVA"
    agenda = cliente.get("/api/reservas", params={"dia": "2030-01-08", "sala_id": sala["id"]}).json()
    assert {(x["id"], x["status"]) for x in agenda} == {(reserva["id"], "CANCELADA"), (nova.json()["id"], "ATIVA")}


def test_ca_08_recusa_cancelar_reserva_passada(cliente, relogio):
    sala = criar_sala(cliente)
    reserva = reservar_ok(cliente, sala["id"], hoje(10), hoje(11))
    relogio.avancar(hours=3)
    r = cliente.post(f"/api/reservas/{reserva['id']}/cancelar")
    assert r.status_code == 409
    assert r.json()["erro"] == "RESERVA_NAO_FUTURA"
    agenda = cliente.get("/api/reservas", params={"dia": "2030-01-07", "sala_id": sala["id"]}).json()
    assert agenda[0]["status"] == "ATIVA"


def test_ca_09_salas_livres_com_filtros(cliente):
    ocupada = criar_sala(cliente, nome="SP Grande Ocupada", local="SAO_PAULO", capacidade=10)
    livre = criar_sala(cliente, nome="SP Grande Livre", local="SAO_PAULO", capacidade=10)
    criar_sala(cliente, nome="SP Pequena", local="SAO_PAULO", capacidade=4)
    criar_sala(cliente, nome="ARA Grande", local="ARARAQUARA", capacidade=10)
    reservar_ok(cliente, ocupada["id"], amanha(10), amanha(11))
    r = cliente.get(
        "/api/salas/livres",
        params={"inicio": amanha(10, 30), "fim": amanha(11, 30), "local": "SAO_PAULO", "capacidade_minima": 6},
    )
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert livre["id"] in ids
    assert ocupada["id"] not in ids
    assert all(s["local"] == "SAO_PAULO" and s["capacidade"] >= 6 for s in r.json())
    # Das salas iniciais, Paulista (SP, 8) também atende; nenhuma outra.
    nomes = sorted(s["nome"] for s in r.json())
    assert nomes == ["Paulista", "SP Grande Livre"]


def test_ca_10_ocupacao_ignora_canceladas(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(8), amanha(10))
    cancelada = reservar_ok(cliente, sala["id"], amanha(10), amanha(12))
    assert cliente.post(f"/api/reservas/{cancelada['id']}/cancelar").status_code == 200
    r = cliente.get("/api/relatorios/ocupacao", params={"dia": "2030-01-08"})
    assert r.status_code == 200
    linha = next(x for x in r.json()["salas"] if x["sala_id"] == sala["id"])
    assert linha["minutos_ocupados"] == 120.0
    assert linha["taxa_ocupacao"] == 20.0
