"""Testes dos critérios de aceite (CA-xx) e das regras de negócio (RN-xx)."""

from datetime import datetime, timedelta

import pytest

from app.relogio import FUSO
from tests.conftest import AGORA_INICIAL


def abrir(cliente, prioridade="ALTA", titulo="Sem acesso à VPN", **extra):
    corpo = {
        "titulo": titulo,
        "descricao": "Não conecta desde cedo",
        "solicitante_nome": "Ana Exemplo",
        "solicitante_email": "ana.exemplo@example.com",
        "categoria": "ACESSO",
        "prioridade": prioridade,
        **extra,
    }
    r = cliente.post("/api/chamados", json=corpo)
    assert r.status_code == 201, r.text
    return r.json()


def assumir(cliente, cid, responsavel="Carla Suporte"):
    return cliente.post(f"/api/chamados/{cid}/assumir", json={"responsavel": responsavel})


def resolver(cliente, cid, solucao="Senha redefinida"):
    return cliente.post(f"/api/chamados/{cid}/resolver", json={"solucao": solucao})


def abrir_e_resolver(cliente, relogio, prioridade="ALTA", depois=None):
    c = abrir(cliente, prioridade)
    assert assumir(cliente, c["id"]).status_code == 200
    if depois:
        relogio.avancar(**depois)
    r = resolver(cliente, c["id"])
    assert r.status_code == 200, r.text
    return r.json()


def relatorio(cliente, inicial="2030-01-07", final="2030-01-07"):
    r = cliente.get("/api/relatorios/prazo", params={"data_inicial": inicial, "data_final": final})
    assert r.status_code == 200, r.text
    return {p["prioridade"]: p for p in r.json()["prioridades"]}


def dt(texto):
    return datetime.fromisoformat(texto)


# ---------- Critérios de aceite ----------

def test_ca_01_abrir_alta_prazo_8h(cliente):
    c = abrir(cliente, "ALTA")
    assert c["situacao"] == "ABERTO"
    assert dt(c["aberto_em"]) == AGORA_INICIAL
    assert dt(c["prazo"]) == AGORA_INICIAL + timedelta(hours=8)
    assert dt(c["prazo"]) - dt(c["aberto_em"]) == timedelta(hours=8)


def test_ca_02_assumir_sem_responsavel_recusa(cliente):
    c = abrir(cliente)
    for corpo in ({}, {"responsavel": "   "}, {"responsavel": None}):
        r = cliente.post(f"/api/chamados/{c['id']}/assumir", json=corpo)
        assert r.status_code == 422
        assert r.json()["erro"] == "RESPONSAVEL_OBRIGATORIO"
    assert cliente.get(f"/api/chamados/{c['id']}").json()["situacao"] == "ABERTO"


def test_ca_03_resolver_aberto_recusa(cliente):
    c = abrir(cliente)
    r = resolver(cliente, c["id"])
    assert r.status_code == 422
    assert r.json()["erro"] == "TRANSICAO_INVALIDA"
    assert cliente.get(f"/api/chamados/{c['id']}").json()["situacao"] == "ABERTO"


def test_ca_04_resolver_sem_solucao_recusa(cliente):
    c = abrir(cliente)
    assert assumir(cliente, c["id"]).status_code == 200
    for corpo in ({}, {"solucao": ""}, {"solucao": "  "}):
        r = cliente.post(f"/api/chamados/{c['id']}/resolver", json=corpo)
        assert r.status_code == 422
        assert r.json()["erro"] == "SOLUCAO_OBRIGATORIA"
    atual = cliente.get(f"/api/chamados/{c['id']}").json()
    assert atual["situacao"] == "EM_ATENDIMENTO"
    assert atual["resolvido_em"] is None


def test_ca_05_resolvido_no_prazo_conta_dentro(cliente, relogio):
    c = abrir_e_resolver(cliente, relogio, "MEDIA", depois={"hours": 2})
    assert c["dentro_do_prazo"] is True
    media = relatorio(cliente)["MEDIA"]
    assert media["resolvidos"] == 1
    assert media["dentro_do_prazo"] == 1
    assert media["percentual_dentro_do_prazo"] == 100.0


