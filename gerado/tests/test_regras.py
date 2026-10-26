"""Testes de borda das regras de negócio (RN-xx) e dos requisitos sem CA (RF-xx)."""

from datetime import datetime

import pytest

from app.relogio import FUSO
from tests.apoio import amanha, criar_sala, dados_reserva, hoje, reservar, reservar_ok


# RN-01 · sobreposição
def test_rn_01_sobreposicao_contida_recusada(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(10), amanha(12))
    r = reservar(cliente, sala["id"], amanha(10, 30), amanha(11))
    assert r.status_code == 409
    assert r.json()["erro"] == "CONFLITO_HORARIO"


def test_rn_01_encostar_antes_permitido(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(10), amanha(11))
    assert reservar(cliente, sala["id"], amanha(9), amanha(10)).status_code == 201


def test_rn_01_outra_sala_sem_conflito(cliente):
    a = criar_sala(cliente, nome="A")
    b = criar_sala(cliente, nome="B")
    reservar_ok(cliente, a["id"], amanha(10), amanha(11))
    assert reservar(cliente, b["id"], amanha(10), amanha(11)).status_code == 201


# RN-02 · duração
def test_rn_02_duracao_15_minutos_aceita(cliente):
    sala = criar_sala(cliente)
    assert reservar(cliente, sala["id"], amanha(10), amanha(10, 15)).status_code == 201


def test_rn_02_duracao_14_minutos_recusada(cliente):
    sala = criar_sala(cliente)
    r = reservar(cliente, sala["id"], amanha(10), amanha(10, 14))
    assert r.status_code == 422
    assert r.json()["erro"] == "DURACAO_INVALIDA"


def test_rn_02_duracao_16_minutos_aceita(cliente):
    sala = criar_sala(cliente)
    assert reservar(cliente, sala["id"], amanha(10), amanha(10, 16)).status_code == 201


def test_rn_02_duracao_3h59_aceita(cliente):
    sala = criar_sala(cliente)
    assert reservar(cliente, sala["id"], amanha(10), amanha(13, 59)).status_code == 201


def test_rn_02_duracao_4h_aceita(cliente):
    sala = criar_sala(cliente)
    assert reservar(cliente, sala["id"], amanha(10), amanha(14)).status_code == 201


def test_rn_02_fim_antes_do_inicio_recusado(cliente):
    sala = criar_sala(cliente)
    r = reservar(cliente, sala["id"], amanha(11), amanha(10))
    assert r.status_code == 422
    assert r.json()["erro"] == "DURACAO_INVALIDA"


# RN-03 · passado
def test_rn_03_inicio_igual_agora_aceito(cliente):
    sala = criar_sala(cliente)
    assert reservar(cliente, sala["id"], hoje(9), hoje(10)).status_code == 201


def test_rn_03_inicio_um_minuto_antes_recusado(cliente):
    sala = criar_sala(cliente)
    r = reservar(cliente, sala["id"], hoje(8, 59), hoje(10))
    assert r.status_code == 422
    assert r.json()["erro"] == "INICIO_NO_PASSADO"


def test_rn_03_inicio_um_minuto_depois_aceito(cliente):
    sala = criar_sala(cliente)
    assert reservar(cliente, sala["id"], hoje(9, 1), hoje(10)).status_code == 201


def test_rn_03_horario_sem_fuso_recusado(cliente):
    sala = criar_sala(cliente)
    r = reservar(cliente, sala["id"], "2030-01-08T10:00:00", "2030-01-08T11:00:00")
    assert r.status_code == 422


def test_rn_02_fracao_de_segundo_descartada(cliente):
    sala = criar_sala(cliente)
    r = reservar(cliente, sala["id"], "2030-01-08T10:00:00.700-03:00", "2030-01-08T10:15:00.300-03:00")
    assert r.status_code == 201
    assert r.json()["inicio"] == "2030-01-08T10:00:00-03:00"
    assert r.json()["fim"] == "2030-01-08T10:15:00-03:00"


