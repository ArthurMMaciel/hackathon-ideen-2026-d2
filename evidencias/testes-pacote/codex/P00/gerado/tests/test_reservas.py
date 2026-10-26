from datetime import timedelta

from tests.conftest import iso


def dados(relogio, inicio=(10, 0), fim=(11, 0), **extras):
    corpo = {
        "sala_id": 1, "responsavel_nome": "Pessoa Teste",
        "responsavel_email": "pessoa@example.test", "titulo": "Reunião",
        "participantes": 2, "inicio": iso(relogio.agora, *inicio),
        "fim": iso(relogio.agora, *fim),
    }
    corpo.update(extras)
    return corpo


def criar(cliente, relogio, **extras):
    return cliente.post("/api/reservas", json=dados(relogio, **extras))


def test_ca_01_cria_reserva(cliente, relogio):
    r = criar(cliente, relogio)
    assert r.status_code == 201 and r.json()["status"] == "ATIVA"


def test_ca_02_recusa_conflito(cliente, relogio):
    assert criar(cliente, relogio).status_code == 201
    r = criar(cliente, relogio, inicio=(10, 30), fim=(11, 30))
    assert r.status_code == 409 and r.json()["erro"] == "CONFLITO_HORARIO"
    assert "conflito" in r.json()["mensagem"].lower()


def test_ca_03_permite_encostar(cliente, relogio):
    assert criar(cliente, relogio).status_code == 201
    r = criar(cliente, relogio, inicio=(11, 0), fim=(12, 0))
    assert r.status_code == 201 and r.json()["status"] == "ATIVA"


def test_ca_04_recusa_duracao(cliente, relogio):
    for fim in [(10, 10), (14, 1)]:
        r = criar(cliente, relogio, fim=fim)
        assert r.status_code == 422 and r.json()["erro"] == "DURACAO_INVALIDA"


def test_ca_05_recusa_passado(cliente, relogio):
    r = criar(cliente, relogio, inicio=(8, 59))
    assert r.status_code == 422 and r.json()["erro"] == "INICIO_PASSADO"


def test_ca_06_recusa_capacidade(cliente, relogio):
    r = criar(cliente, relogio, participantes=9)
    assert r.status_code == 422 and r.json()["erro"] == "CAPACIDADE_EXCEDIDA"


def test_ca_07_cancela_e_libera(cliente, relogio):
    criada = criar(cliente, relogio).json()
    cancelada = cliente.post(f"/api/reservas/{criada['id']}/cancelar")
    assert cancelada.status_code == 200 and cancelada.json()["status"] == "CANCELADA"
    assert criar(cliente, relogio).status_code == 201


def test_ca_08_recusa_cancelar_passado(cliente, relogio):
    criada = criar(cliente, relogio).json()
    relogio.avancar(hours=3)
    r = cliente.post(f"/api/reservas/{criada['id']}/cancelar")
    assert r.status_code == 422 and r.json()["erro"] == "CANCELAMENTO_FORA_DO_PRAZO"


def test_ca_09_filtra_livres(cliente, relogio):
    criada = criar(cliente, relogio).json()
    params = {"inicio": iso(relogio.agora, 10), "fim": iso(relogio.agora, 11),
              "local": "SAO_PAULO", "capacidade_minima": 5}
    r = cliente.get("/api/salas/livres", params=params)
    assert r.status_code == 200 and r.json() == []
    cliente.post(f"/api/reservas/{criada['id']}/cancelar")
    r = cliente.get("/api/salas/livres", params=params)
    assert r.status_code == 200 and [s["id"] for s in r.json()] == [1]


def test_ca_10_ignora_canceladas(cliente, relogio):
    criada = criar(cliente, relogio).json()
    cliente.post(f"/api/reservas/{criada['id']}/cancelar")
    assert criar(cliente, relogio, fim=(10, 30)).status_code == 201
    r = cliente.get("/api/relatorios/ocupacao", params={"dia": "2030-01-07"})
    assert r.status_code == 200 and next(x for x in r.json() if x["sala_id"] == 1)["percentual"] == 5.0


def test_rn_02_bordas_duracao(cliente, relogio):
    for minutos, status in [(14, 422), (15, 201), (240, 201), (241, 422)]:
        inicio = relogio.agora.replace(hour=10)
        fim = inicio + timedelta(minutes=minutos)
        r = cliente.post("/api/reservas", json={**dados(relogio), "sala_id": 2 if minutos <= 15 else 4,
                                                "fim": fim.isoformat()})
        assert r.status_code == status


def test_rn_03_borda_inicio(cliente, relogio):
    for minuto, status in [(59, 422), (0, 201), (1, 201)]:
        hora = 8 if minuto == 59 else 9
        r = criar(cliente, relogio, sala_id=2 if minuto == 0 else 3,
                  inicio=(hora, minuto), fim=(10, 0))
        assert r.status_code == status


def test_rn_04_borda_capacidade(cliente, relogio):
    for pessoas, status in [(0, 422), (8, 201), (9, 422)]:
        r = criar(cliente, relogio, participantes=pessoas)
        assert r.status_code == status


def test_rn_05_borda_cancelamento(cliente, relogio):
    a = criar(cliente, relogio).json()
    b = criar(cliente, relogio, sala_id=2).json()
    assert cliente.post(f"/api/reservas/{a['id']}/cancelar").status_code == 200
    relogio.avancar(hours=1)
    r = cliente.post(f"/api/reservas/{b['id']}/cancelar")
    assert r.status_code == 422 and r.json()["erro"] == "CANCELAMENTO_FORA_DO_PRAZO"


def test_rn_06_bordas_ocupacao(cliente, relogio):
    from datetime import datetime
    from app.dominio.relatorios import ocupacao
    from app.relogio import FUSO
    inicio = datetime(2030, 1, 7, 8, tzinfo=FUSO)
    fim = datetime(2030, 1, 7, 18, tzinfo=FUSO)
    assert ocupacao([(inicio - timedelta(hours=1), inicio)], inicio, fim) == (0, 0.0)
    assert ocupacao([(inicio, inicio + timedelta(hours=4))], inicio, fim) == (240, 40.0)
    assert ocupacao([(fim, fim + timedelta(hours=1))], inicio, fim) == (0, 0.0)
    criar(cliente, relogio, inicio=(9, 0), fim=(12, 0))
    r = cliente.get("/api/relatorios/ocupacao", params={"dia": "2030-01-07"})
    assert r.status_code == 200 and next(x for x in r.json() if x["sala_id"] == 1)["percentual"] == 30.0


def test_rn_07_borda_capacidade_sala(cliente):
    for valor, status in [(0, 422), (1, 201), (2, 201)]:
        r = cliente.post("/api/salas", json={"nome": "Teste", "local": "COWORKING",
                                              "capacidade": valor, "recursos": []})
        assert r.status_code == status
