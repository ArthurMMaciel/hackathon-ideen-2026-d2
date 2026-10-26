"""Testes do plano da SPEC. Relógio de teste: 2030-01-07 (hoje); +30 dias = 2030-02-06; +40 dias = 2030-02-16."""

from datetime import date, timedelta
from itertools import count

import pytest

HOJE = date(2030, 1, 7)
_seq = count(1)


def criar_colaborador(cliente, equipe="DADOS", saldo=None, nome=None):
    n = next(_seq)
    corpo = {"nome": nome or f"Pessoa Teste {n}", "email": f"pessoa{n}@exemplo.com", "equipe": equipe}
    if saldo is not None:
        corpo["saldo"] = saldo
    r = cliente.post("/api/colaboradores", json=corpo)
    assert r.status_code == 201, r.text
    return r.json()


def solicitar(cliente, colaborador_id, inicio, fim):
    return cliente.post(
        "/api/solicitacoes",
        json={"colaborador_id": colaborador_id, "inicio": str(inicio), "fim": str(fim)},
    )


def periodo(antecedencia, dias):
    inicio = HOJE + timedelta(days=antecedencia)
    return inicio, inicio + timedelta(days=dias - 1)


def solicitar_ok(cliente, colaborador_id, inicio, fim):
    r = solicitar(cliente, colaborador_id, inicio, fim)
    assert r.status_code == 201, r.text
    return r.json()


def aprovar(cliente, sid):
    return cliente.post(f"/api/solicitacoes/{sid}/aprovar")


def colaborador(cliente, cid):
    r = cliente.get(f"/api/colaboradores/{cid}")
    assert r.status_code == 200, r.text
    return r.json()


A_INICIO, A_FIM = date(2030, 2, 16), date(2030, 2, 25)


# ---------- Critérios de aceite ----------

def test_ca_01_solicitar_10_dias_com_40_de_antecedencia(cliente):
    c = criar_colaborador(cliente)
    r = solicitar(cliente, c["id"], A_INICIO, A_FIM)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["situacao"] == "SOLICITADA"
    assert corpo["dias"] == 10
    assert corpo["inicio"] == "2030-02-16" and corpo["fim"] == "2030-02-25"


def test_ca_02_solicitar_4_dias_recusado(cliente):
    c = criar_colaborador(cliente)
    r = solicitar(cliente, c["id"], date(2030, 2, 16), date(2030, 2, 19))
    assert r.status_code == 422
    assert r.json()["erro"] == "DURACAO_INVALIDA"


def test_ca_03_inicio_em_29_dias_recusado(cliente):
    c = criar_colaborador(cliente)
    r = solicitar(cliente, c["id"], date(2030, 2, 5), date(2030, 2, 14))
    assert r.status_code == 422
    assert r.json()["erro"] == "ANTECEDENCIA_INSUFICIENTE"


def test_ca_04_mais_dias_que_saldo_disponivel_recusado(cliente):
    c = criar_colaborador(cliente, saldo=30)
    solicitar_ok(cliente, c["id"], date(2030, 2, 16), date(2030, 3, 12))  # 25 dias pendentes
    r = solicitar(cliente, c["id"], date(2030, 4, 1), date(2030, 4, 10))  # 10 > 5 disponíveis
    assert r.status_code == 409
    assert r.json()["erro"] == "SALDO_INSUFICIENTE"
    assert colaborador(cliente, c["id"])["saldo_disponivel"] == 5


def test_ca_05_aprovar_reduz_saldo(cliente):
    c = criar_colaborador(cliente)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    r = aprovar(cliente, s["id"])
    assert r.status_code == 200
    assert r.json()["situacao"] == "APROVADA"
    dados = colaborador(cliente, c["id"])
    assert dados["saldo"] == 20
    assert dados["saldo_disponivel"] == 20