# RN-04 · participantes
def test_rn_04_participantes_igual_capacidade_aceito(cliente):
    sala = criar_sala(cliente, capacidade=4)
    assert reservar(cliente, sala["id"], amanha(10), amanha(11), participantes=4).status_code == 201


def test_rn_04_participantes_abaixo_capacidade_aceito(cliente):
    sala = criar_sala(cliente, capacidade=4)
    assert reservar(cliente, sala["id"], amanha(10), amanha(11), participantes=3).status_code == 201


def test_rn_04_participantes_zero_recusado(cliente):
    sala = criar_sala(cliente, capacidade=4)
    assert reservar(cliente, sala["id"], amanha(10), amanha(11), participantes=0).status_code == 422


# RN-05 · cancelamento
def _no_dia_de_hoje(relogio, hora, minuto):
    relogio.agora = datetime(2030, 1, 7, hora, minuto, tzinfo=FUSO)


def test_rn_05_cancelar_um_minuto_antes_do_inicio(cliente, relogio):
    sala = criar_sala(cliente)
    reserva = reservar_ok(cliente, sala["id"], hoje(10), hoje(11))
    _no_dia_de_hoje(relogio, 9, 59)
    r = cliente.post(f"/api/reservas/{reserva['id']}/cancelar")
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELADA"


def test_rn_05_cancelar_no_inicio_recusado(cliente, relogio):
    sala = criar_sala(cliente)
    reserva = reservar_ok(cliente, sala["id"], hoje(10), hoje(11))
    _no_dia_de_hoje(relogio, 10, 0)
    r = cliente.post(f"/api/reservas/{reserva['id']}/cancelar")
    assert r.status_code == 409
    assert r.json()["erro"] == "RESERVA_NAO_FUTURA"


def test_rn_05_cancelar_em_andamento_recusado(cliente, relogio):
    sala = criar_sala(cliente)
    reserva = reservar_ok(cliente, sala["id"], hoje(10), hoje(11))
    _no_dia_de_hoje(relogio, 10, 30)
    r = cliente.post(f"/api/reservas/{reserva['id']}/cancelar")
    assert r.status_code == 409
    assert r.json()["erro"] == "RESERVA_NAO_FUTURA"


def test_rn_05_cancelar_duas_vezes_recusado(cliente):
    sala = criar_sala(cliente)
    reserva = reservar_ok(cliente, sala["id"], amanha(10), amanha(11))
    assert cliente.post(f"/api/reservas/{reserva['id']}/cancelar").status_code == 200
    r = cliente.post(f"/api/reservas/{reserva['id']}/cancelar")
    assert r.status_code == 409
    assert r.json()["erro"] == "RESERVA_JA_CANCELADA"


def test_rn_05_cancelar_inexistente(cliente):
    r = cliente.post("/api/reservas/999/cancelar")
    assert r.status_code == 404
    assert r.json()["erro"] == "RESERVA_NAO_ENCONTRADA"


# RN-07 · salas livres
def _livres(cliente, inicio, fim, **filtros):
    r = cliente.get("/api/salas/livres", params={"inicio": inicio, "fim": fim, **filtros})
    assert r.status_code == 200, r.text
    return [s["id"] for s in r.json()]


def test_rn_07_intervalo_invalido(cliente):
    r = cliente.get("/api/salas/livres", params={"inicio": amanha(10), "fim": amanha(10)})
    assert r.status_code == 422
    assert r.json()["erro"] == "INTERVALO_INVALIDO"


def test_rn_07_encostada_conta_como_livre(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(10), amanha(11))
    assert sala["id"] in _livres(cliente, amanha(11), amanha(12))
    assert sala["id"] not in _livres(cliente, amanha(10, 59), amanha(12))


