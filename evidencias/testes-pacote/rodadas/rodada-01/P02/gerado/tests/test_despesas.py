"""Testes do plano da SPEC: critérios de aceite (test_ca_XX), bordas de regras (test_rn_XX) e requisitos."""

from datetime import datetime

from app.relogio import FUSO

EMAIL = "diego.teste@empresa.example"


def despesa(**mudancas) -> dict:
    base = {
        "colaborador_nome": "Diego Teste",
        "colaborador_email": EMAIL,
        "data_despesa": "2030-01-05",
        "categoria": "TRANSPORTE",
        "valor": 150.00,
        "descricao": "Táxi",
        "numero_comprovante": "NF-9001",
    }
    base.update(mudancas)
    return base


_contador = iter(range(10_000, 99_999))


def lancar(cliente, **mudancas):
    mudancas.setdefault("numero_comprovante", f"NF-{next(_contador)}")
    return cliente.post("/api/despesas", json=despesa(**mudancas))


def criar_com_situacao(cliente, situacao: str, **mudancas) -> int:
    r = lancar(cliente, **mudancas)
    assert r.status_code == 201, r.text
    despesa_id = r.json()["id"]
    if situacao in ("APROVADA", "PAGA"):
        assert cliente.post(f"/api/despesas/{despesa_id}/aprovar").status_code == 200
    if situacao == "PAGA":
        assert cliente.post(f"/api/despesas/{despesa_id}/pagar").status_code == 200
    if situacao == "RECUSADA":
        r = cliente.post(f"/api/despesas/{despesa_id}/recusar", json={"motivo": "Fora da política"})
        assert r.status_code == 200
    return despesa_id


# ---------- Critérios de aceite ----------

def test_ca_01_lancar_despesa_valida_pendente(cliente):
    r = cliente.post("/api/despesas", json=despesa())
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["situacao"] == "PENDENTE"
    assert isinstance(corpo["id"], int)
    assert corpo["valor"] == 150.0
    assert corpo["colaborador_email"] == EMAIL
    assert corpo["data_despesa"] == "2030-01-05"
    assert corpo["criada_em"] == "2030-01-07T09:00:00-03:00"


def test_ca_02_alimentacao_acima_do_limite_recusada(cliente):
    r = lancar(cliente, categoria="ALIMENTACAO", valor=120.01)
    assert r.status_code == 422
    assert r.json()["erro"] == "LIMITE_EXCEDIDO"
    assert "120,00" in r.json()["mensagem"]


def test_ca_03_hospedagem_no_limite_criada(cliente):
    r = lancar(cliente, categoria="HOSPEDAGEM", valor=450.00)
    assert r.status_code == 201
    assert r.json()["valor"] == 450.0
    assert r.json()["situacao"] == "PENDENTE"


def test_ca_04_data_61_dias_atras_recusada(cliente):
    r = lancar(cliente, data_despesa="2029-11-07")
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_ANTIGA"


def test_ca_05_data_de_amanha_recusada(cliente):
    r = lancar(cliente, data_despesa="2030-01-08")
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_FUTURA"


def test_ca_06_comprovante_duplicado_mesmo_colaborador(cliente):
    primeira = cliente.post("/api/despesas", json=despesa())
    assert primeira.status_code == 201
    segunda = cliente.post("/api/despesas", json=despesa(colaborador_email=EMAIL.upper(), valor=10))
    assert segunda.status_code == 409
    assert segunda.json()["erro"] == "COMPROVANTE_DUPLICADO"
    assert len(cliente.get("/api/despesas", params={"email": EMAIL}).json()) == 1


def test_ca_07_recusar_sem_motivo(cliente):
    despesa_id = criar_com_situacao(cliente, "PENDENTE")
    for corpo in ({}, {"motivo": "   "}, {"motivo": None}):
        r = cliente.post(f"/api/despesas/{despesa_id}/recusar", json=corpo)
        assert r.status_code == 422
        assert r.json()["erro"] == "MOTIVO_OBRIGATORIO"
    r = cliente.post(f"/api/despesas/{despesa_id}/recusar")
    assert r.status_code == 422
    assert r.json()["erro"] == "MOTIVO_OBRIGATORIO"
    assert cliente.get(f"/api/despesas/{despesa_id}").json()["situacao"] == "PENDENTE"


