"""Bordas e demais regras de negócio do plano de testes da SPEC."""

from datetime import timedelta

import pytest

from tests.apoio import INICIO_PADRAO, cancelar, criar_turma, inscrever, inscritos, ir_para, presenca
from tests.conftest import AGORA_INICIAL


def _corpo_turma(**mudancas):
    corpo = {"titulo": "Turma", "inicio": INICIO_PADRAO.isoformat(), "duracao_minutos": 60,
             "modalidade": "PRESENCIAL", "vagas": 10}
    corpo.update(mudancas)
    return corpo


@pytest.mark.parametrize("vagas, status", [(0, 422), (1, 201), (50, 201), (51, 422)])
def test_rn_01_vagas_limites(cliente, vagas, status):
    r = cliente.post("/api/turmas", json=_corpo_turma(vagas=vagas))
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "VAGAS_INVALIDAS"
    else:
        assert r.json()["vagas"] == vagas
        assert r.json()["vagas_restantes"] == vagas


@pytest.mark.parametrize("duracao, status", [(0, 422), (1, 201), (1440, 201), (1441, 422)])
def test_rn_02_duracao_limites(cliente, duracao, status):
    r = cliente.post("/api/turmas", json=_corpo_turma(duracao_minutos=duracao))
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "DURACAO_INVALIDA"
    else:
        assert r.json()["duracao_minutos"] == duracao


@pytest.mark.parametrize("antes, status", [
    (timedelta(hours=24, minutes=1), 201),
    (timedelta(hours=24), 201),
    (timedelta(hours=23, minutes=59), 422),
])
def test_rn_06_janela_inscricao_bordas(cliente, relogio, antes, status):
    turma = criar_turma(cliente)
    ir_para(relogio, INICIO_PADRAO - antes)
    r = inscrever(cliente, turma["id"])
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "INSCRICOES_ENCERRADAS"
    else:
        assert r.json()["situacao"] == "CONFIRMADA"


@pytest.mark.parametrize("momento, status", [
    (INICIO_PADRAO - timedelta(minutes=1), 200),
    (INICIO_PADRAO, 422),
])
def test_rn_07_cancelamento_bordas(cliente, relogio, momento, status):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"]).json()
    ir_para(relogio, momento)
    r = cancelar(cliente, a["id"])
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "CANCELAMENTO_ENCERRADO"
    else:
        assert r.json()["inscricao"]["situacao"] == "CANCELADA"


@pytest.mark.parametrize("momento, status", [
    (INICIO_PADRAO - timedelta(minutes=1), 422),
    (INICIO_PADRAO, 200),
])
def test_rn_10_presenca_bordas(cliente, relogio, momento, status):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"]).json()
    ir_para(relogio, momento)
    r = presenca(cliente, a["id"], "PRESENTE")
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "TURMA_NAO_INICIADA"
    else:
        assert r.json()["situacao"] == "PRESENTE"


def test_rn_04_fila_por_ordem_de_chegada(cliente):
    turma = criar_turma(cliente, vagas=1)
    a = inscrever(cliente, turma["id"], 1).json()
    b = inscrever(cliente, turma["id"], 2).json()
    c = inscrever(cliente, turma["id"], 3).json()
    assert (b["posicao_espera"], c["posicao_espera"]) == (1, 2)
    lista = cliente.get(f"/api/turmas/{turma['id']}/inscricoes").json()
    assert [i["id"] for i in lista] == [a["id"], b["id"], c["id"]]
    assert [i["posicao_espera"] for i in lista] == [None, 1, 2]


def test_rn_05_email_sem_diferenciar_maiusculas(cliente):
    turma = criar_turma(cliente)
    r1 = inscrever(cliente, turma["id"], email="Ana@Exemplo.test")
    assert r1.status_code == 201
    assert r1.json()["email"] == "ana@exemplo.test"
    r2 = inscrever(cliente, turma["id"], email="ana@exemplo.test")
    assert r2.status_code == 409
    assert r2.json()["erro"] == "INSCRICAO_DUPLICADA"


def test_rn_05_reinscricao_apos_cancelar(cliente):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"], email="bia@exemplo.test").json()
    assert cancelar(cliente, a["id"]).status_code == 200
    r = inscrever(cliente, turma["id"], email="bia@exemplo.test")
    assert r.status_code == 201
    assert r.json()["situacao"] == "CONFIRMADA"


def test_rn_05_mesmo_email_outra_turma(cliente):
    t1 = criar_turma(cliente)
    t2 = criar_turma(cliente)
    assert inscrever(cliente, t1["id"], email="caio@exemplo.test").status_code == 201
    assert inscrever(cliente, t2["id"], email="caio@exemplo.test").status_code == 201


