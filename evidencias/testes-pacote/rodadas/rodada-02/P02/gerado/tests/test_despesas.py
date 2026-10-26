"""Testes do plano da SPEC. Relógio padrão: 2030-01-07 09:00 -03:00 (hoje = 2030-01-07)."""

from datetime import date, timedelta

import pytest

HOJE = date(2030, 1, 7)
LIMITES = {"ALIMENTACAO": 12000, "HOSPEDAGEM": 45000, "TRANSPORTE": 100000, "OUTROS": 100000}

_contador = {"n": 0}


def despesa(**campos) -> dict:
    """Despesa válida com comprovante único; campos sobrescrevem a base."""
    _contador["n"] += 1
    base = {
        "colaborador_nome": "Diego Teste",
        "colaborador_email": "diego.teste@empresa.example",
        "data": "2030-01-05",
        "categoria": "TRANSPORTE",
        "valor_centavos": 5000,
        "descricao": "Uber até o cliente",
        "comprovante": f"T-{_contador['n']:05d}",
    }
    base.update(campos)
    return base


def lancar(cliente, **campos):
    return cliente.post("/api/despesas", json=despesa(**campos))


def criar(cliente, **campos) -> dict:
    r = lancar(cliente, **campos)
    assert r.status_code == 201, r.text
    return r.json()


def levar_para(cliente, situacao: str, **campos) -> dict:
    d = criar(cliente, **campos)
    if situacao in ("APROVADA", "PAGA"):
        assert cliente.post(f"/api/despesas/{d['id']}/aprovar").status_code == 200
    if situacao == "PAGA":
        assert cliente.post(f"/api/despesas/{d['id']}/pagar").status_code == 200
    if situacao == "RECUSADA":
        assert cliente.post(f"/api/despesas/{d['id']}/recusar", json={"motivo": "Sem nota"}).status_code == 200
    return d


def situacao_de(cliente, id_: int) -> str:
    return next(d["situacao"] for d in cliente.get("/api/despesas").json() if d["id"] == id_)


def resumo(cliente, mes: str) -> dict:
    r = cliente.get("/api/relatorios/mensal", params={"mes": mes})
    assert r.status_code == 200, r.text
    return r.json()


# ---------- Critérios de aceite ----------

def test_ca_01_lancar_despesa_valida_fica_pendente(cliente):
    entrada = despesa()
    r = cliente.post("/api/despesas", json=entrada)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["situacao"] == "PENDENTE"
    assert corpo["motivo_recusa"] is None
    for campo in ("colaborador_nome", "colaborador_email", "data", "categoria", "valor_centavos", "descricao", "comprovante"):
        assert corpo[campo] == entrada[campo]
    assert corpo["id"] >= 1


def test_ca_02_alimentacao_120_01_recusada_por_limite(cliente):
    r = lancar(cliente, categoria="ALIMENTACAO", valor_centavos=12001)
    assert r.status_code == 422
    assert r.json()["erro"] == "VALOR_ACIMA_DO_LIMITE"


def test_ca_03_hospedagem_450_00_criada(cliente):
    r = lancar(cliente, categoria="HOSPEDAGEM", valor_centavos=45000)
    assert r.status_code == 201
    assert r.json()["situacao"] == "PENDENTE"
    assert r.json()["valor_centavos"] == 45000


def test_ca_04_data_61_dias_atras_recusada(cliente):
    r = lancar(cliente, data=(HOJE - timedelta(days=61)).isoformat())
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_MUITO_ANTIGA"


def test_ca_05_data_de_amanha_recusada(cliente):
    r = lancar(cliente, data=(HOJE + timedelta(days=1)).isoformat())
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_FUTURA"


