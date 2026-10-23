"""Testes de empréstimo, devolução e atrasados (CA-01 a CA-10, RN-02 a RN-11)."""

from datetime import datetime

from app.relogio import FUSO

NOTEBOOK, NOTEBOOK_2, NOTEBOOK_3 = 1, 2, 3
PROJETOR = 4
HEADSET = 6
HEADSET_MANUTENCAO = 8


def emprestar(cliente, equipamento_id, data_prevista, email="ana@exemplo.test", nome="Ana Exemplo"):
    return cliente.post(
        "/api/emprestimos",
        json={"equipamento_id": equipamento_id, "nome": nome, "email": email, "data_prevista": data_prevista},
    )


def devolver(cliente, emprestimo_id, defeito=False):
    return cliente.post(f"/api/emprestimos/{emprestimo_id}/devolver", json={"defeito": defeito})


def situacao(cliente, equipamento_id):
    return cliente.get(f"/api/equipamentos/{equipamento_id}").json()["situacao"]


# ---------- Critérios de aceite ----------

def test_ca_01_emprestar_disponivel(cliente):
    r = emprestar(cliente, NOTEBOOK, "2030-01-10")
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["status"] == "ABERTO"
    assert corpo["situacao_equipamento"] == "EMPRESTADO"
    assert corpo["data_retirada"] == "2030-01-07"
    assert corpo["data_prevista"] == "2030-01-10"
    assert corpo["data_devolucao"] is None
    assert situacao(cliente, NOTEBOOK) == "EMPRESTADO"


def test_ca_02_recusa_equipamento_emprestado(cliente):
    assert emprestar(cliente, NOTEBOOK, "2030-01-10").status_code == 201
    r = emprestar(cliente, NOTEBOOK, "2030-01-10", email="bruno@exemplo.test", nome="Bruno Exemplo")
    assert r.status_code == 409
    assert r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL"


def test_ca_03_recusa_equipamento_em_manutencao(cliente):
    r = emprestar(cliente, HEADSET_MANUTENCAO, "2030-01-08")
    assert r.status_code == 409
    assert r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL"
    assert situacao(cliente, HEADSET_MANUTENCAO) == "MANUTENCAO"


def test_ca_04_recusa_notebook_15_dias(cliente):
    r = emprestar(cliente, NOTEBOOK, "2030-01-22")
    assert r.status_code == 422
    assert r.json()["erro"] == "PRAZO_EXCEDIDO"
    assert situacao(cliente, NOTEBOOK) == "DISPONIVEL"


def test_ca_05_projetor_3_dias_criado(cliente):
    r = emprestar(cliente, PROJETOR, "2030-01-10")
    assert r.status_code == 201
    assert r.json()["status"] == "ABERTO"
    assert situacao(cliente, PROJETOR) == "EMPRESTADO"


def test_ca_06_recusa_terceiro_emprestimo(cliente):
    assert emprestar(cliente, NOTEBOOK, "2030-01-10").status_code == 201
    assert emprestar(cliente, NOTEBOOK_2, "2030-01-10").status_code == 201
    r = emprestar(cliente, NOTEBOOK_3, "2030-01-10")
    assert r.status_code == 422
    assert r.json()["erro"] == "LIMITE_EMPRESTIMOS"
    assert situacao(cliente, NOTEBOOK_3) == "DISPONIVEL"


def test_ca_07_devolver_sem_defeito(cliente, relogio):
    emprestimo = emprestar(cliente, NOTEBOOK, "2030-01-10").json()
    relogio.avancar(days=2)
    r = devolver(cliente, emprestimo["id"], defeito=False)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["status"] == "DEVOLVIDO"
    assert corpo["data_devolucao"] == "2030-01-09"
    assert corpo["defeito"] is False
    assert corpo["situacao_equipamento"] == "DISPONIVEL"
    assert situacao(cliente, NOTEBOOK) == "DISPONIVEL"


def test_ca_08_devolver_com_defeito(cliente):
    emprestimo = emprestar(cliente, HEADSET, "2030-01-08").json()
    r = devolver(cliente, emprestimo["id"], defeito=True)
    assert r.status_code == 200
    assert r.json()["status"] == "DEVOLVIDO"
    assert r.json()["situacao_equipamento"] == "MANUTENCAO"
    assert situacao(cliente, HEADSET) == "MANUTENCAO"