def test_rn_08_cancelar_duas_vezes(cliente):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"]).json()
    assert cancelar(cliente, a["id"]).status_code == 200
    r = cancelar(cliente, a["id"])
    assert r.status_code == 409
    assert r.json()["erro"] == "SITUACAO_NAO_CANCELAVEL"


def test_rn_09_cancelar_espera_nao_promove(cliente):
    turma = criar_turma(cliente, vagas=1)
    a = inscrever(cliente, turma["id"], 1).json()
    b = inscrever(cliente, turma["id"], 2).json()
    r = cancelar(cliente, b["id"])
    assert r.status_code == 200
    assert r.json()["inscricao"]["situacao"] == "CANCELADA"
    assert r.json()["promovida"] is None
    assert inscritos(cliente, turma["id"])[a["id"]]["situacao"] == "CONFIRMADA"


def test_rn_09_promocao_dentro_das_24h(cliente, relogio):
    turma = criar_turma(cliente, vagas=1)
    a = inscrever(cliente, turma["id"], 1).json()
    b = inscrever(cliente, turma["id"], 2).json()
    ir_para(relogio, INICIO_PADRAO - timedelta(hours=2))
    r = cancelar(cliente, a["id"])
    assert r.status_code == 200
    assert r.json()["promovida"]["id"] == b["id"]
    assert r.json()["promovida"]["situacao"] == "CONFIRMADA"


def test_rn_09_sem_fila_nao_promove(cliente):
    turma = criar_turma(cliente, vagas=2)
    a = inscrever(cliente, turma["id"]).json()
    r = cancelar(cliente, a["id"])
    assert r.json()["promovida"] is None
    assert cliente.get(f"/api/turmas/{turma['id']}").json()["vagas_restantes"] == 2


def test_rn_11_presenca_definitiva(cliente, relogio):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"]).json()
    ir_para(relogio, INICIO_PADRAO + timedelta(hours=1))
    assert presenca(cliente, a["id"], "PRESENTE").status_code == 200
    r = presenca(cliente, a["id"], "AUSENTE")
    assert r.status_code == 409
    assert r.json()["erro"] == "SITUACAO_SEM_PRESENCA"


def test_rn_11_presenca_de_cancelada_recusada(cliente, relogio):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"]).json()
    cancelar(cliente, a["id"])
    ir_para(relogio, INICIO_PADRAO + timedelta(hours=1))
    r = presenca(cliente, a["id"], "AUSENTE")
    assert r.status_code == 409
    assert r.json()["erro"] == "SITUACAO_SEM_PRESENCA"


@pytest.mark.parametrize("valor", ["CANCELADA", "CONFIRMADA", "presente", ""])
def test_rn_11_presenca_valor_invalido(cliente, relogio, valor):
    turma = criar_turma(cliente)
    a = inscrever(cliente, turma["id"]).json()
    ir_para(relogio, INICIO_PADRAO + timedelta(hours=1))
    assert presenca(cliente, a["id"], valor).status_code == 422


def test_rn_12_taxa_sem_marcacao_vazia(cliente):
    turma = criar_turma(cliente)
    r = cliente.get(f"/api/turmas/{turma['id']}/relatorio-presenca")
    assert r.status_code == 200
    assert r.json() == {"turma_id": turma["id"], "presentes": 0, "ausentes": 0, "taxa_presenca_percentual": None}


def test_rn_12_taxa_arredondada(cliente, relogio):
    turma = criar_turma(cliente, vagas=3)
    ids = [inscrever(cliente, turma["id"], n).json()["id"] for n in range(1, 4)]
    ir_para(relogio, INICIO_PADRAO + timedelta(hours=1))
    for i, situacao in zip(ids, ["PRESENTE", "PRESENTE", "AUSENTE"]):
        presenca(cliente, i, situacao)
    assert cliente.get(f"/api/turmas/{turma['id']}/relatorio-presenca").json()["taxa_presenca_percentual"] == 66.67


def test_rn_13_vagas_restantes_contam_presenca(cliente, relogio):
    turma = criar_turma(cliente, vagas=2)
    a = inscrever(cliente, turma["id"], 1).json()
    b = inscrever(cliente, turma["id"], 2).json()
    ir_para(relogio, INICIO_PADRAO + timedelta(hours=1))
    presenca(cliente, a["id"], "PRESENTE")
    presenca(cliente, b["id"], "AUSENTE")
    assert cliente.get(f"/api/turmas/{turma['id']}").json()["vagas_restantes"] == 0


