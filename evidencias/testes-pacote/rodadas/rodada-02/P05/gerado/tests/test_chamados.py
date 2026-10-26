"""Testes do plano da SPEC: critérios de aceite (test_ca_XX), bordas das regras (test_rn_XX) e requisitos."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from app.relogio import FUSO, obter_agora
from tests.conftest import AGORA_INICIAL

DIA = AGORA_INICIAL.date().isoformat()  # 2030-01-07


def abrir(cliente, prioridade="ALTA", **extra):
    corpo = {
        "titulo": "Sem acesso à VPN",
        "descricao": "Erro de certificado ao conectar.",
        "solicitante_nome": "Ana Souza",
        "solicitante_email": "ana.souza@empresa.example",
        "categoria": "ACESSO",
        "prioridade": prioridade,
        **extra,
    }
    resposta = cliente.post("/api/chamados", json=corpo)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def assumir(cliente, id_, responsavel="Carla Mendes"):
    return cliente.post(f"/api/chamados/{id_}/assumir", json={"responsavel": responsavel})


def resolver(cliente, id_, solucao="Certificado reinstalado."):
    return cliente.post(f"/api/chamados/{id_}/resolver", json={"solucao": solucao})


def em_atendimento(cliente, prioridade="ALTA"):
    chamado = abrir(cliente, prioridade)
    assert assumir(cliente, chamado["id"]).status_code == 200
    return chamado


def resolvido(cliente, prioridade="ALTA"):
    chamado = em_atendimento(cliente, prioridade)
    assert resolver(cliente, chamado["id"]).status_code == 200
    return chamado


def relatorio(cliente, inicio=DIA, fim=DIA):
    resposta = cliente.get("/api/relatorio", params={"data_inicial": inicio, "data_final": fim})
    assert resposta.status_code == 200, resposta.text
    return {linha["prioridade"]: linha for linha in resposta.json()["prioridades"]}


def situacao(cliente, id_):
    return cliente.get(f"/api/chamados/{id_}").json()["situacao"]


def item_da_fila(cliente, id_):
    return next(item for item in cliente.get("/api/fila").json() if item["id"] == id_)


# ---------- Critérios de aceite ----------


def test_ca_01_abrir_alta_prazo_8h(cliente):
    chamado = abrir(cliente, "ALTA")
    assert chamado["situacao"] == "ABERTO"
    assert chamado["aberto_em"] == "2030-01-07T09:00:00-03:00"
    assert chamado["prazo_em"] == "2030-01-07T17:00:00-03:00"
    aberto = datetime.fromisoformat(chamado["aberto_em"])
    assert datetime.fromisoformat(chamado["prazo_em"]) - aberto == timedelta(hours=8)


def test_ca_02_assumir_sem_responsavel_recusa(cliente):
    chamado = abrir(cliente)
    for kwargs in ({"json": {}}, {}):
        resposta = cliente.post(f"/api/chamados/{chamado['id']}/assumir", **kwargs)
        assert resposta.status_code == 422
        assert resposta.json()["erro"] == "RESPONSAVEL_OBRIGATORIO"
    assert situacao(cliente, chamado["id"]) == "ABERTO"


def test_ca_03_resolver_aberto_recusa(cliente):
    chamado = abrir(cliente)
    resposta = resolver(cliente, chamado["id"])
    assert resposta.status_code == 409
    assert resposta.json()["erro"] == "TRANSICAO_INVALIDA"
    assert situacao(cliente, chamado["id"]) == "ABERTO"


def test_ca_04_resolver_sem_solucao_recusa(cliente):
    chamado = em_atendimento(cliente)
    resposta = cliente.post(f"/api/chamados/{chamado['id']}/resolver", json={})
    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "SOLUCAO_OBRIGATORIA"
    assert situacao(cliente, chamado["id"]) == "EM_ATENDIMENTO"


def test_ca_05_resolvido_no_prazo_conta_no_relatorio(cliente, relogio):
    chamado = em_atendimento(cliente, "MEDIA")
    relogio.avancar(hours=2)
    assert resolver(cliente, chamado["id"]).status_code == 200
    linha = relatorio(cliente)["MEDIA"]
    assert linha["resolvidos"] == 1
    assert linha["dentro_do_prazo"] == 1
    assert linha["percentual_dentro_do_prazo"] == 100.0


def test_ca_06_critica_4h01_fora_do_prazo(cliente, relogio):
    chamado = em_atendimento(cliente, "CRITICA")
    relogio.avancar(hours=4, minutes=1)
    assert resolver(cliente, chamado["id"]).status_code == 200
    linha = relatorio(cliente)["CRITICA"]
    assert linha["resolvidos"] == 1
    assert linha["dentro_do_prazo"] == 0
    assert linha["percentual_dentro_do_prazo"] == 0.0


def test_ca_07_fila_mostra_atrasado(cliente, relogio):
    chamado = abrir(cliente, "CRITICA")
    relogio.avancar(hours=4, minutes=1)
    assert item_da_fila(cliente, chamado["id"])["indicacao"] == "ATRASADO"


def test_ca_08_reabrir_resolvido_ha_6_dias(cliente, relogio):
    chamado = em_atendimento(cliente)
    relogio.avancar(hours=1)
    assert resolver(cliente, chamado["id"]).status_code == 200
    relogio.avancar(days=6)
    resposta = cliente.post(f"/api/chamados/{chamado['id']}/reabrir")
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "EM_ATENDIMENTO"
    assert resposta.json()["prazo_em"] == chamado["prazo_em"]


def test_ca_09_reabrir_resolvido_ha_8_dias_recusa(cliente, relogio):
    chamado = resolvido(cliente)
    relogio.avancar(days=8)
    resposta = cliente.post(f"/api/chamados/{chamado['id']}/reabrir")
    assert resposta.status_code == 409
    assert resposta.json()["erro"] == "PRAZO_REABERTURA_ENCERRADO"
    assert situacao(cliente, chamado["id"]) == "RESOLVIDO"


def test_ca_10_fechar_aberto_recusa(cliente):
    chamado = abrir(cliente)
    resposta = cliente.post(f"/api/chamados/{chamado['id']}/fechar")
    assert resposta.status_code == 409
    assert resposta.json()["erro"] == "TRANSICAO_INVALIDA"
    assert situacao(cliente, chamado["id"]) == "ABERTO"


# ---------- RN-01 e RN-02: prazo ----------


@pytest.mark.parametrize("prioridade, horas", [("CRITICA", 4), ("ALTA", 8), ("MEDIA", 24), ("BAIXA", 72)])
def test_rn_01_prazo_por_prioridade(cliente, prioridade, horas):
    chamado = abrir(cliente, prioridade)
    esperado = AGORA_INICIAL + timedelta(hours=horas)
    assert datetime.fromisoformat(chamado["prazo_em"]) == esperado


def test_rn_02_prazo_nao_muda_ao_reabrir(cliente, relogio):
    chamado = resolvido(cliente)
    relogio.avancar(days=1)
    reaberto = cliente.post(f"/api/chamados/{chamado['id']}/reabrir").json()
    assert reaberto["prazo_em"] == chamado["prazo_em"]
    assert reaberto["solucao"] is None and reaberto["resolvido_em"] is None
    assert reaberto["responsavel"] == "Carla Mendes"
    relogio.avancar(hours=1)
    novo = resolver(cliente, chamado["id"]).json()
    assert novo["prazo_em"] == chamado["prazo_em"]
    assert datetime.fromisoformat(novo["resolvido_em"]) == relogio.agora


# ---------- RN-03: dentro do prazo, inclusive ----------


def _resolver_critica_apos(cliente, relogio, minutos):
    chamado = em_atendimento(cliente, "CRITICA")
    relogio.avancar(minutes=minutos)
    assert resolver(cliente, chamado["id"]).status_code == 200
    linha = relatorio(cliente)["CRITICA"]
    assert linha["resolvidos"] == 1
    return linha


def test_rn_03_resolver_um_minuto_antes_do_prazo_conta_dentro(cliente, relogio):
    assert _resolver_critica_apos(cliente, relogio, 239)["dentro_do_prazo"] == 1


def test_rn_03_resolver_um_minuto_depois_do_prazo_conta_fora(cliente, relogio):
    assert _resolver_critica_apos(cliente, relogio, 241)["dentro_do_prazo"] == 0


def test_rn_03_resolver_no_limite_do_prazo_conta_dentro(cliente, relogio):
    linha = _resolver_critica_apos(cliente, relogio, 240)
    assert linha["dentro_do_prazo"] == 1
    assert linha["percentual_dentro_do_prazo"] == 100.0


# ---------- RN-04 e RN-05 ----------


@pytest.mark.parametrize("valor", ["", "   "])
def test_rn_04_responsavel_so_espacos_recusa(cliente, valor):
    chamado = abrir(cliente)
    resposta = assumir(cliente, chamado["id"], valor)
    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "RESPONSAVEL_OBRIGATORIO"


def test_rn_04_assumir_registra_responsavel(cliente):
    chamado = abrir(cliente)
    resposta = assumir(cliente, chamado["id"], "  Carla Mendes ")
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "EM_ATENDIMENTO"
    assert resposta.json()["responsavel"] == "Carla Mendes"


def test_rn_05_resolver_registra_solucao_e_resolucao(cliente, relogio):
    chamado = em_atendimento(cliente)
    relogio.avancar(hours=1)
    resposta = resolver(cliente, chamado["id"], "Certificado reinstalado.")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["situacao"] == "RESOLVIDO"
    assert corpo["solucao"] == "Certificado reinstalado."
    assert corpo["resolvido_em"] == "2030-01-07T10:00:00-03:00"


@pytest.mark.parametrize("valor", ["", "  "])
def test_rn_05_solucao_so_espacos_recusa(cliente, valor):
    chamado = em_atendimento(cliente)
    resposta = resolver(cliente, chamado["id"], valor)
    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "SOLUCAO_OBRIGATORIA"


# ---------- RN-06: janela de reabertura ----------


def _reabrir_apos(cliente, relogio, delta):
    chamado = resolvido(cliente)
    relogio.agora = relogio.agora + delta
    return cliente.post(f"/api/chamados/{chamado['id']}/reabrir")


def test_rn_06_reabrir_exatamente_7_dias_aceito(cliente, relogio):
    resposta = _reabrir_apos(cliente, relogio, timedelta(days=7))
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "EM_ATENDIMENTO"


def test_rn_06_reabrir_7_dias_menos_1_minuto_aceito(cliente, relogio):
    resposta = _reabrir_apos(cliente, relogio, timedelta(days=7) - timedelta(minutes=1))
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "EM_ATENDIMENTO"


def test_rn_06_reabrir_7_dias_mais_1_minuto_recusa(cliente, relogio):
    resposta = _reabrir_apos(cliente, relogio, timedelta(days=7) + timedelta(minutes=1))
    assert resposta.status_code == 409
    assert resposta.json()["erro"] == "PRAZO_REABERTURA_ENCERRADO"


# ---------- RN-07: transições ----------


def _preparar(cliente, situacao_desejada):
    chamado = abrir(cliente)
    id_ = chamado["id"]
    if situacao_desejada in ("EM_ATENDIMENTO", "RESOLVIDO", "FECHADO"):
        assert assumir(cliente, id_).status_code == 200
    if situacao_desejada in ("RESOLVIDO", "FECHADO"):
        assert resolver(cliente, id_).status_code == 200
    if situacao_desejada == "FECHADO":
        assert cliente.post(f"/api/chamados/{id_}/fechar").status_code == 200
    return id_


@pytest.mark.parametrize(
    "situacao_inicial, acao",
    [
        ("EM_ATENDIMENTO", "assumir"),
        ("RESOLVIDO", "assumir"),
        ("FECHADO", "assumir"),
        ("RESOLVIDO", "resolver"),
        ("FECHADO", "resolver"),
        ("EM_ATENDIMENTO", "fechar"),
        ("FECHADO", "fechar"),
        ("ABERTO", "reabrir"),
        ("EM_ATENDIMENTO", "reabrir"),
        ("FECHADO", "reabrir"),
    ],
)
def test_rn_07_transicoes_invalidas(cliente, situacao_inicial, acao):
    id_ = _preparar(cliente, situacao_inicial)
    corpo = {"responsavel": "Bruno Lima", "solucao": "Feito."}
    resposta = cliente.post(f"/api/chamados/{id_}/{acao}", json=corpo)
    assert resposta.status_code == 409
    assert resposta.json()["erro"] == "TRANSICAO_INVALIDA"
    assert situacao(cliente, id_) == situacao_inicial


def test_rn_07_fechar_resolvido(cliente):
    chamado = resolvido(cliente)
    resposta = cliente.post(f"/api/chamados/{chamado['id']}/fechar")
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "FECHADO"


# ---------- RN-08 e RF-07: fila ----------


def _indicacao_critica_apos(cliente, relogio, minutos):
    chamado = abrir(cliente, "CRITICA")
    relogio.avancar(minutes=minutos)
    return item_da_fila(cliente, chamado["id"])["indicacao"]


def test_rn_08_fila_no_instante_do_prazo_nao_atrasado(cliente, relogio):
    assert _indicacao_critica_apos(cliente, relogio, 240) == "NO_PRAZO"


def test_rn_08_fila_um_minuto_antes_nao_atrasado(cliente, relogio):
    assert _indicacao_critica_apos(cliente, relogio, 239) == "NO_PRAZO"


def test_rn_08_fila_um_minuto_depois_atrasado(cliente, relogio):
    assert _indicacao_critica_apos(cliente, relogio, 241) == "ATRASADO"


def test_rf_07_fila_ordem_e_filtro(cliente):
    baixa = abrir(cliente, "BAIXA")
    critica = abrir(cliente, "CRITICA")
    media = em_atendimento(cliente, "MEDIA")
    feito = resolvido(cliente, "CRITICA")
    fila = cliente.get("/api/fila").json()
    ids = [item["id"] for item in fila]
    assert feito["id"] not in ids
    assert ids.index(critica["id"]) < ids.index(media["id"]) < ids.index(baixa["id"])
    prazos = [item["prazo_em"] for item in fila]
    assert [datetime.fromisoformat(p) for p in prazos] == sorted(datetime.fromisoformat(p) for p in prazos)
    assert all(item["situacao"] in ("ABERTO", "EM_ATENDIMENTO") for item in fila)


# ---------- RN-09, PR-04, PR-05: relatório ----------


def test_rn_09_periodo_invertido_recusa(cliente):
    resposta = cliente.get("/api/relatorio", params={"data_inicial": "2030-01-08", "data_final": "2030-01-07"})
    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "PERIODO_INVALIDO"


def test_rn_09_periodo_conta_primeiro_e_ultimo_dia(cliente, relogio):
    chamado = em_atendimento(cliente, "BAIXA")
    relogio.agora = datetime(2030, 1, 7, 23, 59, tzinfo=FUSO)
    assert resolver(cliente, chamado["id"]).status_code == 200
    assert relatorio(cliente, "2030-01-07", "2030-01-07")["BAIXA"]["resolvidos"] == 1
    assert relatorio(cliente, "2030-01-06", "2030-01-06")["BAIXA"]["resolvidos"] == 0
    assert relatorio(cliente, "2030-01-08", "2030-01-08")["BAIXA"]["resolvidos"] == 0
    assert relatorio(cliente, "2030-01-01", "2030-01-07")["BAIXA"]["resolvidos"] == 1


def test_rn_09_resolucao_meia_noite_conta_no_dia_seguinte(cliente, relogio):
    chamado = em_atendimento(cliente, "BAIXA")
    relogio.agora = datetime(2030, 1, 8, 0, 0, tzinfo=FUSO)
    assert resolver(cliente, chamado["id"]).status_code == 200
    assert relatorio(cliente, "2030-01-07", "2030-01-07")["BAIXA"]["resolvidos"] == 0
    assert relatorio(cliente, "2030-01-08", "2030-01-08")["BAIXA"]["resolvidos"] == 1


def test_pr_05_percentual_arredondado_e_vazio(cliente, relogio):
    dentro = [em_atendimento(cliente, "ALTA") for _ in range(2)]
    fora = em_atendimento(cliente, "ALTA")
    relogio.avancar(hours=1)
    for chamado in dentro:
        assert resolver(cliente, chamado["id"]).status_code == 200
    relogio.avancar(hours=8)
    assert resolver(cliente, fora["id"]).status_code == 200
    resposta = cliente.get("/api/relatorio", params={"data_inicial": DIA, "data_final": DIA}).json()
    assert [linha["prioridade"] for linha in resposta["prioridades"]] == ["CRITICA", "ALTA", "MEDIA", "BAIXA"]
    linhas = {linha["prioridade"]: linha for linha in resposta["prioridades"]}
    assert linhas["ALTA"]["resolvidos"] == 3
    assert linhas["ALTA"]["percentual_dentro_do_prazo"] == 66.7
    assert linhas["BAIXA"]["resolvidos"] == 0
    assert linhas["BAIXA"]["percentual_dentro_do_prazo"] is None


def test_pr_04_relatorio_conta_fechado_e_ignora_reaberto(cliente, relogio):
    fechado = resolvido(cliente, "MEDIA")
    reaberto = resolvido(cliente, "MEDIA")
    assert cliente.post(f"/api/chamados/{fechado['id']}/fechar").status_code == 200
    assert cliente.post(f"/api/chamados/{reaberto['id']}/reabrir").status_code == 200
    linha = relatorio(cliente)["MEDIA"]
    assert linha["resolvidos"] == 1
    assert linha["dentro_do_prazo"] == 1


# ---------- RF-01, RF-02, RF-12 ----------


def test_rf_02_consultar_e_listar(cliente):
    primeiro = abrir(cliente)
    segundo = abrir(cliente, "BAIXA")
    lista = cliente.get("/api/chamados").json()
    ids = [item["id"] for item in lista]
    assert ids == sorted(ids, reverse=True)
    assert ids.index(segundo["id"]) < ids.index(primeiro["id"])
    assert cliente.get(f"/api/chamados/{primeiro['id']}").json()["titulo"] == "Sem acesso à VPN"
    resposta = cliente.get("/api/chamados/999999")
    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "CHAMADO_NAO_ENCONTRADO"
    for acao in ("assumir", "resolver", "fechar", "reabrir"):
        assert cliente.post(f"/api/chamados/999999/{acao}", json={}).status_code == 404


def test_rf_12_carga_inicial_seis_chamados(cliente):
    lista = cliente.get("/api/chamados").json()
    assert len(lista) == 6
    assert {item["situacao"] for item in lista} == {"ABERTO", "EM_ATENDIMENTO", "RESOLVIDO", "FECHADO"}
    assert {item["prioridade"] for item in lista} == {"BAIXA", "MEDIA", "ALTA", "CRITICA"}
    assert any(item["indicacao"] == "ATRASADO" for item in cliente.get("/api/fila").json())


def test_rf_12_carga_inicial_idempotente(tmp_path, relogio):
    caminho = str(tmp_path / "idem.db")
    for _ in range(2):
        app = criar_app(caminho)
        app.dependency_overrides[obter_agora] = relogio
        with TestClient(app) as c:
            total = len(c.get("/api/chamados").json())
    assert total == 6


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("solicitante_email", "sem-arroba"),
        ("prioridade", "URGENTE"),
        ("categoria", "REDE"),
        ("titulo", "   "),
        ("descricao", "x" * 2001),
    ],
)
def test_rf_01_validacao_entrada(cliente, campo, valor):
    corpo = {
        "titulo": "Sem acesso à VPN",
        "descricao": "Erro.",
        "solicitante_nome": "Ana Souza",
        "solicitante_email": "ana.souza@empresa.example",
        "categoria": "ACESSO",
        "prioridade": "ALTA",
        campo: valor,
    }
    assert cliente.post("/api/chamados", json=corpo).status_code == 422


def test_pr_05_percentual_arredonda_meio_para_cima():
    from app.dominio.relatorio import montar_relatorio

    prazo = AGORA_INICIAL + timedelta(hours=4)
    resolvidos = [
        {"prioridade": "CRITICA", "prazo_em": prazo,
         "resolvido_em": prazo if i == 0 else prazo + timedelta(minutes=1)}
        for i in range(16)
    ]
    linha = next(l for l in montar_relatorio(resolvidos) if l["prioridade"] == "CRITICA")
    assert linha["resolvidos"] == 16 and linha["dentro_do_prazo"] == 1
    assert linha["percentual_dentro_do_prazo"] == 6.3  # 6,25 arredondado meio para cima