def test_ca_06_aprovar_segunda_pessoa_mesma_equipe_recusado(cliente):
    a = criar_colaborador(cliente, "DADOS")
    b = criar_colaborador(cliente, "DADOS")
    sa = solicitar_ok(cliente, a["id"], A_INICIO, A_FIM)
    sb = solicitar_ok(cliente, b["id"], date(2030, 2, 20), date(2030, 3, 1))
    assert aprovar(cliente, sa["id"]).status_code == 200
    r = aprovar(cliente, sb["id"])
    assert r.status_code == 409
    assert r.json()["erro"] == "LIMITE_EQUIPE"
    assert cliente.get(f"/api/solicitacoes/{sb['id']}").json()["situacao"] == "SOLICITADA"
    assert colaborador(cliente, b["id"])["saldo"] == 30


def test_ca_07_aprovar_outra_equipe_mesmo_periodo(cliente):
    a = criar_colaborador(cliente, "DADOS")
    c = criar_colaborador(cliente, "PRODUTO")
    sa = solicitar_ok(cliente, a["id"], A_INICIO, A_FIM)
    sc = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert aprovar(cliente, sa["id"]).status_code == 200
    r = aprovar(cliente, sc["id"])
    assert r.status_code == 200
    assert r.json()["situacao"] == "APROVADA"


def test_ca_08_mesma_equipe_comecando_no_dia_seguinte(cliente):
    a = criar_colaborador(cliente, "SUPORTE")
    b = criar_colaborador(cliente, "SUPORTE")
    sa = solicitar_ok(cliente, a["id"], A_INICIO, A_FIM)
    sb = solicitar_ok(cliente, b["id"], date(2030, 2, 26), date(2030, 3, 7))
    assert aprovar(cliente, sa["id"]).status_code == 200
    r = aprovar(cliente, sb["id"])
    assert r.status_code == 200
    assert r.json()["situacao"] == "APROVADA"