def test_ca_06_critica_4h01_fora_do_prazo(cliente, relogio):
    c = abrir_e_resolver(cliente, relogio, "CRITICA", depois={"hours": 4, "minutes": 1})
    assert c["dentro_do_prazo"] is False
    critica = relatorio(cliente)["CRITICA"]
    assert critica["resolvidos"] == 1
    assert critica["dentro_do_prazo"] == 0
    assert critica["percentual_dentro_do_prazo"] == 0.0


def test_ca_07_fila_prazo_vencido_atrasado(cliente, relogio):
    c = abrir(cliente, "CRITICA")
    relogio.avancar(hours=4, minutes=1)
    fila = {item["id"]: item for item in cliente.get("/api/chamados/fila").json()}
    assert fila[c["id"]]["indicacao"] == "ATRASADO"


def test_ca_08_reabrir_6_dias(cliente, relogio):
    c = abrir_e_resolver(cliente, relogio)
    relogio.avancar(days=6)
    r = cliente.post(f"/api/chamados/{c['id']}/reabrir")
    assert r.status_code == 200, r.text
    assert r.json()["situacao"] == "EM_ATENDIMENTO"


def test_ca_09_reabrir_8_dias_recusa(cliente, relogio):
    c = abrir_e_resolver(cliente, relogio)
    relogio.avancar(days=8)
    r = cliente.post(f"/api/chamados/{c['id']}/reabrir")
    assert r.status_code == 422
    assert r.json()["erro"] == "REABERTURA_EXPIRADA"
    assert cliente.get(f"/api/chamados/{c['id']}").json()["situacao"] == "RESOLVIDO"


def test_ca_10_fechar_aberto_recusa(cliente):
    c = abrir(cliente)
    r = cliente.post(f"/api/chamados/{c['id']}/fechar")
    assert r.status_code == 422
    assert r.json()["erro"] == "TRANSICAO_INVALIDA"
    assert cliente.get(f"/api/chamados/{c['id']}").json()["situacao"] == "ABERTO"


# ---------- Regras de negócio ----------

@pytest.mark.parametrize("prioridade,horas", [("CRITICA", 4), ("ALTA", 8), ("MEDIA", 24), ("BAIXA", 72)])
def test_rn_01_prazo_por_prioridade(cliente, prioridade, horas):
    c = abrir(cliente, prioridade)
    assert dt(c["prazo"]) == AGORA_INICIAL + timedelta(hours=horas)


def test_rn_02_prazo_nao_muda_ao_reabrir(cliente, relogio):
    c = abrir_e_resolver(cliente, relogio, "ALTA", depois={"hours": 1})
    prazo_original = c["prazo"]
    relogio.avancar(days=1)
    r = cliente.post(f"/api/chamados/{c['id']}/reabrir")
    assert r.status_code == 200
    reaberto = r.json()
    assert reaberto["prazo"] == prazo_original
    assert reaberto["solucao"] is None and reaberto["resolvido_em"] is None
    assert reaberto["responsavel"] == "Carla Suporte"
    # Resolvido de novo após o prazo original: fora do prazo.
    assert resolver(cliente, c["id"]).json()["dentro_do_prazo"] is False


@pytest.mark.parametrize("minutos,esperado", [(239, True), (240, True), (241, False)])
def test_rn_03_borda_prazo(cliente, relogio, minutos, esperado):
    c = abrir_e_resolver(cliente, relogio, "CRITICA", depois={"minutes": minutos})
    assert c["dentro_do_prazo"] is esperado
    critica = relatorio(cliente)["CRITICA"]
    assert critica["dentro_do_prazo"] == (1 if esperado else 0)


def test_rn_05_resolver_registra_data(cliente, relogio):
    c = abrir_e_resolver(cliente, relogio, "BAIXA", depois={"minutes": 30})
    assert c["situacao"] == "RESOLVIDO"
    assert c["solucao"] == "Senha redefinida"
    assert dt(c["resolvido_em"]) == AGORA_INICIAL + timedelta(minutes=30)


