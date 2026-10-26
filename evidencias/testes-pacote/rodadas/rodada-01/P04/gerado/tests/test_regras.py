"""Bordas das regras de negócio e requisitos. Relógio: 2030-01-07 09:00 -03:00."""

import pytest

from tests.apoio import acao, colaborador, criar_solicitacao, novo_colaborador, solicitar


def test_rn_01_fim_antes_do_inicio(cliente):
    r = solicitar(cliente, 1, "2030-03-10", "2030-03-01")
    assert r.status_code == 422
    assert r.json()["erro"] == "PERIODO_INVALIDO"


@pytest.mark.parametrize("fim,status", [("2030-03-04", 422), ("2030-03-05", 201), ("2030-03-30", 201), ("2030-03-31", 422)])
def test_rn_02_bordas_duracao(cliente, fim, status):
    # início 2030-03-01: 4, 5, 30 e 31 dias
    r = solicitar(cliente, 1, "2030-03-01", fim)
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "DURACAO_INVALIDA"
    else:
        assert r.json()["situacao"] == "SOLICITADA"


@pytest.mark.parametrize("inicio,fim,status", [
    ("2030-02-05", "2030-02-09", 422),  # 29 dias
    ("2030-02-06", "2030-02-10", 201),  # 30 dias
    ("2030-02-07", "2030-02-11", 201),  # 31 dias
])
def test_rn_03_bordas_antecedencia(cliente, inicio, fim, status):
    r = solicitar(cliente, 1, inicio, fim)
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "ANTECEDENCIA_INSUFICIENTE"


def test_rn_03_hoje_no_fuso_de_sao_paulo(cliente, relogio):
    # 2030-01-07 23:30 -03:00 já é dia 8 em UTC; "hoje" continua 2030-01-07.
    relogio.avancar(hours=14, minutes=30)
    assert solicitar(cliente, 1, "2030-02-06", "2030-02-10").status_code == 201


@pytest.mark.parametrize("saldo,status", [(9, 422), (10, 201), (11, 201)])
def test_rn_04_bordas_saldo(cliente, saldo, status):
    c = novo_colaborador(cliente, f"saldo{saldo}@exemplo.test", saldo=saldo)
    r = solicitar(cliente, c["id"], "2030-03-01", "2030-03-10")
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "SALDO_INSUFICIENTE"


def test_rn_04_aprovadas_nao_sao_descontadas_duas_vezes(cliente):
    s = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-20")
    acao(cliente, s["id"], "aprovar")
    assert colaborador(cliente, 1)["saldo_disponivel"] == 10
    assert solicitar(cliente, 1, "2030-05-01", "2030-05-10").status_code == 201
    assert solicitar(cliente, 1, "2030-06-01", "2030-06-05").status_code == 422


def test_rn_05_recusa_sobreposicao_mesmo_colaborador(cliente):
    criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    r = solicitar(cliente, 1, "2030-03-10", "2030-03-14")
    assert r.status_code == 409
    assert r.json()["erro"] == "SOBREPOSICAO_COLABORADOR"
    assert solicitar(cliente, 1, "2030-03-11", "2030-03-15").status_code == 201


