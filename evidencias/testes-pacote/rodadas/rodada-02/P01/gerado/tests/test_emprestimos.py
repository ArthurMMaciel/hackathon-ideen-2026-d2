"""Testes do plano da SPEC: critérios de aceite (test_ca_*), bordas de regras (test_rn_*) e requisitos (test_rf_*)."""

import itertools
from datetime import timedelta

import pytest

HOJE = "2030-01-07"
_seq = itertools.count(100)


def dia(relogio, dias: int = 0) -> str:
    return (relogio.agora.date() + timedelta(days=dias)).isoformat()


def novo_equipamento(cliente, tipo: str = "NOTEBOOK") -> dict:
    r = cliente.post(
        "/api/equipamentos",
        json={"patrimonio": f"EQ-{next(_seq):04d}", "tipo": tipo, "descricao": f"{tipo.title()} de teste"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def emprestar(cliente, equipamento_id: int, data_prevista: str, email: str = "ana@exemplo.com"):
    return cliente.post(
        "/api/emprestimos",
        json={"equipamento_id": equipamento_id, "nome": "Ana Teste", "email": email, "data_prevista": data_prevista},
    )


def situacao(cliente, equipamento_id: int) -> str:
    return cliente.get(f"/api/equipamentos/{equipamento_id}").json()["situacao"]


def devolver(cliente, emprestimo_id: int, defeito: bool | None = None):
    corpo = {} if defeito is None else {"defeito": defeito}
    return cliente.post(f"/api/emprestimos/{emprestimo_id}/devolver", json=corpo)


# ---------- Critérios de aceite ----------

def test_ca_01_emprestar_disponivel_dentro_do_prazo(cliente, relogio):
    eq = novo_equipamento(cliente, "NOTEBOOK")
    r = emprestar(cliente, eq["id"], dia(relogio, 7))
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["status"] == "ABERTO"
    assert corpo["data_retirada"] == HOJE
    assert corpo["data_prevista"] == "2030-01-14"
    assert corpo["data_devolucao"] is None
    assert situacao(cliente, eq["id"]) == "EMPRESTADO"


def test_ca_02_recusa_equipamento_ja_emprestado(cliente, relogio):
    eq = novo_equipamento(cliente)
    assert emprestar(cliente, eq["id"], dia(relogio, 1)).status_code == 201
    r = emprestar(cliente, eq["id"], dia(relogio, 1), email="bruno@exemplo.com")
    assert r.status_code == 409
    assert r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL"


def test_ca_03_recusa_equipamento_em_manutencao(cliente, relogio):
    eq = novo_equipamento(cliente, "PROJETOR")
    emp = emprestar(cliente, eq["id"], dia(relogio, 1)).json()
    assert devolver(cliente, emp["id"], True).status_code == 200
    assert situacao(cliente, eq["id"]) == "MANUTENCAO"
    r = emprestar(cliente, eq["id"], dia(relogio, 1))
    assert r.status_code == 409
    assert r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL"


def test_ca_03_recusa_headset_inicial_em_manutencao(cliente, relogio):
    equipamentos = cliente.get("/api/equipamentos").json()
    em_manutencao = [e for e in equipamentos if e["situacao"] == "MANUTENCAO"]
    assert len(em_manutencao) == 1 and em_manutencao[0]["tipo"] == "HEADSET"
    r = emprestar(cliente, em_manutencao[0]["id"], dia(relogio, 1))
    assert r.status_code == 409
    assert r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL"


def test_ca_04_recusa_notebook_15_dias(cliente, relogio):
    eq = novo_equipamento(cliente, "NOTEBOOK")
    r = emprestar(cliente, eq["id"], dia(relogio, 15))
    assert r.status_code == 422
    assert r.json()["erro"] == "PRAZO_EXCEDIDO"
    assert situacao(cliente, eq["id"]) == "DISPONIVEL"


def test_ca_05_projetor_3_dias_criado(cliente, relogio):
    eq = novo_equipamento(cliente, "PROJETOR")
    r = emprestar(cliente, eq["id"], dia(relogio, 3))
    assert r.status_code == 201
    assert r.json()["status"] == "ABERTO"
    assert r.json()["data_prevista"] == "2030-01-10"


def test_ca_06_recusa_terceiro_emprestimo_aberto(cliente, relogio):
    for _ in range(2):
        eq = novo_equipamento(cliente, "HEADSET")
        assert emprestar(cliente, eq["id"], dia(relogio, 1)).status_code == 201
    terceiro = novo_equipamento(cliente, "HEADSET")
    r = emprestar(cliente, terceiro["id"], dia(relogio, 1))
    assert r.status_code == 409
    assert r.json()["erro"] == "LIMITE_EMPRESTIMOS"
    assert situacao(cliente, terceiro["id"]) == "DISPONIVEL"


def test_ca_07_devolver_sem_defeito(cliente, relogio):
    eq = novo_equipamento(cliente)
    emp = emprestar(cliente, eq["id"], dia(relogio, 5)).json()
    relogio.avancar(days=2)
    r = devolver(cliente, emp["id"], False)
    assert r.status_code == 200
    assert r.json()["status"] == "DEVOLVIDO"
    assert r.json()["data_devolucao"] == "2030-01-09"
    assert r.json()["defeito"] is False
    assert situacao(cliente, eq["id"]) == "DISPONIVEL"


def test_ca_07_devolver_sem_informar_defeito_assume_sem_defeito(cliente, relogio):
    eq = novo_equipamento(cliente)
    emp = emprestar(cliente, eq["id"], dia(relogio, 5)).json()
    r = devolver(cliente, emp["id"])
    assert r.status_code == 200
    assert r.json()["status"] == "DEVOLVIDO"
    assert situacao(cliente, eq["id"]) == "DISPONIVEL"


def test_ca_08_devolver_com_defeito(cliente, relogio):
    eq = novo_equipamento(cliente, "HEADSET")
    emp = emprestar(cliente, eq["id"], dia(relogio, 2)).json()
    r = devolver(cliente, emp["id"], True)
    assert r.status_code == 200
    assert r.json()["status"] == "DEVOLVIDO"
    assert r.json()["defeito"] is True
    assert situacao(cliente, eq["id"]) == "MANUTENCAO"


def test_ca_09_atrasado_um_dia(cliente, relogio):
    eq = novo_equipamento(cliente, "PROJETOR")
    emp = emprestar(cliente, eq["id"], dia(relogio, 1)).json()
    relogio.avancar(days=2)  # hoje = 2030-01-09, prevista 2030-01-08 = ontem
    atrasados = cliente.get("/api/emprestimos/atrasados").json()
    item = next(a for a in atrasados if a["id"] == emp["id"])
    assert item["status"] == "ABERTO"
    assert item["dias_atraso"] == 1


def test_ca_10_recusa_devolver_ja_devolvido(cliente, relogio):
    eq = novo_equipamento(cliente)
    emp = emprestar(cliente, eq["id"], dia(relogio, 1)).json()
    assert devolver(cliente, emp["id"], False).status_code == 200
    r = devolver(cliente, emp["id"], False)
    assert r.status_code == 409
    assert r.json()["erro"] == "EMPRESTIMO_JA_DEVOLVIDO"


# ---------- Bordas das regras ----------

@pytest.mark.parametrize("patrimonio", ["EQ-123", "EQ-12345", "eq-0001", "XX-0001", "EQ-１２３４", " EQ-0001x"])
def test_rn_01_patrimonio_formato_invalido(cliente, patrimonio):
    r = cliente.post("/api/equipamentos", json={"patrimonio": patrimonio, "tipo": "NOTEBOOK", "descricao": "x"})
    assert r.status_code == 422


def test_rn_01_patrimonio_duplicado(cliente):
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-0001", "tipo": "NOTEBOOK", "descricao": "Outro"})
    assert r.status_code == 409
    assert r.json()["erro"] == "PATRIMONIO_DUPLICADO"


def test_rn_01_cadastro_nasce_disponivel(cliente):
    r = cliente.post("/api/equipamentos", json={"patrimonio": "EQ-9999", "tipo": "PROJETOR", "descricao": "Novo"})
    assert r.status_code == 201
    assert r.json()["situacao"] == "DISPONIVEL"
    assert r.json()["patrimonio"] == "EQ-9999"


@pytest.mark.parametrize(
    "tipo,dias,status",
    [
        ("NOTEBOOK", 13, 201), ("NOTEBOOK", 14, 201), ("NOTEBOOK", 15, 422),
    ],
)
def test_rn_04_notebook_borda_13_14_15(cliente, relogio, tipo, dias, status):
    eq = novo_equipamento(cliente, tipo)
    r = emprestar(cliente, eq["id"], dia(relogio, dias))
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "PRAZO_EXCEDIDO"


@pytest.mark.parametrize("dias,status", [(2, 201), (3, 201), (4, 422)])
def test_rn_04_projetor_borda_2_3_4(cliente, relogio, dias, status):
    eq = novo_equipamento(cliente, "PROJETOR")
    r = emprestar(cliente, eq["id"], dia(relogio, dias))
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "PRAZO_EXCEDIDO"


@pytest.mark.parametrize("dias,status", [(2, 201), (3, 201), (4, 422)])
def test_rn_04_headset_borda_2_3_4(cliente, relogio, dias, status):
    eq = novo_equipamento(cliente, "HEADSET")
    r = emprestar(cliente, eq["id"], dia(relogio, dias))
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "PRAZO_EXCEDIDO"


def test_rn_05_prevista_igual_retirada_aceita_ontem_recusada(cliente, relogio):
    eq = novo_equipamento(cliente)
    r = emprestar(cliente, eq["id"], dia(relogio, -1))
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_PREVISTA_ANTERIOR"
    r = emprestar(cliente, eq["id"], dia(relogio, 0))
    assert r.status_code == 201
    assert r.json()["data_prevista"] == r.json()["data_retirada"] == HOJE


def test_rn_06_limite_por_email_sem_diferenca_de_caixa(cliente, relogio):
    for email in ["ana@exemplo.com", "Ana@Exemplo.com"]:
        eq = novo_equipamento(cliente)
        r = emprestar(cliente, eq["id"], dia(relogio, 1), email=email)
        assert r.status_code == 201
        assert r.json()["email"] == "ana@exemplo.com"
    eq = novo_equipamento(cliente)
    r = emprestar(cliente, eq["id"], dia(relogio, 1), email="ANA@EXEMPLO.COM")
    assert r.status_code == 409
    assert r.json()["erro"] == "LIMITE_EMPRESTIMOS"
    # outra pessoa não é afetada
    assert emprestar(cliente, eq["id"], dia(relogio, 1), email="bruno@exemplo.com").status_code == 201


def test_rn_06_devolucao_libera_limite(cliente, relogio):
    ids = []
    for _ in range(2):
        eq = novo_equipamento(cliente)
        ids.append(emprestar(cliente, eq["id"], dia(relogio, 1)).json()["id"])
    assert devolver(cliente, ids[0], False).status_code == 200
    eq = novo_equipamento(cliente)
    assert emprestar(cliente, eq["id"], dia(relogio, 1)).status_code == 201


def test_rn_09_borda_prevista_hoje_nao_atrasa(cliente, relogio):
    eq = novo_equipamento(cliente)
    emp = emprestar(cliente, eq["id"], dia(relogio, 1)).json()
    relogio.avancar(days=1)  # hoje == prevista
    assert all(a["id"] != emp["id"] for a in cliente.get("/api/emprestimos/atrasados").json())
    relogio.avancar(days=2)  # 2030-01-10, prevista 2030-01-08
    item = next(a for a in cliente.get("/api/emprestimos/atrasados").json() if a["id"] == emp["id"])
    assert item["dias_atraso"] == 2


def test_rn_09_devolvido_nao_aparece_nos_atrasados(cliente, relogio):
    eq = novo_equipamento(cliente)
    emp = emprestar(cliente, eq["id"], dia(relogio, 1)).json()
    relogio.avancar(days=3)
    assert devolver(cliente, emp["id"], False).status_code == 200
    assert all(a["id"] != emp["id"] for a in cliente.get("/api/emprestimos/atrasados").json())


def test_rn_09_atrasados_ordenados_por_maior_atraso(cliente, relogio):
    eq1 = novo_equipamento(cliente)
    eq2 = novo_equipamento(cliente)
    e1 = emprestar(cliente, eq1["id"], dia(relogio, 2), email="c@exemplo.com").json()
    e2 = emprestar(cliente, eq2["id"], dia(relogio, 0), email="d@exemplo.com").json()
    relogio.avancar(days=5)
    atrasados = cliente.get("/api/emprestimos/atrasados").json()
    assert [a["id"] for a in atrasados] == [e2["id"], e1["id"]]
    assert [a["dias_atraso"] for a in atrasados] == [5, 3]


def test_rn_10_relatorio_por_tipo_no_mes(tmp_path):
    from datetime import datetime

    from fastapi.testclient import TestClient

    from app.main import criar_app
    from app.relogio import FUSO, obter_agora
    from tests.conftest import RelogioDeTeste

    relogio = RelogioDeTeste(datetime(2030, 1, 31, 23, 30, tzinfo=FUSO))
    app = criar_app(str(tmp_path / "rel.db"))
    app.dependency_overrides[obter_agora] = relogio
    with TestClient(app) as cliente:
        for tipo, email in [("NOTEBOOK", "a@exemplo.com"), ("NOTEBOOK", "b@exemplo.com"), ("HEADSET", "c@exemplo.com")]:
            eq = novo_equipamento(cliente, tipo)
            assert emprestar(cliente, eq["id"], dia(relogio, 1), email=email).status_code == 201
        relogio.avancar(hours=1)  # 2030-02-01 00:30
        eq = novo_equipamento(cliente, "PROJETOR")
        assert emprestar(cliente, eq["id"], dia(relogio, 1), email="d@exemplo.com").status_code == 201

        jan = cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": "2030-01"})
        assert jan.status_code == 200
        assert jan.json() == {
            "mes": "2030-01",
            "itens": [
                {"tipo": "NOTEBOOK", "quantidade": 2},
                {"tipo": "PROJETOR", "quantidade": 0},
                {"tipo": "HEADSET", "quantidade": 1},
            ],
        }
        fev = cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": "2030-02"}).json()
        assert [i["quantidade"] for i in fev["itens"]] == [0, 1, 0]
        dez = cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": "2029-12"}).json()
        assert [i["quantidade"] for i in dez["itens"]] == [0, 0, 0]


@pytest.mark.parametrize("mes", ["2030-13", "2030-00", "2030-1", "1999-12", "2101-01", "abc", "2030-01-01", "２０３０-01"])
def test_rn_10_mes_invalido(cliente, mes):
    assert cliente.get("/api/relatorios/emprestimos-por-tipo", params={"mes": mes}).status_code == 422


def test_rn_10_mes_obrigatorio(cliente):
    assert cliente.get("/api/relatorios/emprestimos-por-tipo").status_code == 422


# ---------- Requisitos ----------

def test_rf_03_carga_inicial(cliente):
    equipamentos = cliente.get("/api/equipamentos").json()
    assert len(equipamentos) == 8
    por_tipo = {t: [e for e in equipamentos if e["tipo"] == t] for t in ("NOTEBOOK", "PROJETOR", "HEADSET")}
    assert [len(por_tipo[t]) for t in ("NOTEBOOK", "PROJETOR", "HEADSET")] == [3, 2, 3]
    assert [e["situacao"] for e in por_tipo["HEADSET"]].count("MANUTENCAO") == 1
    assert all(e["situacao"] == "DISPONIVEL" for e in equipamentos if e["tipo"] != "HEADSET")
    assert [e["patrimonio"] for e in equipamentos] == sorted(e["patrimonio"] for e in equipamentos)


def test_rf_03_carga_inicial_idempotente(tmp_path, relogio):
    from fastapi.testclient import TestClient

    from app.main import criar_app
    from app.relogio import obter_agora

    caminho = str(tmp_path / "idem.db")
    for _ in range(2):
        app = criar_app(caminho)
        app.dependency_overrides[obter_agora] = relogio
        with TestClient(app) as c:
            assert len(c.get("/api/equipamentos").json()) == 8


def test_rf_06_disponiveis_filtro_tipo(cliente, relogio):
    headsets = cliente.get("/api/equipamentos/disponiveis", params={"tipo": "HEADSET"}).json()
    assert len(headsets) == 2
    assert all(e["tipo"] == "HEADSET" and e["situacao"] == "DISPONIVEL" for e in headsets)
    todos = cliente.get("/api/equipamentos/disponiveis").json()
    assert len(todos) == 7
    assert emprestar(cliente, todos[0]["id"], dia(relogio, 1)).status_code == 201
    assert len(cliente.get("/api/equipamentos/disponiveis").json()) == 6
    assert cliente.get("/api/equipamentos/disponiveis", params={"tipo": "TABLET"}).status_code == 422


def test_rf_08_lista_por_status(cliente, relogio):
    a = emprestar(cliente, novo_equipamento(cliente)["id"], dia(relogio, 1)).json()
    b = emprestar(cliente, novo_equipamento(cliente)["id"], dia(relogio, 1)).json()
    devolver(cliente, b["id"], False)
    abertos = cliente.get("/api/emprestimos", params={"status": "ABERTO"}).json()
    devolvidos = cliente.get("/api/emprestimos", params={"status": "DEVOLVIDO"}).json()
    assert [e["id"] for e in abertos] == [a["id"]]
    assert [e["id"] for e in devolvidos] == [b["id"]]
    assert [e["id"] for e in cliente.get("/api/emprestimos").json()] == [a["id"], b["id"]]
    assert abertos[0]["patrimonio"].startswith("EQ-") and abertos[0]["tipo"] == "NOTEBOOK"
    assert cliente.get("/api/emprestimos", params={"status": "PERDIDO"}).status_code == 422


def test_equipamento_e_emprestimo_inexistentes(cliente, relogio):
    r = cliente.get("/api/equipamentos/999999")
    assert r.status_code == 404 and r.json()["erro"] == "EQUIPAMENTO_NAO_ENCONTRADO"
    r = emprestar(cliente, 999999, dia(relogio, 1))
    assert r.status_code == 404 and r.json()["erro"] == "EQUIPAMENTO_NAO_ENCONTRADO"
    r = devolver(cliente, 999999, False)
    assert r.status_code == 404 and r.json()["erro"] == "EMPRESTIMO_NAO_ENCONTRADO"