def test_ca_06_mesmo_comprovante_mesmo_colaborador_recusado(cliente):
    entrada = despesa(comprovante="NF-777")
    assert cliente.post("/api/despesas", json=entrada).status_code == 201
    r = cliente.post("/api/despesas", json=entrada)
    assert r.status_code == 409
    assert r.json()["erro"] == "COMPROVANTE_DUPLICADO"
    assert len(cliente.get("/api/despesas", params={"email": entrada["colaborador_email"]}).json()) == 1


def test_ca_07_recusar_sem_motivo_recusado(cliente):
    d = criar(cliente)
    r = cliente.post(f"/api/despesas/{d['id']}/recusar")
    assert r.status_code == 422
    assert r.json()["erro"] == "MOTIVO_OBRIGATORIO"
    r = cliente.post(f"/api/despesas/{d['id']}/recusar", json={})
    assert r.status_code == 422
    assert r.json()["erro"] == "MOTIVO_OBRIGATORIO"
    assert situacao_de(cliente, d["id"]) == "PENDENTE"


def test_ca_08_pagar_pendente_recusado(cliente):
    d = criar(cliente)
    r = cliente.post(f"/api/despesas/{d['id']}/pagar")
    assert r.status_code == 409
    assert r.json()["erro"] == "TRANSICAO_INVALIDA"
    assert situacao_de(cliente, d["id"]) == "PENDENTE"