@pytest.mark.parametrize("delta,status", [
    ({"days": 6, "hours": 23, "minutes": 59}, 200),
    ({"days": 7}, 200),
    ({"days": 7, "minutes": 1}, 422),
])
def test_rn_06_borda_reabertura(cliente, relogio, delta, status):
    c = abrir_e_resolver(cliente, relogio)
    relogio.avancar(**delta)
    r = cliente.post(f"/api/chamados/{c['id']}/reabrir")
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "REABERTURA_EXPIRADA"
    else:
        assert r.json()["situacao"] == "EM_ATENDIMENTO"


def _em_situacao(cliente, situacao):
    c = abrir(cliente)
    if situacao == "ABERTO":
        return c["id"]
    assumir(cliente, c["id"])
    if situacao == "EM_ATENDIMENTO":
        return c["id"]
    resolver(cliente, c["id"])
    if situacao == "RESOLVIDO":
        return c["id"]
    cliente.post(f"/api/chamados/{c['id']}/fechar")
    return c["id"]


@pytest.mark.parametrize("situacao,acao,corpo", [
    ("EM_ATENDIMENTO", "assumir", {"responsavel": "X"}),
    ("EM_ATENDIMENTO", "fechar", None),
    ("EM_ATENDIMENTO", "reabrir", None),
    ("ABERTO", "reabrir", None),
    ("RESOLVIDO", "assumir", {"responsavel": "X"}),
    ("RESOLVIDO", "resolver", {"solucao": "Y"}),
    ("FECHADO", "assumir", {"responsavel": "X"}),
    ("FECHADO", "resolver", {"solucao": "Y"}),
    ("FECHADO", "fechar", None),
    ("FECHADO", "reabrir", None),
])
def test_rn_07_transicoes_invalidas(cliente, situacao, acao, corpo):
    cid = _em_situacao(cliente, situacao)
    r = cliente.post(f"/api/chamados/{cid}/{acao}", json=corpo)
    assert r.status_code == 422
    assert r.json()["erro"] == "TRANSICAO_INVALIDA"
    assert cliente.get(f"/api/chamados/{cid}").json()["situacao"] == situacao


def test_rn_07_fechar_resolvido(cliente):
    cid = _em_situacao(cliente, "RESOLVIDO")
    r = cliente.post(f"/api/chamados/{cid}/fechar")
    assert r.status_code == 200
    assert r.json()["situacao"] == "FECHADO"
    assert r.json()["resolvido_em"] is not None


@pytest.mark.parametrize("minutos,indicacao", [(239, None), (240, None), (241, "ATRASADO")])
def test_rn_08_borda_atrasado(cliente, relogio, minutos, indicacao):
    c = abrir(cliente, "CRITICA")
    relogio.avancar(minutes=minutos)
    fila = {item["id"]: item for item in cliente.get("/api/chamados/fila").json()}
    assert fila[c["id"]]["indicacao"] == indicacao


def test_rn_08_fila_ordenada_pelo_prazo(cliente):
    baixa = abrir(cliente, "BAIXA")
    critica = abrir(cliente, "CRITICA")
    alta = abrir(cliente, "ALTA")
    resolvido = _em_situacao(cliente, "RESOLVIDO")
    fila = cliente.get("/api/chamados/fila").json()
    ids = [item["id"] for item in fila]
    assert resolvido not in ids
    nossos = [i for i in ids if i in (baixa["id"], critica["id"], alta["id"])]
    assert nossos == [critica["id"], alta["id"], baixa["id"]]
    prazos = [dt(item["prazo"]) for item in fila]
    assert prazos == sorted(prazos)
    assert all(item["situacao"] in ("ABERTO", "EM_ATENDIMENTO") for item in fila)


@pytest.mark.parametrize("campo,valor", [
    ("solicitante_email", "sem-arroba"),
    ("solicitante_email", "a@b"),
    ("prioridade", "URGENTE"),
    ("categoria", "REDE"),
    ("titulo", ""),
    ("titulo", "   "),
    ("solicitante_nome", ""),
])
def test_rn_09_validacao_campos(cliente, campo, valor):
    corpo = {
        "titulo": "Teste", "descricao": "Desc", "solicitante_nome": "Ana",
        "solicitante_email": "ana@example.com", "categoria": "ACESSO", "prioridade": "ALTA",
    }
    corpo[campo] = valor
    assert cliente.post("/api/chamados", json=corpo).status_code == 422