def test_ca_09_cancelar_aprovada_devolve_saldo(cliente):
    c = criar_colaborador(cliente)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert aprovar(cliente, s["id"]).status_code == 200
    assert colaborador(cliente, c["id"])["saldo"] == 20
    r = cliente.post(f"/api/solicitacoes/{s['id']}/cancelar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "CANCELADA"
    assert colaborador(cliente, c["id"])["saldo"] == 30


def test_ca_10_calendario_mostra_so_aprovadas(cliente):
    a = criar_colaborador(cliente, "DADOS", nome="Pessoa Aprovada")
    b = criar_colaborador(cliente, "PRODUTO", nome="Pessoa Solicitada")
    c = criar_colaborador(cliente, "SUPORTE", nome="Pessoa Reprovada")
    sa = solicitar_ok(cliente, a["id"], A_INICIO, A_FIM)
    solicitar_ok(cliente, b["id"], A_INICIO, A_FIM)
    sc = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert aprovar(cliente, sa["id"]).status_code == 200
    assert cliente.post(f"/api/solicitacoes/{sc['id']}/reprovar").status_code == 200

    r = cliente.get("/api/calendario", params={"mes": "2030-02"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["mes"] == "2030-02"
    assert len(corpo["dias"]) == 28
    por_dia = {d["data"]: d["equipes"] for d in corpo["dias"]}
    dia = por_dia["2030-02-16"]
    assert [p["nome"] for p in dia["DADOS"]] == ["Pessoa Aprovada"]
    assert dia["PRODUTO"] == [] and dia["SUPORTE"] == []
    assert por_dia["2030-02-15"] == {"DADOS": [], "PRODUTO": [], "SUPORTE": []}
    nomes = {p["nome"] for eq in por_dia.values() for lista in eq.values() for p in lista}
    assert nomes == {"Pessoa Aprovada"}


# ---------- Regras de negócio ----------

def test_rn_01_fim_antes_do_inicio_recusado(cliente):
    c = criar_colaborador(cliente)
    r = solicitar(cliente, c["id"], date(2030, 2, 20), date(2030, 2, 16))
    assert r.status_code == 422
    assert r.json()["erro"] == "PERIODO_INVALIDO"


@pytest.mark.parametrize("dias,status", [(4, 422), (5, 201), (30, 201), (31, 422)])
def test_rn_02_bordas_da_duracao(cliente, dias, status):
    c = criar_colaborador(cliente, saldo=60)
    r = solicitar(cliente, c["id"], *periodo(40, dias))
    assert r.status_code == status
    if status == 201:
        assert r.json()["dias"] == dias
    else:
        assert r.json()["erro"] == "DURACAO_INVALIDA"


@pytest.mark.parametrize("antecedencia,status", [(29, 422), (30, 201), (31, 201)])
def test_rn_03_bordas_da_antecedencia(cliente, antecedencia, status):
    c = criar_colaborador(cliente)
    r = solicitar(cliente, c["id"], *periodo(antecedencia, 10))
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "ANTECEDENCIA_INSUFICIENTE"


def test_rn_04_bordas_do_saldo_disponivel(cliente):
    c = criar_colaborador(cliente, saldo=12)
    solicitar_ok(cliente, c["id"], *periodo(40, 5))  # disponível 7
    r = solicitar(cliente, c["id"], *periodo(60, 8))
    assert r.status_code == 409
    assert r.json()["erro"] == "SALDO_INSUFICIENTE"
    r = solicitar(cliente, c["id"], *periodo(60, 7))
    assert r.status_code == 201
    assert colaborador(cliente, c["id"])["saldo_disponivel"] == 0


def test_rn_04_aprovada_descontada_uma_vez(cliente):
    c = criar_colaborador(cliente, saldo=30)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert aprovar(cliente, s["id"]).status_code == 200
    r = solicitar(cliente, c["id"], *periodo(100, 20))
    assert r.status_code == 201
    dados = colaborador(cliente, c["id"])
    assert dados["saldo"] == 20 and dados["saldo_disponivel"] == 0


def test_rn_05_sobreposicao_do_mesmo_colaborador(cliente):
    c = criar_colaborador(cliente, saldo=60)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    r = solicitar(cliente, c["id"], A_FIM, A_FIM + timedelta(days=5))  # 1 dia em comum
    assert r.status_code == 409
    assert r.json()["erro"] == "SOBREPOSICAO"
    r = solicitar(cliente, c["id"], A_FIM + timedelta(days=1), A_FIM + timedelta(days=5))
    assert r.status_code == 201
    assert cliente.post(f"/api/solicitacoes/{s['id']}/cancelar").status_code == 200
    r = solicitar(cliente, c["id"], A_INICIO, A_FIM)
    assert r.status_code == 201


def test_rn_05_sobreposicao_com_aprovada(cliente):
    c = criar_colaborador(cliente, saldo=60)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert aprovar(cliente, s["id"]).status_code == 200
    r = solicitar(cliente, c["id"], A_INICIO - timedelta(days=4), A_INICIO)
    assert r.status_code == 409
    assert r.json()["erro"] == "SOBREPOSICAO"


def test_rn_06_so_solicitada_pode_ser_decidida(cliente):
    c = criar_colaborador(cliente)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    r = cliente.post(f"/api/solicitacoes/{s['id']}/reprovar")
    assert r.status_code == 200 and r.json()["situacao"] == "REPROVADA"
    assert colaborador(cliente, c["id"])["saldo"] == 30
    r = aprovar(cliente, s["id"])
    assert r.status_code == 409 and r.json()["erro"] == "TRANSICAO_INVALIDA"

    s2 = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert aprovar(cliente, s2["id"]).status_code == 200
    r = cliente.post(f"/api/solicitacoes/{s2['id']}/reprovar")
    assert r.status_code == 409 and r.json()["erro"] == "TRANSICAO_INVALIDA"
    r = aprovar(cliente, s2["id"])
    assert r.status_code == 409 and r.json()["erro"] == "TRANSICAO_INVALIDA"
    assert colaborador(cliente, c["id"])["saldo"] == 20


def test_rn_07_limite_equipe_um_dia_em_comum(cliente):
    a = criar_colaborador(cliente, "PRODUTO")
    b = criar_colaborador(cliente, "PRODUTO")
    sa = solicitar_ok(cliente, a["id"], A_INICIO, A_FIM)
    sb = solicitar_ok(cliente, b["id"], A_FIM, A_FIM + timedelta(days=4))
    assert aprovar(cliente, sa["id"]).status_code == 200
    r = aprovar(cliente, sb["id"])
    assert r.status_code == 409
    assert r.json()["erro"] == "LIMITE_EQUIPE"


def test_rn_07_cancelada_libera_a_equipe(cliente):
    a = criar_colaborador(cliente, "DADOS")
    b = criar_colaborador(cliente, "DADOS")
    sa = solicitar_ok(cliente, a["id"], A_INICIO, A_FIM)
    sb = solicitar_ok(cliente, b["id"], A_INICIO, A_FIM)
    assert aprovar(cliente, sa["id"]).status_code == 200
    assert cliente.post(f"/api/solicitacoes/{sa['id']}/cancelar").status_code == 200
    assert aprovar(cliente, sb["id"]).status_code == 200


@pytest.mark.parametrize("avanco,status", [(39, 200), (40, 422), (41, 422)])
def test_rn_09_bordas_do_cancelamento(cliente, relogio, avanco, status):
    c = criar_colaborador(cliente)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)  # início 2030-02-16
    assert aprovar(cliente, s["id"]).status_code == 200
    relogio.avancar(days=avanco)  # 39 → 2030-02-15 (véspera); 40 → dia do início
    r = cliente.post(f"/api/solicitacoes/{s['id']}/cancelar")
    assert r.status_code == status
    if status == 200:
        assert r.json()["situacao"] == "CANCELADA"
        assert colaborador(cliente, c["id"])["saldo"] == 30
    else:
        assert r.json()["erro"] == "CANCELAMENTO_FORA_DO_PRAZO"
        assert colaborador(cliente, c["id"])["saldo"] == 20


def test_rn_09_cancelar_finalizada_recusado(cliente):
    c = criar_colaborador(cliente)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert cliente.post(f"/api/solicitacoes/{s['id']}/cancelar").status_code == 200
    r = cliente.post(f"/api/solicitacoes/{s['id']}/cancelar")
    assert r.status_code == 409 and r.json()["erro"] == "TRANSICAO_INVALIDA"
    s2 = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert cliente.post(f"/api/solicitacoes/{s2['id']}/reprovar").status_code == 200
    r = cliente.post(f"/api/solicitacoes/{s2['id']}/cancelar")
    assert r.status_code == 409 and r.json()["erro"] == "TRANSICAO_INVALIDA"


def test_rn_10_cancelar_solicitada_nao_mexe_no_saldo(cliente):
    c = criar_colaborador(cliente)
    s = solicitar_ok(cliente, c["id"], A_INICIO, A_FIM)
    assert colaborador(cliente, c["id"])["saldo_disponivel"] == 20
    r = cliente.post(f"/api/solicitacoes/{s['id']}/cancelar")
    assert r.status_code == 200
    dados = colaborador(cliente, c["id"])
    assert dados["saldo"] == 30 and dados["saldo_disponivel"] == 30


@pytest.mark.parametrize("saldo,status", [(-1, 422), (0, 201), (365, 201), (366, 422)])
def test_rn_11_bordas_do_saldo_inicial(cliente, saldo, status):
    r = cliente.post(
        "/api/colaboradores",
        json={"nome": "Pessoa Saldo", "email": f"saldo{saldo}@exemplo.com", "equipe": "DADOS", "saldo": saldo},
    )
    assert r.status_code == status
    if status == 201:
        assert r.json()["saldo"] == saldo


def test_rn_11_saldo_padrao_30(cliente):
    r = cliente.post("/api/colaboradores", json={"nome": "Pessoa Padrao", "email": "padrao@exemplo.com", "equipe": "SUPORTE"})
    assert r.status_code == 201
    assert r.json()["saldo"] == 30 and r.json()["saldo_disponivel"] == 30


def test_rn_11_email_duplicado_e_equipe_invalida(cliente):
    corpo = {"nome": "Pessoa Um", "email": "repetido@exemplo.com", "equipe": "DADOS"}
    assert cliente.post("/api/colaboradores", json=corpo).status_code == 201
    r = cliente.post("/api/colaboradores", json={**corpo, "email": "REPETIDO@exemplo.com"})
    assert r.status_code == 409 and r.json()["erro"] == "EMAIL_DUPLICADO"
    r = cliente.post("/api/colaboradores", json={**corpo, "email": "outro@exemplo.com", "equipe": "RH"})
    assert r.status_code == 422
    r = cliente.post("/api/colaboradores", json={**corpo, "email": "sem-arroba"})
    assert r.status_code == 422


# ---------- Requisitos funcionais ----------

def test_rf_03_carga_inicial_9_colaboradores_3_por_equipe(cliente):
    r = cliente.get("/api/colaboradores")
    assert r.status_code == 200
    lista = r.json()
    assert len(lista) == 9
    for equipe in ("DADOS", "PRODUTO", "SUPORTE"):
        assert sum(1 for c in lista if c["equipe"] == equipe) == 3
    assert all(c["saldo"] == 30 and c["saldo_disponivel"] == 30 for c in lista)


def test_rf_05_listar_e_consultar_solicitacoes(cliente):
    c = criar_colaborador(cliente, saldo=60)
    s2 = solicitar_ok(cliente, c["id"], *periodo(80, 5))
    s1 = solicitar_ok(cliente, c["id"], *periodo(40, 5))
    lista = cliente.get("/api/solicitacoes").json()
    ids = [s["id"] for s in lista]
    assert ids.index(s1["id"]) < ids.index(s2["id"])
    r = cliente.get(f"/api/solicitacoes/{s1['id']}")
    assert r.status_code == 200
    assert r.json()["colaborador_nome"] == c["nome"] and r.json()["equipe"] == c["equipe"]


def test_rf_02_e_rf_05_inexistente_404(cliente):
    r = cliente.get("/api/colaboradores/999999")
    assert r.status_code == 404 and r.json()["erro"] == "COLABORADOR_NAO_ENCONTRADO"
    r = solicitar(cliente, 999999, A_INICIO, A_FIM)
    assert r.status_code == 404 and r.json()["erro"] == "COLABORADOR_NAO_ENCONTRADO"
    r = cliente.get("/api/solicitacoes/999999")
    assert r.status_code == 404 and r.json()["erro"] == "SOLICITACAO_NAO_ENCONTRADA"
    for acao in ("aprovar", "reprovar", "cancelar"):
        r = cliente.post(f"/api/solicitacoes/999999/{acao}")
        assert r.status_code == 404 and r.json()["erro"] == "SOLICITACAO_NAO_ENCONTRADA"


@pytest.mark.parametrize("mes", ["2030-13", "2030-1", "9999-01", "1999-12", "2030-00", "２０３０-０１"])
def test_rf_09_mes_invalido_recusado(cliente, mes):
    assert cliente.get("/api/calendario", params={"mes": mes}).status_code == 422


def test_rf_09_calendario_mes_com_31_dias(cliente):
    r = cliente.get("/api/calendario", params={"mes": "2030-03"})
    assert r.status_code == 200
    dias = r.json()["dias"]
    assert len(dias) == 31 and dias[0]["data"] == "2030-03-01" and dias[-1]["data"] == "2030-03-31"