def test_ca_09_aprovar_e_pagar_fica_paga(cliente):
    d = criar(cliente)
    r = cliente.post(f"/api/despesas/{d['id']}/aprovar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "APROVADA"
    r = cliente.post(f"/api/despesas/{d['id']}/pagar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "PAGA"
    assert situacao_de(cliente, d["id"]) == "PAGA"


def test_ca_10_resumo_ignora_recusada_e_pendente(cliente):
    antes = resumo(cliente, "2029-12")
    levar_para(cliente, "APROVADA", data="2029-12-10", categoria="HOSPEDAGEM", valor_centavos=30000)
    levar_para(cliente, "PAGA", data="2029-12-11", categoria="TRANSPORTE", valor_centavos=7000)
    levar_para(cliente, "RECUSADA", data="2029-12-12", categoria="ALIMENTACAO", valor_centavos=11000)
    levar_para(cliente, "PENDENTE", data="2029-12-13", categoria="OUTROS", valor_centavos=50000)
    depois = resumo(cliente, "2029-12")
    delta = {c: depois["totais_centavos"][c] - antes["totais_centavos"][c] for c in LIMITES}
    assert delta == {"HOSPEDAGEM": 30000, "TRANSPORTE": 7000, "ALIMENTACAO": 0, "OUTROS": 0}
    assert depois["total_geral_centavos"] - antes["total_geral_centavos"] == 37000
    assert depois["total_geral_centavos"] == sum(depois["totais_centavos"].values())
    assert depois["mes"] == "2029-12"


# ---------- Bordas das regras ----------

def test_rn_01_valor_zero_recusado(cliente):
    r = lancar(cliente, valor_centavos=0)
    assert r.status_code == 422
    assert r.json()["erro"] == "VALOR_INVALIDO"


def test_rn_01_valor_um_centavo_aceito(cliente):
    r = lancar(cliente, valor_centavos=1)
    assert r.status_code == 201
    assert r.json()["valor_centavos"] == 1


def test_rn_01_valor_negativo_recusado(cliente):
    assert lancar(cliente, valor_centavos=-1).status_code == 422


@pytest.mark.parametrize("categoria", list(LIMITES))
def test_rn_02_limite_por_categoria(cliente, categoria):
    limite = LIMITES[categoria]
    assert lancar(cliente, categoria=categoria, valor_centavos=limite - 1).status_code == 201
    assert lancar(cliente, categoria=categoria, valor_centavos=limite).status_code == 201
    r = lancar(cliente, categoria=categoria, valor_centavos=limite + 1)
    assert r.status_code == 422
    assert r.json()["erro"] == "VALOR_ACIMA_DO_LIMITE"


def test_rn_03_data_de_hoje_aceita(cliente):
    assert lancar(cliente, data=HOJE.isoformat()).status_code == 201


def test_rn_03_virada_do_dia_libera_data(cliente, relogio):
    amanha = (HOJE + timedelta(days=1)).isoformat()
    assert lancar(cliente, data=amanha).status_code == 422
    relogio.avancar(days=1)
    assert lancar(cliente, data=amanha).status_code == 201


def test_rn_04_borda_60_dias(cliente):
    assert lancar(cliente, data=(HOJE - timedelta(days=59)).isoformat()).status_code == 201
    assert lancar(cliente, data=(HOJE - timedelta(days=60)).isoformat()).status_code == 201
    r = lancar(cliente, data=(HOJE - timedelta(days=61)).isoformat())
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_MUITO_ANTIGA"


def test_rn_05_mesmo_comprovante_outro_colaborador_aceito(cliente):
    assert lancar(cliente, comprovante="NF-888").status_code == 201
    r = lancar(cliente, comprovante="NF-888", colaborador_email="outra.pessoa@empresa.example")
    assert r.status_code == 201


def test_rn_05_email_com_maiusculas_conta_como_mesmo_colaborador(cliente):
    assert lancar(cliente, comprovante="NF-999").status_code == 201
    r = lancar(cliente, comprovante=" NF-999 ", colaborador_email="Diego.Teste@EMPRESA.example")
    assert r.status_code == 409
    assert r.json()["erro"] == "COMPROVANTE_DUPLICADO"


def test_rn_05_recusada_continua_bloqueando_e_excluida_libera(cliente):
    levar_para(cliente, "RECUSADA", comprovante="NF-500")
    assert lancar(cliente, comprovante="NF-500").status_code == 409
    d = criar(cliente, comprovante="NF-501")
    assert cliente.delete(f"/api/despesas/{d['id']}").status_code == 204
    assert lancar(cliente, comprovante="NF-501").status_code == 201


@pytest.mark.parametrize(
    "situacao, acao",
    [
        ("APROVADA", "aprovar"),
        ("APROVADA", "recusar"),
        ("RECUSADA", "aprovar"),
        ("RECUSADA", "recusar"),
        ("RECUSADA", "pagar"),
        ("PAGA", "aprovar"),
        ("PAGA", "recusar"),
        ("PAGA", "pagar"),
    ],
)
def test_rn_07_transicoes_invalidas(cliente, situacao, acao):
    d = levar_para(cliente, situacao)
    r = cliente.post(f"/api/despesas/{d['id']}/{acao}", json={"motivo": "Qualquer"})
    assert r.status_code == 409
    assert r.json()["erro"] == "TRANSICAO_INVALIDA"
    assert situacao_de(cliente, d["id"]) == situacao


def test_rn_08_motivo_so_espacos_recusado(cliente):
    d = criar(cliente)
    r = cliente.post(f"/api/despesas/{d['id']}/recusar", json={"motivo": "   "})
    assert r.status_code == 422
    assert r.json()["erro"] == "MOTIVO_OBRIGATORIO"


def test_rn_08_recusar_com_motivo(cliente):
    d = criar(cliente)
    r = cliente.post(f"/api/despesas/{d['id']}/recusar", json={"motivo": " Sem nota "})
    assert r.status_code == 200
    assert r.json()["situacao"] == "RECUSADA"
    assert r.json()["motivo_recusa"] == "Sem nota"


def test_rn_09_excluir_pendente(cliente):
    d = criar(cliente)
    r = cliente.delete(f"/api/despesas/{d['id']}")
    assert r.status_code == 204
    assert all(x["id"] != d["id"] for x in cliente.get("/api/despesas").json())


@pytest.mark.parametrize("situacao", ["APROVADA", "RECUSADA", "PAGA"])
def test_rn_09_excluir_nao_pendente_recusado(cliente, situacao):
    d = levar_para(cliente, situacao)
    r = cliente.delete(f"/api/despesas/{d['id']}")
    assert r.status_code == 409
    assert r.json()["erro"] == "EXCLUSAO_NAO_PERMITIDA"
    assert situacao_de(cliente, d["id"]) == situacao


def test_rn_10_resumo_bordas_do_mes(cliente):
    dez_antes, nov_antes = resumo(cliente, "2029-12"), resumo(cliente, "2029-11")
    levar_para(cliente, "APROVADA", data="2029-12-01", categoria="OUTROS", valor_centavos=100)
    levar_para(cliente, "APROVADA", data="2029-12-31", categoria="OUTROS", valor_centavos=200)
    levar_para(cliente, "APROVADA", data="2029-11-30", categoria="OUTROS", valor_centavos=400)
    dez, nov = resumo(cliente, "2029-12"), resumo(cliente, "2029-11")
    assert dez["totais_centavos"]["OUTROS"] - dez_antes["totais_centavos"]["OUTROS"] == 300
    assert nov["totais_centavos"]["OUTROS"] - nov_antes["totais_centavos"]["OUTROS"] == 400
    assert dez["total_geral_centavos"] - dez_antes["total_geral_centavos"] == 300


def test_rf_06_filtros_por_email_e_situacao(cliente):
    a1 = criar(cliente, colaborador_email="filtro.a@empresa.example", data="2030-01-01")
    a2 = levar_para(cliente, "APROVADA", colaborador_email="filtro.a@empresa.example", data="2030-01-03")
    b1 = criar(cliente, colaborador_email="filtro.b@empresa.example")

    por_email = cliente.get("/api/despesas", params={"email": "FILTRO.A@empresa.example"}).json()
    assert [d["id"] for d in por_email] == [a2["id"], a1["id"]]  # data mais recente primeiro

    combinado = cliente.get("/api/despesas", params={"email": "filtro.a@empresa.example", "situacao": "PENDENTE"}).json()
    assert [d["id"] for d in combinado] == [a1["id"]]

    pendentes = cliente.get("/api/despesas", params={"situacao": "PENDENTE"}).json()
    assert all(d["situacao"] == "PENDENTE" for d in pendentes)
    assert b1["id"] in [d["id"] for d in pendentes]

    todas = cliente.get("/api/despesas").json()
    datas = [d["data"] for d in todas]
    assert datas == sorted(datas, reverse=True)
    assert cliente.get("/api/despesas", params={"situacao": "OUTRA"}).status_code == 422
    assert cliente.get("/api/despesas", params={"email": "sem-arroba"}).status_code == 422


def test_rf_08_carga_inicial_cinco_despesas_quatro_situacoes(cliente):
    despesas = cliente.get("/api/despesas").json()
    assert len(despesas) == 5
    assert {d["situacao"] for d in despesas} == {"PENDENTE", "APROVADA", "RECUSADA", "PAGA"}
    for d in despesas:
        dia = date.fromisoformat(d["data"])
        assert HOJE - timedelta(days=60) <= dia <= HOJE
        assert d["valor_centavos"] <= LIMITES[d["categoria"]]
    assert all(d["motivo_recusa"] for d in despesas if d["situacao"] == "RECUSADA")


def test_despesa_inexistente_404(cliente):
    for acao in ("aprovar", "recusar", "pagar"):
        r = cliente.post(f"/api/despesas/999999/{acao}", json={"motivo": "x"})
        assert r.status_code == 404
        assert r.json()["erro"] == "DESPESA_NAO_ENCONTRADA"
    r = cliente.delete("/api/despesas/999999")
    assert r.status_code == 404
    assert r.json()["erro"] == "DESPESA_NAO_ENCONTRADA"


@pytest.mark.parametrize("params", [{"mes": "2030-13"}, {"mes": "1999-01"}, {"mes": "2030-1"}, {}])
def test_mes_invalido_422(cliente, params):
    assert cliente.get("/api/relatorios/mensal", params=params).status_code == 422