def test_ca_09_atrasado_um_dia(cliente, relogio):
    emprestimo = emprestar(cliente, PROJETOR, "2030-01-07").json()
    relogio.avancar(days=1)
    r = cliente.get("/api/emprestimos/atrasados")
    assert r.status_code == 200
    atrasados = r.json()
    assert [a["id"] for a in atrasados] == [emprestimo["id"]]
    assert atrasados[0]["dias_atraso"] == 1
    assert atrasados[0]["status"] == "ABERTO"


def test_ca_10_recusa_devolver_ja_devolvido(cliente):
    emprestimo = emprestar(cliente, NOTEBOOK, "2030-01-10").json()
    assert devolver(cliente, emprestimo["id"]).status_code == 200
    r = devolver(cliente, emprestimo["id"])
    assert r.status_code == 409
    assert r.json()["erro"] == "EMPRESTIMO_JA_DEVOLVIDO"


# ---------- RN-04: prazo máximo (bordas) ----------

def test_rn_04_notebook_13_dias_aceito(cliente):
    assert emprestar(cliente, NOTEBOOK, "2030-01-20").status_code == 201


def test_rn_04_notebook_14_dias_aceito(cliente):
    assert emprestar(cliente, NOTEBOOK, "2030-01-21").status_code == 201


def test_rn_04_projetor_2_dias_aceito(cliente):
    assert emprestar(cliente, PROJETOR, "2030-01-09").status_code == 201


def test_rn_04_projetor_4_dias_recusado(cliente):
    r = emprestar(cliente, PROJETOR, "2030-01-11")
    assert r.status_code == 422
    assert r.json()["erro"] == "PRAZO_EXCEDIDO"


def test_rn_04_headset_3_dias_aceito(cliente):
    assert emprestar(cliente, HEADSET, "2030-01-10").status_code == 201


def test_rn_04_headset_4_dias_recusado(cliente):
    r = emprestar(cliente, HEADSET, "2030-01-11")
    assert r.status_code == 422
    assert r.json()["erro"] == "PRAZO_EXCEDIDO"


# ---------- RN-05: data prevista não anterior à retirada ----------

def test_rn_05_prevista_ontem_recusada(cliente):
    r = emprestar(cliente, NOTEBOOK, "2030-01-06")
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_PREVISTA_ANTERIOR"


def test_rn_05_prevista_hoje_aceita(cliente):
    r = emprestar(cliente, NOTEBOOK, "2030-01-07")
    assert r.status_code == 201
    assert r.json()["data_prevista"] == r.json()["data_retirada"] == "2030-01-07"


# ---------- RN-06: limite por pessoa ----------

def test_rn_06_segundo_emprestimo_aceito(cliente):
    assert emprestar(cliente, NOTEBOOK, "2030-01-10").status_code == 201
    assert emprestar(cliente, PROJETOR, "2030-01-10").status_code == 201


def test_rn_06_email_com_maiusculas_mesma_pessoa(cliente):
    assert emprestar(cliente, NOTEBOOK, "2030-01-10", email="ana@exemplo.test").status_code == 201
    assert emprestar(cliente, NOTEBOOK_2, "2030-01-10", email="ana@exemplo.test").status_code == 201
    r = emprestar(cliente, NOTEBOOK_3, "2030-01-10", email="  ANA@Exemplo.TEST ")
    assert r.status_code == 422
    assert r.json()["erro"] == "LIMITE_EMPRESTIMOS"


def test_rn_06_devolucao_libera_novo_emprestimo(cliente):
    primeiro = emprestar(cliente, NOTEBOOK, "2030-01-10").json()
    assert emprestar(cliente, NOTEBOOK_2, "2030-01-10").status_code == 201
    assert devolver(cliente, primeiro["id"]).status_code == 200
    assert emprestar(cliente, NOTEBOOK_3, "2030-01-10").status_code == 201


# ---------- RN-03: retirada é a data local do registro ----------

def test_rn_03_retirada_usa_data_local(cliente, relogio):
    relogio.agora = datetime(2030, 1, 7, 22, 30, tzinfo=FUSO)  # 01:30 UTC do dia 8
    r = emprestar(cliente, NOTEBOOK, "2030-01-07")
    assert r.status_code == 201
    assert r.json()["data_retirada"] == "2030-01-07"


# ---------- RN-11: atraso ----------

def test_rn_11_prevista_hoje_nao_atrasa(cliente):
    emprestar(cliente, NOTEBOOK, "2030-01-07")
    assert cliente.get("/api/emprestimos/atrasados").json() == []