@pytest.mark.parametrize("tamanho,status", [(199, 201), (200, 201), (201, 422)])
def test_rn_09_limite_titulo(cliente, tamanho, status):
    corpo = {
        "titulo": "a" * tamanho, "descricao": "Desc", "solicitante_nome": "Ana",
        "solicitante_email": "ana@example.com", "categoria": "ACESSO", "prioridade": "ALTA",
    }
    assert cliente.post("/api/chamados", json=corpo).status_code == status


def test_rn_10_periodo_invalido(cliente):
    r = cliente.get("/api/relatorios/prazo", params={"data_inicial": "2030-01-08", "data_final": "2030-01-07"})
    assert r.status_code == 422
    assert r.json()["erro"] == "PERIODO_INVALIDO"


def test_rn_10_bordas_periodo(cliente, relogio):
    # Abre às 09:00 do dia 06 e resolve às 00:00 do dia 07 (dia inicial do período).
    relogio.agora = datetime(2030, 1, 6, 9, 0, tzinfo=FUSO)
    abrir_e_resolver(cliente, relogio, "BAIXA", depois={"hours": 15})
    # Resolvido às 23:59 do dia 08 (dia final do período).
    relogio.agora = datetime(2030, 1, 8, 20, 0, tzinfo=FUSO)
    abrir_e_resolver(cliente, relogio, "BAIXA", depois={"hours": 3, "minutes": 59})
    # Resolvido às 00:00 do dia 09: fora do período.
    relogio.agora = datetime(2030, 1, 8, 20, 0, tzinfo=FUSO)
    abrir_e_resolver(cliente, relogio, "BAIXA", depois={"hours": 4})
    # Resolvido às 23:59 do dia 06: fora do período.
    relogio.agora = datetime(2030, 1, 6, 20, 0, tzinfo=FUSO)
    abrir_e_resolver(cliente, relogio, "BAIXA", depois={"hours": 3, "minutes": 59})
    baixa = relatorio(cliente, "2030-01-07", "2030-01-08")["BAIXA"]
    assert baixa["resolvidos"] == 2
    assert baixa["percentual_dentro_do_prazo"] == 100.0
    # Prioridade sem resolvidos aparece com zero e percentual vazio.
    assert relatorio(cliente, "2030-01-07", "2030-01-08")["ALTA"] == {
        "prioridade": "ALTA", "resolvidos": 0, "dentro_do_prazo": 0, "percentual_dentro_do_prazo": None,
    }


def test_rf_02_consultar_e_404(cliente):
    c = abrir(cliente)
    r = cliente.get(f"/api/chamados/{c['id']}")
    assert r.status_code == 200 and r.json()["titulo"] == "Sem acesso à VPN"
    r = cliente.get("/api/chamados/999999")
    assert r.status_code == 404
    assert r.json()["erro"] == "CHAMADO_NAO_ENCONTRADO"
    for acao in ("assumir", "resolver", "fechar", "reabrir"):
        assert cliente.post(f"/api/chamados/999999/{acao}", json={}).status_code == 404


def test_rf_12_carga_inicial(cliente):
    chamados = cliente.get("/api/chamados").json()
    assert len(chamados) == 6
    situacoes = sorted(c["situacao"] for c in chamados)
    assert situacoes == sorted(["ABERTO", "ABERTO", "EM_ATENDIMENTO", "RESOLVIDO", "RESOLVIDO", "FECHADO"])
    assert {c["prioridade"] for c in chamados} == {"BAIXA", "MEDIA", "ALTA", "CRITICA"}
    assert {c["categoria"] for c in chamados} == {"ACESSO", "HARDWARE", "SOFTWARE"}
    assert all(c["solicitante_email"].endswith("@example.com") for c in chamados)
