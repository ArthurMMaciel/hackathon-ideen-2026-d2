"""Testes de borda das regras de negócio (RN-xx) e dos requisitos auxiliares (RF-xx)."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from tests.conftest import AGORA_INICIAL, iso
from tests.test_criterios_aceite import D1, SALA_IBIRAPUERA, SALA_PAULISTA, reserva


def criar(cliente, **kw):
    return cliente.post("/api/reservas", json=reserva(**kw))


@pytest.mark.parametrize(
    "inicio,fim",
    [((9, 0), (10, 1)), ((10, 59), (12, 0)), ((10, 15), (10, 45)), ((9, 0), (12, 0))],
)
def test_rn_01_sobreposicao_bordas(cliente, inicio, fim):
    assert criar(cliente).status_code == 201  # base 10:00–11:00
    r = criar(cliente, inicio=iso(D1, *inicio), fim=iso(D1, *fim))
    assert r.status_code == 409
    assert r.json()["erro"] == "CONFLITO_HORARIO"


def test_rn_01_encostar_dos_dois_lados_e_outra_sala(cliente):
    assert criar(cliente).status_code == 201
    assert criar(cliente, inicio=iso(D1, 9), fim=iso(D1, 10)).status_code == 201
    assert criar(cliente, inicio=iso(D1, 11), fim=iso(D1, 12)).status_code == 201
    assert criar(cliente, sala_id=SALA_IBIRAPUERA).status_code == 201


@pytest.mark.parametrize("minutos,status", [(14, 422), (15, 201), (16, 201), (239, 201), (240, 201), (241, 422)])
def test_rn_02_duracao_bordas(cliente, minutos, status):
    inicio = D1.replace(hour=8)
    fim = inicio + timedelta(minutes=minutos)
    r = criar(cliente, inicio=inicio.isoformat(), fim=fim.isoformat())
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "DURACAO_INVALIDA"


@pytest.mark.parametrize("minuto_offset,status", [(-1, 422), (0, 201), (1, 201)])
def test_rn_03_inicio_bordas(cliente, minuto_offset, status):
    inicio = AGORA_INICIAL + timedelta(minutes=minuto_offset)
    r = criar(cliente, inicio=inicio.isoformat(), fim=(inicio + timedelta(hours=1)).isoformat())
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "INICIO_NO_PASSADO"


@pytest.mark.parametrize("participantes,status", [(3, 201), (4, 201), (5, 422), (0, 422)])
def test_rn_04_participantes_bordas(cliente, participantes, status):
    r = criar(cliente, sala_id=SALA_IBIRAPUERA, participantes=participantes)
    assert r.status_code == status
    if participantes == 5:
        assert r.json()["erro"] == "CAPACIDADE_EXCEDIDA"


def test_rn_05_cancelamento_bordas(cliente, relogio):
    inicio = AGORA_INICIAL + timedelta(minutes=1)  # 09:01
    fim = inicio + timedelta(hours=1)
    a = criar(cliente, inicio=inicio.isoformat(), fim=fim.isoformat()).json()
    b = criar(cliente, sala_id=SALA_IBIRAPUERA, inicio=inicio.isoformat(), fim=fim.isoformat()).json()
    # Um minuto antes do início: pode cancelar.
    r = cliente.post(f"/api/reservas/{a['id']}/cancelar")
    assert r.status_code == 200 and r.json()["status"] == "CANCELADA"
    # Já cancelada.
    r = cliente.post(f"/api/reservas/{a['id']}/cancelar")
    assert r.status_code == 409 and r.json()["erro"] == "RESERVA_JA_CANCELADA"
    # Início igual a agora: não é futura.
    relogio.avancar(minutes=1)
    r = cliente.post(f"/api/reservas/{b['id']}/cancelar")
    assert r.status_code == 422 and r.json()["erro"] == "CANCELAMENTO_NAO_PERMITIDO"
    # Em andamento.
    relogio.avancar(minutes=30)
    r = cliente.post(f"/api/reservas/{b['id']}/cancelar")
    assert r.status_code == 422 and r.json()["erro"] == "CANCELAMENTO_NAO_PERMITIDO"


def test_rn_05_cancelar_inexistente(cliente):
    r = cliente.post("/api/reservas/999/cancelar")
    assert r.status_code == 404
    assert r.json()["erro"] == "RESERVA_NAO_ENCONTRADA"


def test_rn_08_ocupacao_janela_bordas(cliente):
    assert criar(cliente, inicio=iso(D1, 7), fim=iso(D1, 9)).status_code == 201  # 60 min na janela
    assert criar(cliente, inicio=iso(D1, 17, 30), fim=iso(D1, 19)).status_code == 201  # 30 min na janela
    assert criar(cliente, sala_id=SALA_IBIRAPUERA, inicio=iso(D1, 18), fim=iso(D1, 19)).status_code == 201  # 0
    assert criar(cliente, sala_id=3, inicio=iso(D1, 8), fim=iso(D1, 8, 20)).status_code == 201  # 20 min
    salas = {s["sala_id"]: s for s in cliente.get("/api/relatorios/ocupacao", params={"data": "2030-01-08"}).json()["salas"]}
    assert (salas[SALA_PAULISTA]["minutos_ocupados"], salas[SALA_PAULISTA]["taxa_ocupacao"]) == (90, 15.0)
    assert (salas[SALA_IBIRAPUERA]["minutos_ocupados"], salas[SALA_IBIRAPUERA]["taxa_ocupacao"]) == (0, 0.0)
    assert (salas[3]["minutos_ocupados"], salas[3]["taxa_ocupacao"]) == (20, 3.3)


def test_rn_08_reserva_que_atravessa_meia_noite(cliente):
    inicio = D1.replace(hour=22)
    fim = inicio + timedelta(hours=4)  # termina 02:00 do dia seguinte, fora da janela dos dois dias
    assert criar(cliente, inicio=inicio.isoformat(), fim=fim.isoformat()).status_code == 201
    salas = cliente.get("/api/relatorios/ocupacao", params={"data": "2030-01-09"}).json()["salas"]
    assert all(s["minutos_ocupados"] == 0 for s in salas)


def test_rn_09_intervalo_invalido(cliente):
    for inicio, fim in ((iso(D1, 10), iso(D1, 10)), (iso(D1, 11), iso(D1, 10))):
        r = criar(cliente, inicio=inicio, fim=fim)
        assert r.status_code == 422 and r.json()["erro"] == "INTERVALO_INVALIDO"
        r = cliente.get("/api/salas/livres", params={"inicio": inicio, "fim": fim})
        assert r.status_code == 422 and r.json()["erro"] == "INTERVALO_INVALIDO"


def sala(**kw):
    corpo = {"nome": "Sala Nova", "local": "COWORKING", "capacidade": 5, "recursos": ["TV"]}
    corpo.update(kw)
    return corpo


@pytest.mark.parametrize("capacidade,status", [(0, 422), (1, 201), (500, 201), (501, 422)])
def test_rn_10_sala_capacidade_bordas(cliente, capacidade, status):
    r = cliente.post("/api/salas", json=sala(capacidade=capacidade))
    assert r.status_code == status
    if status == 201:
        assert r.json()["capacidade"] == capacidade
        assert r.json()["recursos"] == ["TV"]


def test_rn_10_sala_cadastro_bordas(cliente):
    assert cliente.post("/api/salas", json=sala()).status_code == 201
    dup = cliente.post("/api/salas", json=sala(nome="  sala NOVA "))
    assert dup.status_code == 409 and dup.json()["erro"] == "SALA_NOME_DUPLICADO"
    assert cliente.post("/api/salas", json=sala(nome="Outra", recursos=["TV", "TV"])).status_code == 422
    assert cliente.post("/api/salas", json=sala(nome="Outra", local="RIO")).status_code == 422
    assert cliente.post("/api/salas", json=sala(nome="   ")).status_code == 422
    assert cliente.post("/api/salas", json=sala(nome="Outra", recursos=["CAFE"])).status_code == 422
    sem_recursos = cliente.post("/api/salas", json={"nome": "Sem recursos", "local": "SAO_PAULO", "capacidade": 3})
    assert sem_recursos.status_code == 201 and sem_recursos.json()["recursos"] == []


def test_rn_11_validacao_reserva(cliente):
    assert criar(cliente, responsavel_email="sem-arroba").status_code == 422
    assert criar(cliente, titulo="").status_code == 422
    assert criar(cliente, responsavel_nome="   ").status_code == 422
    sem_fuso = criar(cliente, inicio="2030-01-08T10:00:00", fim="2030-01-08T11:00:00")
    assert sem_fuso.status_code == 422
    r = criar(cliente, sala_id=999)
    assert r.status_code == 404 and r.json()["erro"] == "SALA_NAO_ENCONTRADA"
    assert cliente.get("/api/salas/livres", params={"inicio": "2030-01-08T10:00:00", "fim": iso(D1, 11)}).status_code == 422


def test_rf_02_consultar_sala(cliente):
    r = cliente.get(f"/api/salas/{SALA_PAULISTA}")
    assert r.status_code == 200 and r.json()["nome"] == "Sala Paulista"
    r = cliente.get("/api/salas/999")
    assert r.status_code == 404 and r.json()["erro"] == "SALA_NAO_ENCONTRADA"
    assert cliente.get("/api/reservas/999").status_code == 404


def test_rf_03_carga_inicial(tmp_path):
    caminho = str(tmp_path / "carga.db")
    for _ in range(2):  # reinicia no mesmo banco: continua com 6
        with TestClient(criar_app(caminho)) as c:
            salas = c.get("/api/salas").json()
            assert len(salas) == 6
            for local in ("SAO_PAULO", "ARARAQUARA", "COWORKING"):
                assert sum(1 for s in salas if s["local"] == local) == 2


def test_rf_08_agenda_do_dia(cliente):
    tarde = criar(cliente, inicio=iso(D1, 14), fim=iso(D1, 15)).json()
    manha = criar(cliente, inicio=iso(D1, 9), fim=iso(D1, 10)).json()
    outra = criar(cliente, sala_id=SALA_IBIRAPUERA, inicio=iso(D1, 9), fim=iso(D1, 10)).json()
    d2 = D1 + timedelta(days=1)
    criar(cliente, inicio=iso(d2, 9), fim=iso(d2, 10))
    cliente.post(f"/api/reservas/{tarde['id']}/cancelar")
    r = cliente.get("/api/reservas", params={"data": "2030-01-08"})
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert set(ids) == {tarde["id"], manha["id"], outra["id"]}
    assert ids[-1] == tarde["id"]
    assert {x["id"]: x["status"] for x in r.json()}[tarde["id"]] == "CANCELADA"
    por_sala = cliente.get("/api/reservas", params={"data": "2030-01-08", "sala_id": SALA_IBIRAPUERA}).json()
    assert [x["id"] for x in por_sala] == [outra["id"]]
    assert cliente.get("/api/reservas").status_code == 422