def test_rn_11_tres_dias_de_atraso(cliente, relogio):
    emprestar(cliente, PROJETOR, "2030-01-10")
    relogio.avancar(days=6)
    atrasados = cliente.get("/api/emprestimos/atrasados").json()
    assert len(atrasados) == 1
    assert atrasados[0]["dias_atraso"] == 3


def test_rn_11_atrasados_ordenados_por_maior_atraso(cliente, relogio):
    emprestar(cliente, PROJETOR, "2030-01-09")
    emprestar(cliente, NOTEBOOK, "2030-01-07", email="bruno@exemplo.test")
    relogio.avancar(days=4)
    atrasados = cliente.get("/api/emprestimos/atrasados").json()
    assert [a["dias_atraso"] for a in atrasados] == [4, 2]


def test_rn_11_devolvido_nao_atrasa(cliente, relogio):
    emprestimo = emprestar(cliente, NOTEBOOK, "2030-01-07").json()
    relogio.avancar(days=2)
    devolver(cliente, emprestimo["id"])
    assert cliente.get("/api/emprestimos/atrasados").json() == []


# ---------- RF-08: listagem ----------

def test_rf_08_listar_por_status(cliente):
    primeiro = emprestar(cliente, NOTEBOOK, "2030-01-10").json()
    emprestar(cliente, PROJETOR, "2030-01-10")
    devolver(cliente, primeiro["id"])
    abertos = cliente.get("/api/emprestimos", params={"status": "ABERTO"}).json()
    devolvidos = cliente.get("/api/emprestimos", params={"status": "DEVOLVIDO"}).json()
    todos = cliente.get("/api/emprestimos").json()
    assert [e["equipamento_id"] for e in abertos] == [PROJETOR]
    assert [e["id"] for e in devolvidos] == [primeiro["id"]]
    assert len(todos) == 2
    assert cliente.get("/api/emprestimos", params={"status": "PERDIDO"}).status_code == 422


# ---------- Erros de entrada ----------

def test_erro_equipamento_inexistente_no_emprestimo(cliente):
    r = emprestar(cliente, 999, "2030-01-08")
    assert r.status_code == 404
    assert r.json()["erro"] == "EQUIPAMENTO_NAO_ENCONTRADO"


def test_erro_emprestimo_inexistente_na_devolucao(cliente):
    r = devolver(cliente, 999)
    assert r.status_code == 404
    assert r.json()["erro"] == "EMPRESTIMO_NAO_ENCONTRADO"


def test_erro_devolucao_sem_corpo_assume_sem_defeito(cliente):
    emprestimo = emprestar(cliente, NOTEBOOK, "2030-01-10").json()
    r = cliente.post(f"/api/emprestimos/{emprestimo['id']}/devolver")
    assert r.status_code == 200
    assert r.json()["situacao_equipamento"] == "DISPONIVEL"


def test_erro_validacao_entrada(cliente):
    base = {"equipamento_id": NOTEBOOK, "nome": "Ana Exemplo", "email": "ana@exemplo.test", "data_prevista": "2030-01-08"}
    sem_email = {k: v for k, v in base.items() if k != "email"}
    casos = [
        sem_email,
        {**base, "email": "sem-arroba"},
        {**base, "data_prevista": "amanha"},
        {**base, "nome": ""},
        {**base, "nome": "   "},
        {**base, "equipamento_id": "abc"},
    ]
    for corpo in casos:
        r = cliente.post("/api/emprestimos", json=corpo)
        assert r.status_code == 422, corpo
    assert situacao(cliente, NOTEBOOK) == "DISPONIVEL"


# ---------- Correções da revisão de qualidade ----------

def test_erro_id_acima_do_limite_do_banco_nao_gera_500(cliente):
    enorme = 10**20
    assert cliente.get(f"/api/equipamentos/{enorme}").status_code == 422
    assert cliente.post(f"/api/emprestimos/{enorme}/devolver").status_code == 422
    assert emprestar(cliente, enorme, "2030-01-08").status_code == 422


def test_erro_data_prevista_so_aceita_aaaa_mm_dd(cliente):
    for valor in [1893456000, "2030-01-08T00:00:00", "08/01/2030", "2030-02-30"]:
        r = emprestar(cliente, NOTEBOOK, valor)
        assert r.status_code == 422, valor
    assert situacao(cliente, NOTEBOOK) == "DISPONIVEL"