def test_rn_07_cancelada_libera_sala(cliente):
    sala = criar_sala(cliente)
    reserva = reservar_ok(cliente, sala["id"], amanha(10), amanha(11))
    assert sala["id"] not in _livres(cliente, amanha(10), amanha(11))
    cliente.post(f"/api/reservas/{reserva['id']}/cancelar")
    assert sala["id"] in _livres(cliente, amanha(10), amanha(11))


def test_rn_07_capacidade_minima_igual_aceita(cliente):
    sala = criar_sala(cliente, local="COWORKING", capacidade=7, nome="Sete")
    assert sala["id"] in _livres(cliente, amanha(10), amanha(11), capacidade_minima=7)
    assert sala["id"] not in _livres(cliente, amanha(10), amanha(11), capacidade_minima=8)
    assert sala["id"] in _livres(cliente, amanha(10), amanha(11), capacidade_minima=6)


def test_rn_07_sem_filtros_lista_todas_livres(cliente):
    assert len(_livres(cliente, amanha(10), amanha(11))) == 6


# RN-08 · ocupação
def _ocupacao(cliente, sala_id, dia="2030-01-08"):
    r = cliente.get("/api/relatorios/ocupacao", params={"dia": dia})
    assert r.status_code == 200, r.text
    return next(x for x in r.json()["salas"] if x["sala_id"] == sala_id)


def test_rn_08_janela_corta_bordas(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(7), amanha(9))
    reservar_ok(cliente, sala["id"], amanha(17, 30), amanha(19))
    linha = _ocupacao(cliente, sala["id"])
    assert linha["minutos_ocupados"] == 90.0
    assert linha["taxa_ocupacao"] == 15.0


def test_rn_08_fora_da_janela_nao_conta(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(7), amanha(8))
    reservar_ok(cliente, sala["id"], amanha(18), amanha(19))
    linha = _ocupacao(cliente, sala["id"])
    assert linha["minutos_ocupados"] == 0.0
    assert linha["taxa_ocupacao"] == 0.0


def test_rn_08_dia_inteiro_100(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(8), amanha(12))
    reservar_ok(cliente, sala["id"], amanha(12), amanha(16))
    reservar_ok(cliente, sala["id"], amanha(16), amanha(18))
    assert _ocupacao(cliente, sala["id"])["taxa_ocupacao"] == 100.0


def test_rn_08_arredondamento_uma_casa(cliente):
    sala = criar_sala(cliente)
    reservar_ok(cliente, sala["id"], amanha(10), amanha(10, 20))
    assert _ocupacao(cliente, sala["id"])["taxa_ocupacao"] == 3.3


def test_rn_08_lista_todas_as_salas(cliente):
    r = cliente.get("/api/relatorios/ocupacao", params={"dia": "2030-02-01"})
    corpo = r.json()
    assert r.status_code == 200
    assert corpo["minutos_janela"] == 600
    assert len(corpo["salas"]) == 6
    assert all(x["taxa_ocupacao"] == 0.0 for x in corpo["salas"])


# RN-09 · validação de sala
@pytest.mark.parametrize("capacidade,esperado", [(0, 422), (1, 201), (1000, 201), (1001, 422)])
def test_rn_09_capacidade_bordas(cliente, capacidade, esperado):
    r = cliente.post(
        "/api/salas", json={"nome": f"Cap {capacidade}", "local": "SAO_PAULO", "capacidade": capacidade}
    )
    assert r.status_code == esperado


@pytest.mark.parametrize(
    "corpo",
    [
        {"nome": "X", "local": "RIO", "capacidade": 4},
        {"nome": "X", "local": "SAO_PAULO", "capacidade": 4, "recursos": ["PROJETOR"]},
    ],
)
def test_rn_09_enum_invalido(cliente, corpo):
    assert cliente.post("/api/salas", json=corpo).status_code == 422