def test_rn_05_ignora_reprovada_e_cancelada(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    acao(cliente, a["id"], "reprovar")
    b = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    acao(cliente, b["id"], "cancelar")
    assert solicitar(cliente, 1, "2030-03-01", "2030-03-10").status_code == 201


def test_rn_06_so_solicitada_pode_ser_decidida(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    b = criar_solicitacao(cliente, 2, "2030-04-01", "2030-04-10")
    acao(cliente, a["id"], "aprovar")
    acao(cliente, b["id"], "reprovar")
    for sid in (a["id"], b["id"]):
        for nome in ("aprovar", "reprovar"):
            r = acao(cliente, sid, nome)
            assert r.status_code == 409
            assert r.json()["erro"] == "SITUACAO_INVALIDA"
    assert colaborador(cliente, 1)["saldo"] == 20


def test_rn_07_um_dia_em_comum_conflita(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    b = criar_solicitacao(cliente, 2, "2030-03-10", "2030-03-14")
    acao(cliente, a["id"], "aprovar")
    r = acao(cliente, b["id"], "aprovar")
    assert r.status_code == 409
    assert r.json()["erro"] == "LIMITE_EQUIPE"


def test_rn_07_cancelada_libera_a_equipe(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    b = criar_solicitacao(cliente, 2, "2030-03-01", "2030-03-10")
    acao(cliente, a["id"], "aprovar")
    acao(cliente, a["id"], "cancelar")
    assert acao(cliente, b["id"], "aprovar").status_code == 200


def test_rn_09_bordas_cancelamento(cliente, relogio):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    b = criar_solicitacao(cliente, 2, "2030-03-02", "2030-03-11")
    acao(cliente, a["id"], "aprovar")
    relogio.avancar(days=52, hours=14)  # 2030-02-28 23:00, véspera do início de a
    r = acao(cliente, a["id"], "cancelar")
    assert r.status_code == 200 and r.json()["situacao"] == "CANCELADA"
    relogio.avancar(days=2)  # 2030-03-02 23:00, dia do início de b
    r = acao(cliente, b["id"], "cancelar")
    assert r.status_code == 422
    assert r.json()["erro"] == "CANCELAMENTO_FORA_DO_PRAZO"


def test_rn_09_nao_cancela_reprovada_nem_cancelada(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    acao(cliente, a["id"], "reprovar")
    r = acao(cliente, a["id"], "cancelar")
    assert r.status_code == 409 and r.json()["erro"] == "SITUACAO_INVALIDA"
    b = criar_solicitacao(cliente, 1, "2030-04-01", "2030-04-10")
    acao(cliente, b["id"], "cancelar")
    assert acao(cliente, b["id"], "cancelar").status_code == 409


def test_rn_09_cancelar_solicitada_nao_altera_saldo(cliente):
    s = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    assert colaborador(cliente, 1)["saldo_disponivel"] == 20
    r = acao(cliente, s["id"], "cancelar")
    assert r.status_code == 200 and r.json()["situacao"] == "CANCELADA"
    c = colaborador(cliente, 1)
    assert c["saldo"] == 30 and c["saldo_disponivel"] == 30


@pytest.mark.parametrize("saldo,status", [(-1, 422), (0, 201), (365, 201), (366, 422)])
def test_rn_11_bordas_saldo_cadastro(cliente, saldo, status):
    r = cliente.post("/api/colaboradores", json={"nome": "X", "email": f"s{saldo}@exemplo.test", "equipe": "SUPORTE", "saldo": saldo})
    assert r.status_code == status
    if status == 201:
        assert r.json()["saldo"] == saldo


def test_rn_12_email_duplicado_e_invalido(cliente):
    r = cliente.post("/api/colaboradores", json={"nome": "X", "email": "ANA.RIBEIRO@exemplo.test", "equipe": "DADOS"})
    assert r.status_code == 409
    assert r.json()["erro"] == "EMAIL_DUPLICADO"
    r = cliente.post("/api/colaboradores", json={"nome": "X", "email": "sem-arroba", "equipe": "DADOS"})
    assert r.status_code == 422
    r = cliente.post("/api/colaboradores", json={"nome": "", "email": "x@exemplo.test", "equipe": "DADOS"})
    assert r.status_code == 422
    r = cliente.post("/api/colaboradores", json={"nome": "X", "email": "y@exemplo.test", "equipe": "VENDAS"})
    assert r.status_code == 422


def test_rf_01_cadastro_saldo_padrao_30(cliente):
    c = novo_colaborador(cliente, "nova@exemplo.test", equipe="PRODUTO")
    assert c["saldo"] == 30 and c["saldo_disponivel"] == 30 and c["equipe"] == "PRODUTO"
    assert any(x["id"] == c["id"] for x in cliente.get("/api/colaboradores").json())


def test_rf_03_carga_inicial_9_colaboradores(cliente):
    lista = cliente.get("/api/colaboradores").json()
    assert len(lista) == 9
    for equipe in ("DADOS", "PRODUTO", "SUPORTE"):
        assert sum(1 for c in lista if c["equipe"] == equipe) == 3
    assert all(c["saldo"] == 30 for c in lista)


def test_rf_03_carga_inicial_idempotente(tmp_path):
    from app import banco
    caminho = str(tmp_path / "x.db")
    banco.iniciar(caminho)
    banco.iniciar(caminho)
    conn = banco.conectar(caminho)
    assert conn.execute("SELECT COUNT(*) FROM colaboradores").fetchone()[0] == 9
    conn.close()


def test_rf_05_filtros_listagem(cliente):
    a = criar_solicitacao(cliente, 1, "2030-03-01", "2030-03-10")
    criar_solicitacao(cliente, 4, "2030-02-10", "2030-02-20")
    acao(cliente, a["id"], "aprovar")
    todas = cliente.get("/api/solicitacoes").json()
    assert [s["inicio"] for s in todas] == ["2030-02-10", "2030-03-01"]
    aprovadas = cliente.get("/api/solicitacoes", params={"situacao": "APROVADA"}).json()
    assert [s["id"] for s in aprovadas] == [a["id"]]
    do4 = cliente.get("/api/solicitacoes", params={"colaborador_id": 4}).json()
    assert len(do4) == 1 and do4[0]["colaborador_id"] == 4 and do4[0]["equipe"] == "PRODUTO"
    assert cliente.get("/api/solicitacoes", params={"situacao": "OUTRA"}).status_code == 422


@pytest.mark.parametrize("mes", ["2030-13", "abc", "2030-1", "2030-00"])
def test_rf_09_mes_invalido(cliente, mes):
    r = cliente.get("/api/calendario", params={"mes": mes})
    assert r.status_code == 422
    assert r.json()["erro"] == "MES_INVALIDO"


def test_rf_09_calendario_fevereiro_e_ferias_entre_meses(cliente):
    s = criar_solicitacao(cliente, 7, "2030-02-25", "2030-03-06")
    acao(cliente, s["id"], "aprovar")
    fev = cliente.get("/api/calendario", params={"mes": "2030-02"}).json()["dias"]
    assert len(fev) == 28
    assert [p["nome"] for p in fev[24]["equipes"]["SUPORTE"]] == ["Gabriela Souto"]
    mar = cliente.get("/api/calendario", params={"mes": "2030-03"}).json()["dias"]
    assert mar[5]["equipes"]["SUPORTE"] and not mar[6]["equipes"]["SUPORTE"]


def test_erros_404(cliente):
    r = cliente.get("/api/colaboradores/999")
    assert r.status_code == 404 and r.json()["erro"] == "COLABORADOR_NAO_ENCONTRADO"
    r = solicitar(cliente, 999, "2030-03-01", "2030-03-10")
    assert r.status_code == 404 and r.json()["erro"] == "COLABORADOR_NAO_ENCONTRADO"
    for nome in ("aprovar", "reprovar", "cancelar"):
        r = acao(cliente, 999, nome)
        assert r.status_code == 404 and r.json()["erro"] == "SOLICITACAO_NAO_ENCONTRADA"


def test_entradas_invalidas_retornam_422(cliente):
    assert cliente.post("/api/solicitacoes", json={"colaborador_id": 1, "inicio": "2030-03-01"}).status_code == 422
    assert cliente.post("/api/solicitacoes", json={"colaborador_id": "x", "inicio": "2030-03-01", "fim": "2030-03-10"}).status_code == 422
    assert solicitar(cliente, 1, "01/03/2030", "2030-03-10").status_code == 422
    assert solicitar(cliente, 1, "2030-03-01T10:00:00", "2030-03-10").status_code == 422
    assert cliente.post("/api/solicitacoes/abc/aprovar").status_code == 422


def test_ids_enormes_nao_causam_erro_500(cliente):
    enorme = 99999999999999999999
    assert cliente.get(f"/api/colaboradores/{enorme}").status_code == 422
    assert cliente.post(f"/api/solicitacoes/{enorme}/aprovar").status_code == 422
    assert cliente.post(f"/api/solicitacoes/{enorme}/cancelar").status_code == 422
    assert cliente.get("/api/solicitacoes", params={"colaborador_id": enorme}).status_code == 422
    assert solicitar(cliente, enorme, "2030-03-01", "2030-03-10").status_code == 422


def test_data_inexistente_retorna_422(cliente):
    assert solicitar(cliente, 1, "2030-02-30", "2030-03-10").status_code == 422
