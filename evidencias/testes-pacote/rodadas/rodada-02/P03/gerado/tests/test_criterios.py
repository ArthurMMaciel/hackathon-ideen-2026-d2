"""Um teste por critério de aceite do pedido (CA-01 a CA-10)."""

from datetime import timedelta

from tests.apoio import INICIO_PADRAO, cancelar, criar_turma, inscrever, inscritos, ir_para, presenca


def test_ca_01_inscricao_com_vaga_confirmada(cliente):
    turma = criar_turma(cliente, vagas=2)
    r = inscrever(cliente, turma["id"])
    assert r.status_code == 201
    assert r.json()["situacao"] == "CONFIRMADA"
    assert r.json()["posicao_espera"] is None


def test_ca_02_turma_lotada_entra_em_espera_primeira_da_fila(cliente):
    turma = criar_turma(cliente, vagas=1)
    assert inscrever(cliente, turma["id"], 1).json()["situacao"] == "CONFIRMADA"
    r = inscrever(cliente, turma["id"], 2)
    assert r.status_code == 201
    assert r.json()["situacao"] == "ESPERA"
    assert r.json()["posicao_espera"] == 1


def test_ca_03_cancelar_confirmada_promove_primeira_da_espera(cliente):
    turma = criar_turma(cliente, vagas=1)
    a = inscrever(cliente, turma["id"], 1).json()
    b = inscrever(cliente, turma["id"], 2).json()
    c = inscrever(cliente, turma["id"], 3).json()
    r = cancelar(cliente, a["id"])
    assert r.status_code == 200
    assert r.json()["inscricao"]["situacao"] == "CANCELADA"
    assert r.json()["promovida"]["id"] == b["id"]
    assert r.json()["promovida"]["situacao"] == "CONFIRMADA"
    lista = inscritos(cliente, turma["id"])
    assert lista[b["id"]]["situacao"] == "CONFIRMADA"
    assert lista[c["id"]]["situacao"] == "ESPERA"
    assert lista[c["id"]]["posicao_espera"] == 1


def test_ca_04_mesmo_email_duas_vezes_recusado(cliente):
    turma = criar_turma(cliente, vagas=5)
    assert inscrever(cliente, turma["id"], email="ana@exemplo.test").status_code == 201
    r = inscrever(cliente, turma["id"], email="ana@exemplo.test")
    assert r.status_code == 409
    assert r.json()["erro"] == "INSCRICAO_DUPLICADA"
    assert len(inscritos(cliente, turma["id"])) == 1


def test_ca_05_inscrever_23_horas_antes_recusado(cliente, relogio):
    turma = criar_turma(cliente)
    ir_para(relogio, INICIO_PADRAO - timedelta(hours=23))
    r = inscrever(cliente, turma["id"])
    assert r.status_code == 422
    assert r.json()["erro"] == "INSCRICOES_ENCERRADAS"
    assert inscritos(cliente, turma["id"]) == {}


def test_ca_06_cancelar_depois_do_inicio_recusado(cliente, relogio):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"]).json()
    ir_para(relogio, INICIO_PADRAO + timedelta(hours=1))
    r = cancelar(cliente, a["id"])
    assert r.status_code == 422
    assert r.json()["erro"] == "CANCELAMENTO_ENCERRADO"
    assert inscritos(cliente, turma["id"])[a["id"]]["situacao"] == "CONFIRMADA"


def test_ca_07_presenca_antes_do_inicio_recusada(cliente, relogio):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"]).json()
    ir_para(relogio, INICIO_PADRAO - timedelta(hours=1))
    r = presenca(cliente, a["id"], "PRESENTE")
    assert r.status_code == 422
    assert r.json()["erro"] == "TURMA_NAO_INICIADA"
    assert inscritos(cliente, turma["id"])[a["id"]]["situacao"] == "CONFIRMADA"


def test_ca_08_presenca_de_inscricao_em_espera_recusada(cliente, relogio):
    turma = criar_turma(cliente, vagas=1)
    inscrever(cliente, turma["id"], 1)
    espera = inscrever(cliente, turma["id"], 2).json()
    assert espera["situacao"] == "ESPERA"
    ir_para(relogio, INICIO_PADRAO + timedelta(hours=1))
    r = presenca(cliente, espera["id"], "PRESENTE")
    assert r.status_code == 409
    assert r.json()["erro"] == "SITUACAO_SEM_PRESENCA"
    assert inscritos(cliente, turma["id"])[espera["id"]]["situacao"] == "ESPERA"


def test_ca_09_turma_lotada_aparece_com_zero_vagas(cliente):
    turma = criar_turma(cliente, vagas=2)
    inscrever(cliente, turma["id"], 1)
    inscrever(cliente, turma["id"], 2)
    r = cliente.get("/api/turmas")
    assert r.status_code == 200
    encontrada = [t for t in r.json() if t["id"] == turma["id"]]
    assert len(encontrada) == 1
    assert encontrada[0]["vagas_restantes"] == 0


def test_ca_10_taxa_presenca_3_presentes_1_ausente_75(cliente, relogio):
    turma = criar_turma(cliente, vagas=4)
    ids = [inscrever(cliente, turma["id"], n).json()["id"] for n in range(1, 5)]
    ir_para(relogio, INICIO_PADRAO + timedelta(hours=1))
    for i, situacao in zip(ids, ["PRESENTE", "PRESENTE", "PRESENTE", "AUSENTE"]):
        assert presenca(cliente, i, situacao).status_code == 200
    r = cliente.get(f"/api/turmas/{turma['id']}/relatorio-presenca")
    assert r.status_code == 200
    assert r.json() == {"turma_id": turma["id"], "presentes": 3, "ausentes": 1, "taxa_presenca_percentual": 75.0}