def test_rn_09_recursos_repetidos(cliente):
    r = cliente.post(
        "/api/salas", json={"nome": "X", "local": "SAO_PAULO", "capacidade": 4, "recursos": ["TV", "TV"]}
    )
    assert r.status_code == 422
    assert r.json()["erro"] == "RECURSOS_REPETIDOS"


# RN-10 · nome único por local
def test_rn_10_nome_duplicado_mesmo_local(cliente):
    criar_sala(cliente, nome="Sala X", local="SAO_PAULO")
    r = cliente.post("/api/salas", json={"nome": "sala x", "local": "SAO_PAULO", "capacidade": 4})
    assert r.status_code == 409
    assert r.json()["erro"] == "SALA_DUPLICADA"


def test_rn_10_mesmo_nome_outro_local(cliente):
    criar_sala(cliente, nome="Sala X", local="SAO_PAULO")
    r = cliente.post("/api/salas", json={"nome": "Sala X", "local": "ARARAQUARA", "capacidade": 4})
    assert r.status_code == 201


# RF-xx
def test_rf_01_cadastrar_sala(cliente):
    r = cliente.post(
        "/api/salas",
        json={"nome": "Nova", "local": "COWORKING", "capacidade": 5, "recursos": ["QUADRO", "TV"]},
    )
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["local"] == "COWORKING"
    assert corpo["recursos"] == ["TV", "QUADRO"]
    assert any(s["id"] == corpo["id"] for s in cliente.get("/api/salas").json())


def test_rf_02_consultar_sala(cliente):
    sala = criar_sala(cliente)
    r = cliente.get(f"/api/salas/{sala['id']}")
    assert r.status_code == 200
    assert r.json()["nome"] == "Sala Teste"
    r = cliente.get("/api/salas/999")
    assert r.status_code == 404
    assert r.json()["erro"] == "SALA_NAO_ENCONTRADA"


def test_rf_03_carga_inicial_seis_salas(cliente):
    salas = cliente.get("/api/salas").json()
    assert len(salas) == 6
    for local in ("SAO_PAULO", "ARARAQUARA", "COWORKING"):
        assert sum(1 for s in salas if s["local"] == local) == 2


def test_rf_04_sala_inexistente(cliente):
    r = cliente.post("/api/reservas", json=dados_reserva(999, amanha(10), amanha(11)))
    assert r.status_code == 404
    assert r.json()["erro"] == "SALA_NAO_ENCONTRADA"


def test_rf_05_agenda_do_dia_por_sala(cliente):
    a = criar_sala(cliente, nome="A")
    b = criar_sala(cliente, nome="B")
    ra = reservar_ok(cliente, a["id"], amanha(10), amanha(11))
    rb = reservar_ok(cliente, b["id"], amanha(9), amanha(10))
    reservar_ok(cliente, a["id"], "2030-01-09T10:00:00-03:00", "2030-01-09T11:00:00-03:00")
    todas = cliente.get("/api/reservas", params={"dia": "2030-01-08"}).json()
    assert [x["id"] for x in todas] == [rb["id"], ra["id"]]
    assert todas[0]["sala_nome"] == "B"
    so_a = cliente.get("/api/reservas", params={"dia": "2030-01-08", "sala_id": a["id"]}).json()
    assert [x["id"] for x in so_a] == [ra["id"]]
    r = cliente.get("/api/reservas", params={"dia": "2030-01-08", "sala_id": 999})
    assert r.status_code == 404


def test_rf_05_reserva_atravessando_meia_noite(cliente):
    sala = criar_sala(cliente)
    reserva = reservar_ok(cliente, sala["id"], amanha(23), "2030-01-09T01:00:00-03:00")
    for dia in ("2030-01-08", "2030-01-09"):
        ids = [x["id"] for x in cliente.get("/api/reservas", params={"dia": dia}).json()]
        assert reserva["id"] in ids
    ids = [x["id"] for x in cliente.get("/api/reservas", params={"dia": "2030-01-10"}).json()]
    assert reserva["id"] not in ids
