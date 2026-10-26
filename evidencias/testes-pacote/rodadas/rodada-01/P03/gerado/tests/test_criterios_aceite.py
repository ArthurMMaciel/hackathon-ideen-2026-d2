"""Um teste por critério de aceite do pedido (CA-01 a CA-10)."""

from datetime import timedelta

from tests.apoio import INICIO_PADRAO, criar_turma, inicio_mais, inscrever, ir_para


def test_ca_01_inscricao_com_vaga_confirmada(cliente):
    turma = criar_turma(cliente, vagas=2)
    r = inscrever(cliente, turma["id"], 1)
    assert r.status_code == 201
    assert r.json()["situacao"] == "CONFIRMADA"
    assert r.json()["posicao_espera"] is None


def test_ca_02_turma_lotada_entra_em_espera_primeira(cliente):
    turma = criar_turma(cliente, vagas=1)
    assert inscrever(cliente, turma["id"], 1).json()["situacao"] == "CONFIRMADA"
    r = inscrever(cliente, turma["id"], 2)
    assert r.status_code == 201
    assert r.json()["situacao"] == "ESPERA"
    assert r.json()["posicao_espera"] == 1


def test_ca_03_cancelar_confirmada_promove_primeira_espera(cliente):
    turma = criar_turma(cliente, vagas=1)
    a = inscrever(cliente, turma["id"], 1).json()
    b = inscrever(cliente, turma["id"], 2).json()
    c = inscrever(cliente, turma["id"], 3).json()
    r = cliente.post(f"/api/inscricoes/{a['id']}/cancelar")
    assert r.status_code == 200
    assert r.json()["cancelada"]["situacao"] == "CANCELADA"
    assert r.json()["promovida"]["id"] == b["id"]
    assert r.json()["promovida"]["situacao"] == "CONFIRMADA"
    inscritos = {i["id"]: i for i in cliente.get(f"/api/turmas/{turma['id']}/inscricoes").json()}
    assert inscritos[b["id"]]["situacao"] == "CONFIRMADA"
    assert inscritos[c["id"]]["situacao"] == "ESPERA"
    assert inscritos[c["id"]]["posicao_espera"] == 1


def test_ca_04_mesmo_email_duas_vezes_recusado(cliente):
    turma = criar_turma(cliente, vagas=5)
    assert inscrever(cliente, turma["id"], 1).status_code == 201
    r = inscrever(cliente, turma["id"], 1)
    assert r.status_code == 409
    assert r.json()["erro"] == "INSCRICAO_DUPLICADA"


def test_ca_05_inscrever_23h_antes_recusado(cliente, relogio):
    turma = criar_turma(cliente, inicio=relogio.agora + timedelta(hours=23))
    r = inscrever(cliente, turma["id"], 1)
    assert r.status_code == 422
    assert r.json()["erro"] == "INSCRICOES_ENCERRADAS"


def test_ca_06_cancelar_apos_inicio_recusado(cliente, relogio):
    turma = criar_turma(cliente)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    ir_para(relogio, inicio_mais(1))
    r = cliente.post(f"/api/inscricoes/{inscricao['id']}/cancelar")
    assert r.status_code == 422
    assert r.json()["erro"] == "CANCELAMENTO_ENCERRADO"
    inscritos = cliente.get(f"/api/turmas/{turma['id']}/inscricoes").json()
    assert inscritos[0]["situacao"] == "CONFIRMADA"


def test_ca_07_presenca_antes_do_inicio_recusada(cliente):
    turma = criar_turma(cliente)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    r = cliente.post(f"/api/inscricoes/{inscricao['id']}/presenca", json={"situacao": "PRESENTE"})
    assert r.status_code == 422
    assert r.json()["erro"] == "PRESENCA_ANTES_DO_INICIO"


def test_ca_08_presenca_de_espera_recusada(cliente, relogio):
    turma = criar_turma(cliente, vagas=1)
    inscrever(cliente, turma["id"], 1)
    espera = inscrever(cliente, turma["id"], 2).json()
    assert espera["situacao"] == "ESPERA"
    ir_para(relogio, INICIO_PADRAO)
    r = cliente.post(f"/api/inscricoes/{espera['id']}/presenca", json={"situacao": "PRESENTE"})
    assert r.status_code == 422
    assert r.json()["erro"] == "PRESENCA_SITUACAO_INVALIDA"


def test_ca_09_turma_lotada_aparece_com_zero_vagas(cliente):
    turma = criar_turma(cliente, vagas=2)
    inscrever(cliente, turma["id"], 1)
    inscrever(cliente, turma["id"], 2)
    r = cliente.get("/api/turmas")
    assert r.status_code == 200
    encontrada = [t for t in r.json() if t["id"] == turma["id"]]
    assert len(encontrada) == 1
    assert encontrada[0]["vagas_restantes"] == 0


def test_ca_10_taxa_presenca_75(cliente, relogio):
    turma = criar_turma(cliente, vagas=4)
    ids = [inscrever(cliente, turma["id"], n).json()["id"] for n in range(1, 5)]
    ir_para(relogio, INICIO_PADRAO)
    for i, situacao in zip(ids, ["PRESENTE", "PRESENTE", "PRESENTE", "AUSENTE"]):
        assert cliente.post(f"/api/inscricoes/{i}/presenca", json={"situacao": situacao}).status_code == 200
    r = cliente.get(f"/api/turmas/{turma['id']}/taxa-presenca")
    assert r.status_code == 200
    assert r.json() == {"turma_id": turma["id"], "presentes": 3, "ausentes": 1, "taxa_presenca": 75.0}
