"""Um teste por critério de aceite do pedido. Relógio: 2030-01-07 (início mínimo 2030-02-06)."""

from tests.apoio import acao, colaborador, criar_solicitacao, solicitar


def test_ca_01_solicitar_10_dias_com_40_de_antecedencia(cliente):
    # 2030-01-07 + 40 dias = 2030-02-16
    r = solicitar(cliente, 1, "2030-02-16", "2030-02-25")
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["situacao"] == "SOLICITADA"
    assert corpo["dias"] == 10
    assert corpo["inicio"] == "2030-02-16" and corpo["fim"] == "2030-02-25"


def test_ca_02_recusa_4_dias(cliente):
    r = solicitar(cliente, 1, "2030-03-01", "2030-03-04")
    assert r.status_code == 422
    assert r.json()["erro"] == "DURACAO_INVALIDA"


def test_ca_03_recusa_inicio_em_29_dias(cliente):
    r = solicitar(cliente, 1, "2030-02-05", "2030-02-14")
    assert r.status_code == 422
    assert r.json()["erro"] == "ANTECEDENCIA_INSUFICIENTE"


def test_ca_04_recusa_mais_dias_que_saldo_disponivel(cliente):
    criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-20")  # 20 dias pendentes
    r = solicitar(cliente, 1, "2030-04-01", "2030-04-15")  # 15 > 10 disponíveis
    assert r.status_code == 422
    assert r.json()["erro"] == "SALDO_INSUFICIENTE"
    assert colaborador(cliente, 1)["saldo_disponivel"] == 10


def test_ca_05_aprovar_reduz_saldo(cliente):
    s = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    r = acao(cliente, s["id"], "aprovar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "APROVADA"
    c = colaborador(cliente, 1)
    assert c["saldo"] == 20
    assert c["saldo_disponivel"] == 20


def test_ca_06_recusa_segunda_aprovacao_mesma_equipe(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    b = criar_solicitacao(cliente, 2, "2030-03-05", "2030-03-14")
    assert acao(cliente, a["id"], "aprovar").status_code == 200
    r = acao(cliente, b["id"], "aprovar")
    assert r.status_code == 409
    assert r.json()["erro"] == "LIMITE_EQUIPE"
    situacoes = {s["id"]: s["situacao"] for s in cliente.get("/api/solicitacoes").json()}
    assert situacoes[b["id"]] == "SOLICITADA"
    assert colaborador(cliente, 2)["saldo"] == 30


def test_ca_07_aprova_outra_equipe_mesmo_periodo(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")  # DADOS
    b = criar_solicitacao(cliente, 4, "2030-03-01", "2030-03-10")  # PRODUTO
    assert acao(cliente, a["id"], "aprovar").json()["situacao"] == "APROVADA"
    r = acao(cliente, b["id"], "aprovar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "APROVADA"


def test_ca_08_aprova_mesma_equipe_dia_seguinte_ao_fim(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    b = criar_solicitacao(cliente, 2, "2030-03-11", "2030-03-20")
    assert acao(cliente, a["id"], "aprovar").status_code == 200
    r = acao(cliente, b["id"], "aprovar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "APROVADA"


def test_ca_09_cancelar_aprovada_devolve_saldo(cliente):
    s = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    acao(cliente, s["id"], "aprovar")
    assert colaborador(cliente, 1)["saldo"] == 20
    r = acao(cliente, s["id"], "cancelar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "CANCELADA"
    c = colaborador(cliente, 1)
    assert c["saldo"] == 30
    assert c["saldo_disponivel"] == 30


def test_ca_10_calendario_so_mostra_aprovadas(cliente):
    aprovada = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    criar_solicitacao(cliente, 4, "2030-03-01", "2030-03-10")  # fica SOLICITADA
    reprovada = criar_solicitacao(cliente, 7, "2030-03-01", "2030-03-10")
    acao(cliente, aprovada["id"], "aprovar")
    acao(cliente, reprovada["id"], "reprovar")

    r = cliente.get("/api/calendario", params={"mes": "2030-03"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["mes"] == "2030-03"
    assert len(corpo["dias"]) == 31
    nomes = {p["nome"] for d in corpo["dias"] for eq in d["equipes"].values() for p in eq}
    assert nomes == {"Ana Ribeiro"}
    dia1 = corpo["dias"][0]
    assert dia1["data"] == "2030-03-01"
    assert [p["nome"] for p in dia1["equipes"]["DADOS"]] == ["Ana Ribeiro"]
    assert dia1["equipes"]["PRODUTO"] == [] and dia1["equipes"]["SUPORTE"] == []
    assert corpo["dias"][10]["equipes"]["DADOS"] == []  # 2030-03-11, já terminou
