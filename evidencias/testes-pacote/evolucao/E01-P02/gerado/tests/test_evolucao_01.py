"""Evolução 1: edição de despesa PENDENTE (RF-12, RN-11) e quantidades no resumo (RF-07, PR-15)."""

import pytest

from tests.test_despesas import LIMITES, criar, levar_para, resumo


def editar(cliente, id_: int, **campos):
    corpo = {"categoria": "HOSPEDAGEM", "valor_centavos": 40000, "descricao": "Hotel, descrição corrigida"}
    corpo.update(campos)
    return cliente.put(f"/api/despesas/{id_}", json=corpo)


def despesa_por_id(cliente, id_: int) -> dict:
    return next(d for d in cliente.get("/api/despesas").json() if d["id"] == id_)


# ---------- Critérios de aceite ----------

def test_ca_11_editar_pendente(cliente):
    d = criar(cliente)
    r = editar(cliente, d["id"])
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["categoria"] == "HOSPEDAGEM"
    assert corpo["valor_centavos"] == 40000
    assert corpo["descricao"] == "Hotel, descrição corrigida"
    assert corpo["situacao"] == "PENDENTE"
    for campo in ("colaborador_nome", "colaborador_email", "data", "comprovante"):
        assert corpo[campo] == d[campo]
    assert despesa_por_id(cliente, d["id"]) == corpo


def test_ca_12_editar_para_alimentacao_120_01_recusado(cliente):
    d = criar(cliente)
    r = editar(cliente, d["id"], categoria="ALIMENTACAO", valor_centavos=12001)
    assert r.status_code == 422
    assert r.json()["erro"] == "VALOR_ACIMA_DO_LIMITE"
    assert despesa_por_id(cliente, d["id"]) == d


def test_ca_13_editar_aprovada_recusado(cliente):
    d = levar_para(cliente, "APROVADA")
    antes = despesa_por_id(cliente, d["id"])
    r = editar(cliente, d["id"])
    assert r.status_code == 409
    assert r.json()["erro"] == "EDICAO_NAO_PERMITIDA"
    assert despesa_por_id(cliente, d["id"]) == antes


def test_ca_14_resumo_quantidades_por_categoria(cliente):
    antes = resumo(cliente, "2029-12")
    levar_para(cliente, "APROVADA", categoria="HOSPEDAGEM", valor_centavos=30000, data="2029-12-10")
    levar_para(cliente, "APROVADA", categoria="HOSPEDAGEM", valor_centavos=20000, data="2029-12-11")
    levar_para(cliente, "PAGA", categoria="TRANSPORTE", valor_centavos=7000, data="2029-12-12")
    levar_para(cliente, "RECUSADA", categoria="ALIMENTACAO", valor_centavos=9000, data="2029-12-13")
    levar_para(cliente, "PENDENTE", categoria="OUTROS", valor_centavos=8000, data="2029-12-14")
    depois = resumo(cliente, "2029-12")
    delta = {c: depois["quantidades"][c] - antes["quantidades"][c] for c in LIMITES}
    assert delta == {"HOSPEDAGEM": 2, "TRANSPORTE": 1, "ALIMENTACAO": 0, "OUTROS": 0}
    assert set(depois["quantidades"]) == set(LIMITES)
    assert depois["quantidade_total"] == sum(depois["quantidades"].values())
    assert depois["quantidade_total"] - antes["quantidade_total"] == 3
    assert depois["total_geral_centavos"] - antes["total_geral_centavos"] == 57000


# ---------- Regras ----------

@pytest.mark.parametrize("situacao", ["RECUSADA", "PAGA"])
def test_rn_11_editar_nao_pendente_recusado(cliente, situacao):
    d = levar_para(cliente, situacao)
    r = editar(cliente, d["id"])
    assert r.status_code == 409
    assert r.json()["erro"] == "EDICAO_NAO_PERMITIDA"


def test_rn_11_situacao_antes_do_valor(cliente):
    d = levar_para(cliente, "APROVADA")
    r = editar(cliente, d["id"], valor_centavos=0)
    assert r.status_code == 409
    assert r.json()["erro"] == "EDICAO_NAO_PERMITIDA"


def test_rn_01_editar_valor_zero_recusado(cliente):
    d = criar(cliente)
    r = editar(cliente, d["id"], valor_centavos=0)
    assert r.status_code == 422
    assert r.json()["erro"] == "VALOR_INVALIDO"


def test_rn_02_editar_limite_da_categoria_nova(cliente):
    d = criar(cliente, categoria="TRANSPORTE", valor_centavos=50000)
    r = editar(cliente, d["id"], categoria="ALIMENTACAO", valor_centavos=12000)
    assert r.status_code == 200, r.text
    r = editar(cliente, d["id"], categoria="HOSPEDAGEM", valor_centavos=45001)
    assert r.status_code == 422
    assert r.json()["erro"] == "VALOR_ACIMA_DO_LIMITE"
    assert despesa_por_id(cliente, d["id"])["categoria"] == "ALIMENTACAO"


def test_editar_inexistente_404(cliente):
    r = editar(cliente, 999999)
    assert r.status_code == 404
    assert r.json()["erro"] == "DESPESA_NAO_ENCONTRADA"


def test_editar_campo_faltando_422(cliente):
    d = criar(cliente)
    r = cliente.put(f"/api/despesas/{d['id']}", json={"categoria": "OUTROS", "valor_centavos": 100})
    assert r.status_code == 422
