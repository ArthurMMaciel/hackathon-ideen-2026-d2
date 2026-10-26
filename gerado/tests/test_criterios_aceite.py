"""Um teste por critério de aceite do pedido (CA-01 a CA-10)."""

from datetime import timedelta

from tests.conftest import AGORA_INICIAL, iso

D1 = AGORA_INICIAL + timedelta(days=1)  # 2030-01-08
SALA_PAULISTA = 1  # capacidade 8
SALA_IBIRAPUERA = 2  # capacidade 4


def reserva(sala_id=SALA_PAULISTA, inicio=None, fim=None, participantes=4, **extra):
    corpo = {
        "sala_id": sala_id,
        "responsavel_nome": "Ana Teste",
        "responsavel_email": "ana@exemplo.com",
        "titulo": "Planejamento",
        "participantes": participantes,
        "inicio": inicio or iso(D1, 10),
        "fim": fim or iso(D1, 11),
    }
    corpo.update(extra)
    return corpo


def test_ca_01_reserva_criada_ativa(cliente):
    r = cliente.post("/api/reservas", json=reserva())
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["status"] == "ATIVA"
    assert corpo["sala_id"] == SALA_PAULISTA
    assert corpo["titulo"] == "Planejamento"
    assert corpo["inicio"] == "2030-01-08T10:00:00-03:00"
    assert corpo["fim"] == "2030-01-08T11:00:00-03:00"


def test_ca_02_recusa_conflito(cliente):
    assert cliente.post("/api/reservas", json=reserva()).status_code == 201
    r = cliente.post("/api/reservas", json=reserva(inicio=iso(D1, 10, 30), fim=iso(D1, 11, 30)))
    assert r.status_code == 409
    assert r.json()["erro"] == "CONFLITO_HORARIO"
    assert "conflito" in r.json()["mensagem"].lower()


def test_ca_03_encostar_permitido(cliente):
    assert cliente.post("/api/reservas", json=reserva()).status_code == 201
    r = cliente.post("/api/reservas", json=reserva(inicio=iso(D1, 11), fim=iso(D1, 12)))
    assert r.status_code == 201
    assert r.json()["status"] == "ATIVA"


def test_ca_04_recusa_duracao(cliente):
    curta = cliente.post("/api/reservas", json=reserva(inicio=iso(D1, 10), fim=iso(D1, 10, 10)))
    longa = cliente.post("/api/reservas", json=reserva(inicio=iso(D1, 10), fim=iso(D1, 14, 1)))
    for r in (curta, longa):
        assert r.status_code == 422
        assert r.json()["erro"] == "DURACAO_INVALIDA"


def test_ca_05_recusa_inicio_passado(cliente):
    r = cliente.post("/api/reservas", json=reserva(inicio=iso(AGORA_INICIAL, 8), fim=iso(AGORA_INICIAL, 9, 30)))
    assert r.status_code == 422
    assert r.json()["erro"] == "INICIO_NO_PASSADO"


def test_ca_06_recusa_participantes_acima_capacidade(cliente):
    r = cliente.post("/api/reservas", json=reserva(sala_id=SALA_IBIRAPUERA, participantes=5))
    assert r.status_code == 422
    assert r.json()["erro"] == "CAPACIDADE_EXCEDIDA"


def test_ca_07_cancelar_reserva_futura(cliente):
    criada = cliente.post("/api/reservas", json=reserva()).json()
    r = cliente.post(f"/api/reservas/{criada['id']}/cancelar")
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELADA"
    assert r.json()["cancelada_em"] is not None
    # Horário liberado: mesma sala, mesmo horário.
    nova = cliente.post("/api/reservas", json=reserva())
    assert nova.status_code == 201
    # Histórico mantido.
    assert cliente.get(f"/api/reservas/{criada['id']}").json()["status"] == "CANCELADA"


def test_ca_08_recusa_cancelar_reserva_passada(cliente, relogio):
    criada = cliente.post("/api/reservas", json=reserva()).json()
    relogio.avancar(days=2)
    r = cliente.post(f"/api/reservas/{criada['id']}/cancelar")
    assert r.status_code == 422
    assert r.json()["erro"] == "CANCELAMENTO_NAO_PERMITIDO"
    assert cliente.get(f"/api/reservas/{criada['id']}").json()["status"] == "ATIVA"


def livres(cliente, inicio, fim, **filtros):
    r = cliente.get("/api/salas/livres", params={"inicio": inicio, "fim": fim, **filtros})
    assert r.status_code == 200, r.text
    return [s["nome"] for s in r.json()]


def test_ca_09_salas_livres_com_filtros(cliente):
    assert cliente.post("/api/reservas", json=reserva()).status_code == 201
    assert livres(cliente, iso(D1, 10), iso(D1, 11), local="SAO_PAULO", capacidade_minima=4) == ["Sala Ibirapuera"]
    assert livres(cliente, iso(D1, 10), iso(D1, 11), local="SAO_PAULO", capacidade_minima=5) == []
    assert livres(cliente, iso(D1, 11), iso(D1, 12), local="SAO_PAULO", capacidade_minima=5) == ["Sala Paulista"]
    todas = livres(cliente, iso(D1, 10), iso(D1, 11))
    assert len(todas) == 5 and "Sala Paulista" not in todas


def test_ca_10_ocupacao_ignora_canceladas(cliente):
    assert cliente.post("/api/reservas", json=reserva()).status_code == 201
    cancelar = cliente.post("/api/reservas", json=reserva(inicio=iso(D1, 14), fim=iso(D1, 16))).json()
    assert cliente.post(f"/api/reservas/{cancelar['id']}/cancelar").status_code == 200
    r = cliente.get("/api/relatorios/ocupacao", params={"data": "2030-01-08"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["minutos_janela"] == 600
    por_sala = {s["sala_id"]: s for s in corpo["salas"]}
    assert len(por_sala) == 6
    assert por_sala[SALA_PAULISTA]["minutos_ocupados"] == 60
    assert por_sala[SALA_PAULISTA]["taxa_ocupacao"] == 10.0
    assert all(s["taxa_ocupacao"] == 0.0 for i, s in por_sala.items() if i != SALA_PAULISTA)