def test_rn_14_turma_passada_fora_da_lista(cliente, relogio):
    turma = criar_turma(cliente)
    ids = [t["id"] for t in cliente.get("/api/turmas").json()]
    assert turma["id"] in ids
    ir_para(relogio, INICIO_PADRAO + timedelta(minutes=1))
    ids = [t["id"] for t in cliente.get("/api/turmas").json()]
    assert turma["id"] not in ids
    assert cliente.get(f"/api/turmas/{turma['id']}").status_code == 200


def test_pr_04_inicio_no_passado_recusado(cliente):
    r = cliente.post("/api/turmas", json=_corpo_turma(inicio=AGORA_INICIAL.isoformat()))
    assert r.status_code == 422
    assert r.json()["erro"] == "INICIO_NO_PASSADO"


def test_rf_03_carga_inicial_tres_turmas_futuras(cliente):
    turmas = cliente.get("/api/turmas").json()
    assert len(turmas) == 3
    assert {t["modalidade"] for t in turmas} <= {"PRESENCIAL", "ONLINE"}
    from datetime import datetime
    assert all(datetime.fromisoformat(t["inicio"]) > AGORA_INICIAL for t in turmas)
    assert all(t["vagas_restantes"] == t["vagas"] for t in turmas)


def test_rf_05_lista_inscritos(cliente):
    turma = criar_turma(cliente)
    inscrever(cliente, turma["id"], 1, nome="Ana Teste")
    inscrever(cliente, turma["id"], 2, nome="Bruno Teste")
    r = cliente.get(f"/api/turmas/{turma['id']}/inscricoes")
    assert r.status_code == 200
    assert [i["nome"] for i in r.json()] == ["Ana Teste", "Bruno Teste"]
    assert all(i["turma_id"] == turma["id"] for i in r.json())


def test_rf_01_turma_criada_e_consultada(cliente):
    turma = criar_turma(cliente, vagas=7, titulo="Oratória", modalidade="PRESENCIAL")
    r = cliente.get(f"/api/turmas/{turma['id']}")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["titulo"] == "Oratória"
    assert corpo["modalidade"] == "PRESENCIAL"
    assert corpo["inicio"] == INICIO_PADRAO.isoformat()
    assert corpo["vagas_restantes"] == 7


def test_inexistentes_404(cliente):
    assert cliente.get("/api/turmas/9999").json()["erro"] == "TURMA_NAO_ENCONTRADA"
    assert cliente.get("/api/turmas/9999").status_code == 404
    assert cliente.get("/api/turmas/9999/inscricoes").status_code == 404
    assert cliente.get("/api/turmas/9999/relatorio-presenca").status_code == 404
    r = inscrever(cliente, 9999)
    assert (r.status_code, r.json()["erro"]) == (404, "TURMA_NAO_ENCONTRADA")
    r = cancelar(cliente, 9999)
    assert (r.status_code, r.json()["erro"]) == (404, "INSCRICAO_NAO_ENCONTRADA")
    r = presenca(cliente, 9999, "PRESENTE")
    assert (r.status_code, r.json()["erro"]) == (404, "INSCRICAO_NAO_ENCONTRADA")


@pytest.mark.parametrize("inicio", ["2030-01-10T09:00:00", "10/01/2030 09:00", "9999-01-10T09:00:00-03:00"])
def test_inicio_sem_fuso_recusado(cliente, inicio):
    assert cliente.post("/api/turmas", json=_corpo_turma(inicio=inicio)).status_code == 422


@pytest.mark.parametrize("campo, valor", [
    ("modalidade", "HIBRIDA"), ("vagas", "dez"), ("vagas", 99999999999999999999), ("titulo", "   "),
    ("vagas", True), ("duracao_minutos", False), ("vagas", 1.5), ("vagas", "10"),
])
def test_turma_formato_invalido(cliente, campo, valor):
    assert cliente.post("/api/turmas", json=_corpo_turma(**{campo: valor})).status_code == 422


@pytest.mark.parametrize("email", ["sem-arroba", "a@b", "", "   "])
def test_inscricao_email_invalido(cliente, email):
    turma = criar_turma(cliente)
    assert inscrever(cliente, turma["id"], email=email).status_code == 422


@pytest.mark.parametrize("turma_id", [True, "1", 1.0, 0, 99999999999999999999])
def test_inscricao_turma_id_tipo_errado(cliente, turma_id):
    assert cliente.post("/api/inscricoes", json={"turma_id": turma_id, "nome": "N",
                                                 "email": "n@exemplo.test"}).status_code == 422