def test_ca_08_pagar_despesa_pendente_recusada(cliente):
    despesa_id = criar_com_situacao(cliente, "PENDENTE")
    r = cliente.post(f"/api/despesas/{despesa_id}/pagar")
    assert r.status_code == 409
    assert r.json()["erro"] == "TRANSICAO_INVALIDA"
    assert cliente.get(f"/api/despesas/{despesa_id}").json()["situacao"] == "PENDENTE"


def test_ca_09_aprovar_e_pagar(cliente):
    despesa_id = criar_com_situacao(cliente, "PENDENTE")
    r = cliente.post(f"/api/despesas/{despesa_id}/aprovar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "APROVADA"
    r = cliente.post(f"/api/despesas/{despesa_id}/pagar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "PAGA"
    assert cliente.get(f"/api/despesas/{despesa_id}").json()["situacao"] == "PAGA"


def test_ca_10_resumo_ignora_recusada_e_pendente(cliente):
    criar_com_situacao(cliente, "PAGA", categoria="TRANSPORTE", valor=100, data_despesa="2030-01-02")
    criar_com_situacao(cliente, "APROVADA", categoria="ALIMENTACAO", valor=50, data_despesa="2030-01-03")
    criar_com_situacao(cliente, "RECUSADA", categoria="OUTROS", valor=70, data_despesa="2030-01-04")
    criar_com_situacao(cliente, "PENDENTE", categoria="HOSPEDAGEM", valor=30, data_despesa="2030-01-05")
    r = cliente.get("/api/relatorios/mensal", params={"mes": "2030-01"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total_geral"] == 150.0
    assert corpo["quantidade"] == 2
    assert corpo["totais_por_categoria"] == {
        "TRANSPORTE": 100.0, "HOSPEDAGEM": 0.0, "ALIMENTACAO": 50.0, "OUTROS": 0.0,
    }


# ---------- Bordas de regras de negócio ----------

def test_rn_01_valor_zero_e_negativo_recusados(cliente):
    for valor in (0, -1):
        r = lancar(cliente, valor=valor)
        assert r.status_code == 422
        assert r.json()["erro"] == "VALOR_INVALIDO"
    r = lancar(cliente, valor=0.01)
    assert r.status_code == 201
    assert r.json()["valor"] == 0.01


def test_rn_01_valor_com_tres_casas_recusado(cliente):
    r = lancar(cliente, valor=10.001)
    assert r.status_code == 422
    assert "detail" in r.json()


def test_rn_02_limites_por_categoria_bordas(cliente):
    limites = {"ALIMENTACAO": "120.00", "HOSPEDAGEM": "450.00", "TRANSPORTE": "1000.00", "OUTROS": "1000.00"}
    for categoria, limite in limites.items():
        centavos = int(limite.replace(".", ""))
        abaixo, no_limite, acima = (f"{(centavos + d) / 100:.2f}" for d in (-1, 0, 1))
        assert lancar(cliente, categoria=categoria, valor=abaixo).status_code == 201
        r = lancar(cliente, categoria=categoria, valor=no_limite)
        assert r.status_code == 201
        assert r.json()["valor"] == float(limite)
        r = lancar(cliente, categoria=categoria, valor=acima)
        assert r.status_code == 422, (categoria, acima)
        assert r.json()["erro"] == "LIMITE_EXCEDIDO"


def test_rn_03_data_hoje_aceita_amanha_recusada(cliente):
    assert lancar(cliente, data_despesa="2030-01-07").status_code == 201
    r = lancar(cliente, data_despesa="2030-01-08")
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_FUTURA"


def test_rn_03_hoje_respeita_fuso_sao_paulo(cliente, relogio):
    relogio.agora = datetime(2030, 1, 7, 23, 30, tzinfo=FUSO)  # em UTC já é dia 8
    r = lancar(cliente, data_despesa="2030-01-08")
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_FUTURA"
    assert lancar(cliente, data_despesa="2030-01-07").status_code == 201


def test_rn_04_data_60_dias_aceita_61_recusada(cliente):
    assert lancar(cliente, data_despesa="2029-11-09").status_code == 201  # 59 dias
    assert lancar(cliente, data_despesa="2029-11-08").status_code == 201  # 60 dias
    r = lancar(cliente, data_despesa="2029-11-07")  # 61 dias
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_ANTIGA"


def test_rn_04_data_passa_a_ser_antiga_com_o_tempo(cliente, relogio):
    assert lancar(cliente, data_despesa="2029-11-08").status_code == 201
    relogio.avancar(days=1)
    r = lancar(cliente, data_despesa="2029-11-08")
    assert r.status_code == 422
    assert r.json()["erro"] == "DATA_ANTIGA"


def test_rn_05_mesmo_comprovante_outro_colaborador_aceito(cliente):
    assert cliente.post("/api/despesas", json=despesa()).status_code == 201
    r = cliente.post("/api/despesas", json=despesa(colaborador_email="outra.pessoa@empresa.example"))
    assert r.status_code == 201


def test_rn_07_transicoes_invalidas(cliente):
    aprovada = criar_com_situacao(cliente, "APROVADA")
    paga = criar_com_situacao(cliente, "PAGA")
    recusada = criar_com_situacao(cliente, "RECUSADA")
    tentativas = [
        (aprovada, "aprovar", None),
        (aprovada, "recusar", {"motivo": "x"}),
        (paga, "aprovar", None),
        (paga, "pagar", None),
        (paga, "recusar", {"motivo": "x"}),
        (recusada, "aprovar", None),
        (recusada, "pagar", None),
        (recusada, "recusar", {"motivo": "x"}),
    ]
    for despesa_id, acao, corpo in tentativas:
        r = cliente.post(f"/api/despesas/{despesa_id}/{acao}", json=corpo)
        assert r.status_code == 409, (despesa_id, acao)
        assert r.json()["erro"] == "TRANSICAO_INVALIDA"


def test_rn_08_recusar_com_motivo(cliente, relogio):
    despesa_id = criar_com_situacao(cliente, "PENDENTE")
    relogio.avancar(hours=1)
    r = cliente.post(f"/api/despesas/{despesa_id}/recusar", json={"motivo": "  Fora da política  "})
    assert r.status_code == 200
    assert r.json()["situacao"] == "RECUSADA"
    assert r.json()["motivo_recusa"] == "Fora da política"
    assert r.json()["atualizada_em"] == "2030-01-07T10:00:00-03:00"


def test_rn_09_excluir_pendente_e_nao_pendente(cliente):
    pendente = criar_com_situacao(cliente, "PENDENTE")
    r = cliente.delete(f"/api/despesas/{pendente}")
    assert r.status_code == 204
    assert cliente.get(f"/api/despesas/{pendente}").status_code == 404
    for situacao in ("APROVADA", "RECUSADA", "PAGA"):
        despesa_id = criar_com_situacao(cliente, situacao)
        r = cliente.delete(f"/api/despesas/{despesa_id}")
        assert r.status_code == 409
        assert r.json()["erro"] == "EXCLUSAO_NAO_PERMITIDA"
        assert cliente.get(f"/api/despesas/{despesa_id}").json()["situacao"] == situacao


# ---------- Requisitos ----------

def test_rf_06_filtros_por_email_e_situacao(cliente):
    a = criar_com_situacao(cliente, "PENDENTE", data_despesa="2030-01-01")
    b = criar_com_situacao(cliente, "APROVADA", data_despesa="2030-01-03")
    c = criar_com_situacao(cliente, "PENDENTE", colaborador_email="outra.pessoa@empresa.example")

    por_email = cliente.get("/api/despesas", params={"email": EMAIL.upper()}).json()
    assert [d["id"] for d in por_email] == [b, a]  # PR-09: data mais recente primeiro

    pendentes = cliente.get("/api/despesas", params={"situacao": "PENDENTE"}).json()
    ids_pendentes = {d["id"] for d in pendentes}
    assert {a, c} <= ids_pendentes and b not in ids_pendentes
    assert all(d["situacao"] == "PENDENTE" for d in pendentes)

    ambos = cliente.get("/api/despesas", params={"email": EMAIL, "situacao": "APROVADA"}).json()
    assert [d["id"] for d in ambos] == [b]

    todas = cliente.get("/api/despesas").json()
    assert len(todas) == 5 + 3  # carga inicial + criadas aqui
    datas = [d["data_despesa"] for d in todas]
    assert datas == sorted(datas, reverse=True)


def test_rf_06_despesa_inexistente_404(cliente):
    for metodo, caminho in (
        ("get", "/api/despesas/9999"),
        ("post", "/api/despesas/9999/aprovar"),
        ("post", "/api/despesas/9999/pagar"),
        ("delete", "/api/despesas/9999"),
    ):
        r = getattr(cliente, metodo)(caminho)
        assert r.status_code == 404
        assert r.json()["erro"] == "DESPESA_NAO_ENCONTRADA"
    r = cliente.post("/api/despesas/9999/recusar", json={"motivo": "x"})
    assert r.status_code == 404


def test_rf_07_resumo_considera_mes_pela_data_da_despesa(cliente):
    criar_com_situacao(cliente, "APROVADA", data_despesa="2029-12-31", valor=10)
    criar_com_situacao(cliente, "APROVADA", data_despesa="2030-01-01", valor=20)
    jan = cliente.get("/api/relatorios/mensal", params={"mes": "2030-01"}).json()
    dez = cliente.get("/api/relatorios/mensal", params={"mes": "2029-12"}).json()
    assert jan["total_geral"] == 20.0
    assert dez["total_geral"] == 10.0
    vazio = cliente.get("/api/relatorios/mensal", params={"mes": "2031-06"}).json()
    assert vazio["total_geral"] == 0.0
    assert set(vazio["totais_por_categoria"]) == {"TRANSPORTE", "HOSPEDAGEM", "ALIMENTACAO", "OUTROS"}


def test_rf_11_carga_inicial_cinco_despesas(tmp_path):
    from fastapi.testclient import TestClient

    from app.main import criar_app

    caminho = str(tmp_path / "carga.db")
    for _ in range(2):  # reinício não duplica
        with TestClient(criar_app(caminho)) as c:
            todas = c.get("/api/despesas").json()
    assert len(todas) == 5
    assert sorted(d["situacao"] for d in todas) == ["APROVADA", "PAGA", "PENDENTE", "PENDENTE", "RECUSADA"]
    recusada = next(d for d in todas if d["situacao"] == "RECUSADA")
    assert recusada["motivo_recusa"]
    assert all(d["colaborador_email"].endswith("@empresa.example") for d in todas)


def test_validacao_formato_422(cliente):
    sem_campo = despesa()
    del sem_campo["descricao"]
    casos = [
        sem_campo,
        despesa(categoria="VIAGEM"),
        despesa(colaborador_email="sem-arroba"),
        despesa(data_despesa="2030-01-05T10:00:00-03:00"),
        despesa(data_despesa="05/01/2030"),
        despesa(valor="abc"),
        despesa(colaborador_nome="   "),
    ]
    for corpo in casos:
        assert cliente.post("/api/despesas", json=corpo).status_code == 422, corpo
    assert cliente.get("/api/relatorios/mensal").status_code == 422
    assert cliente.get("/api/relatorios/mensal", params={"mes": "2030-13"}).status_code == 422
    assert cliente.get("/api/despesas", params={"situacao": "CANCELADA"}).status_code == 422
    assert cliente.get("/api/despesas/abc").status_code == 422


def test_revisao_entradas_fora_da_faixa_retornam_4xx(cliente):
    # Achados R-01 e R-02 da revisão: antes retornavam 500.
    for caminho in ("/api/despesas/99999999999999999999", "/api/despesas/0"):
        assert cliente.get(caminho).status_code == 422
    assert cliente.post("/api/despesas/99999999999999999999/aprovar").status_code == 422
    assert cliente.delete("/api/despesas/99999999999999999999").status_code == 422
    for mes in ("0000-01", "9999-12", "2030-00"):
        assert cliente.get("/api/relatorios/mensal", params={"mes": mes}).status_code == 422
    assert cliente.get("/api/relatorios/mensal", params={"mes": "2999-12"}).status_code == 200
    assert cliente.post("/api/despesas", json=despesa(data_despesa="2030-02-30")).status_code == 422
    assert cliente.post("/api/despesas/1/recusar", json="texto").status_code == 422
