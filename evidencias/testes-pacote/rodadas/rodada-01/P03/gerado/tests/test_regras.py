"""Testes de borda das regras de negócio (RN-xx), carga inicial e 404."""

from datetime import timedelta

import pytest

from tests.apoio import INICIO_PADRAO, criar_turma, inicio_mais, inscrever, ir_para


def corpo_turma(**extra):
    return {
        "titulo": "Excel avançado",
        "inicio": INICIO_PADRAO.isoformat(),
        "duracao_minutos": 60,
        "modalidade": "ONLINE",
        "vagas": 10,
        **extra,
    }


@pytest.mark.parametrize("vagas, status", [(0, 422), (1, 201), (50, 201), (51, 422), (-1, 422)])
def test_rn_01_vagas_limites(cliente, vagas, status):
    assert cliente.post("/api/turmas", json=corpo_turma(vagas=vagas)).status_code == status


@pytest.mark.parametrize("duracao, status", [(0, 422), (1, 201), (1440, 201), (1441, 422)])
def test_rn_02_duracao_limites(cliente, duracao, status):
    assert cliente.post("/api/turmas", json=corpo_turma(duracao_minutos=duracao)).status_code == status


def test_rn_03_textos_e_email(cliente):
    assert cliente.post("/api/turmas", json=corpo_turma(titulo="")).status_code == 422
    assert cliente.post("/api/turmas", json=corpo_turma(titulo="x" * 200)).status_code == 201
    assert cliente.post("/api/turmas", json=corpo_turma(titulo="x" * 201)).status_code == 422
    assert cliente.post("/api/turmas", json=corpo_turma(modalidade="HIBRIDA")).status_code == 422
    turma = criar_turma(cliente)
    url = f"/api/turmas/{turma['id']}/inscricoes"
    assert cliente.post(url, json={"nome": "Ana", "email": "sem-arroba"}).status_code == 422
    assert cliente.post(url, json={"nome": "", "email": "ana@exemplo.test"}).status_code == 422
    assert cliente.post(url, json={"nome": "x" * 201, "email": "ana@exemplo.test"}).status_code == 422
    assert cliente.post(url, json={"nome": "Ana", "email": "a" * 250 + "@x.test"}).status_code == 422
    assert cliente.post(url, json={"nome": "x" * 200, "email": "ana@exemplo.test"}).status_code == 201


def test_rn_04_inicio_no_passado(cliente, relogio):
    r = cliente.post("/api/turmas", json=corpo_turma(inicio=relogio.agora.isoformat()))
    assert r.status_code == 422
    assert r.json()["erro"] == "INICIO_NO_PASSADO"
    r = cliente.post("/api/turmas", json=corpo_turma(inicio=(relogio.agora + timedelta(minutes=1)).isoformat()))
    assert r.status_code == 201


def test_rn_04_inicio_sem_fuso_recusado(cliente):
    assert cliente.post("/api/turmas", json=corpo_turma(inicio="2030-01-10T09:00:00")).status_code == 422


def test_rn_05_limite_de_ocupacao(cliente):
    turma = criar_turma(cliente, vagas=2)
    situacoes = [inscrever(cliente, turma["id"], n).json()["situacao"] for n in range(1, 4)]
    assert situacoes == ["CONFIRMADA", "CONFIRMADA", "ESPERA"]


def test_rn_06_fila_por_ordem_de_chegada(cliente, relogio):
    turma = criar_turma(cliente, vagas=1)
    for n in range(1, 4):
        inscrever(cliente, turma["id"], n)
        relogio.avancar(minutes=1)
    inscritos = cliente.get(f"/api/turmas/{turma['id']}/inscricoes").json()
    assert [i["email"] for i in inscritos] == [f"pessoa{n}@exemplo.test" for n in range(1, 4)]
    assert [i["posicao_espera"] for i in inscritos] == [None, 1, 2]


def test_rn_07_email_sem_diferenciar_maiusculas(cliente):
    turma = criar_turma(cliente)
    url = f"/api/turmas/{turma['id']}/inscricoes"
    primeira = cliente.post(url, json={"nome": "Ana", "email": "Ana@X.test"})
    assert primeira.json()["email"] == "ana@x.test"
    r = cliente.post(url, json={"nome": "Ana", "email": "ana@x.test"})
    assert r.status_code == 409
    assert r.json()["erro"] == "INSCRICAO_DUPLICADA"


def test_rn_07_duplicada_em_espera_tambem_recusada(cliente):
    turma = criar_turma(cliente, vagas=1)
    inscrever(cliente, turma["id"], 1)
    assert inscrever(cliente, turma["id"], 2).json()["situacao"] == "ESPERA"
    assert inscrever(cliente, turma["id"], 2).status_code == 409


def test_rn_07_reinscricao_apos_cancelar(cliente):
    turma = criar_turma(cliente)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    assert cliente.post(f"/api/inscricoes/{inscricao['id']}/cancelar").status_code == 200
    r = inscrever(cliente, turma["id"], 1)
    assert r.status_code == 201
    assert r.json()["situacao"] == "CONFIRMADA"


@pytest.mark.parametrize(
    "antecedencia, status",
    [(timedelta(hours=24, minutes=1), 201), (timedelta(hours=24), 422), (timedelta(hours=23, minutes=59), 422)],
)
def test_rn_08_prazo_limites(cliente, relogio, antecedencia, status):
    turma = criar_turma(cliente, inicio=relogio.agora + antecedencia)
    r = inscrever(cliente, turma["id"], 1)
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "INSCRICOES_ENCERRADAS"


@pytest.mark.parametrize("minutos, status", [(-1, 200), (0, 422)])
def test_rn_09_cancelar_limites(cliente, relogio, minutos, status):
    turma = criar_turma(cliente)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    ir_para(relogio, inicio_mais(minutos))
    r = cliente.post(f"/api/inscricoes/{inscricao['id']}/cancelar")
    assert r.status_code == status
    if status == 422:
        assert r.json()["erro"] == "CANCELAMENTO_ENCERRADO"


def test_rn_09_cancelar_ja_cancelada(cliente):
    turma = criar_turma(cliente)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    assert cliente.post(f"/api/inscricoes/{inscricao['id']}/cancelar").status_code == 200
    r = cliente.post(f"/api/inscricoes/{inscricao['id']}/cancelar")
    assert r.status_code == 422
    assert r.json()["erro"] == "SITUACAO_NAO_CANCELAVEL"


def test_rn_10_cancelar_espera_nao_promove(cliente):
    turma = criar_turma(cliente, vagas=1)
    inscrever(cliente, turma["id"], 1)
    espera = inscrever(cliente, turma["id"], 2).json()
    r = cliente.post(f"/api/inscricoes/{espera['id']}/cancelar")
    assert r.status_code == 200
    assert r.json()["promovida"] is None
    assert r.json()["cancelada"]["situacao"] == "CANCELADA"
    assert r.json()["cancelada"]["posicao_espera"] is None


def test_rn_10_cancelar_sem_fila_libera_vaga(cliente):
    turma = criar_turma(cliente, vagas=1)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    r = cliente.post(f"/api/inscricoes/{inscricao['id']}/cancelar")
    assert r.json()["promovida"] is None
    assert cliente.get(f"/api/turmas/{turma['id']}").json()["vagas_restantes"] == 1


def test_rn_10_promocao_dentro_das_24h_finais(cliente, relogio):
    turma = criar_turma(cliente, vagas=1)
    a = inscrever(cliente, turma["id"], 1).json()
    b = inscrever(cliente, turma["id"], 2).json()
    ir_para(relogio, inicio_mais(-60))
    r = cliente.post(f"/api/inscricoes/{a['id']}/cancelar")
    assert r.json()["promovida"]["id"] == b["id"]


@pytest.mark.parametrize("minutos, status", [(-1, 422), (0, 200), (1, 200)])
def test_rn_11_presenca_limites(cliente, relogio, minutos, status):
    turma = criar_turma(cliente)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    ir_para(relogio, inicio_mais(minutos))
    r = cliente.post(f"/api/inscricoes/{inscricao['id']}/presenca", json={"situacao": "PRESENTE"})
    assert r.status_code == status
    if status == 200:
        assert r.json()["situacao"] == "PRESENTE"
    else:
        assert r.json()["erro"] == "PRESENCA_ANTES_DO_INICIO"


def test_rn_11_presenca_ja_marcada(cliente, relogio):
    turma = criar_turma(cliente)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    ir_para(relogio, INICIO_PADRAO)
    url = f"/api/inscricoes/{inscricao['id']}/presenca"
    assert cliente.post(url, json={"situacao": "PRESENTE"}).status_code == 200
    r = cliente.post(url, json={"situacao": "AUSENTE"})
    assert r.status_code == 422
    assert r.json()["erro"] == "PRESENCA_SITUACAO_INVALIDA"


def test_rn_11_valor_invalido(cliente, relogio):
    turma = criar_turma(cliente)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    ir_para(relogio, INICIO_PADRAO)
    r = cliente.post(f"/api/inscricoes/{inscricao['id']}/presenca", json={"situacao": "CANCELADA"})
    assert r.status_code == 422


def test_rn_12_taxa_sem_marcacao_e_arredondamento(cliente, relogio):
    turma = criar_turma(cliente, vagas=3)
    ids = [inscrever(cliente, turma["id"], n).json()["id"] for n in range(1, 4)]
    url_taxa = f"/api/turmas/{turma['id']}/taxa-presenca"
    assert cliente.get(url_taxa).json()["taxa_presenca"] is None
    ir_para(relogio, INICIO_PADRAO)
    for i, situacao in zip(ids, ["PRESENTE", "PRESENTE", "AUSENTE"]):
        cliente.post(f"/api/inscricoes/{i}/presenca", json={"situacao": situacao})
    assert cliente.get(url_taxa).json()["taxa_presenca"] == 66.7


def test_rn_13_vagas_restantes_e_turmas_futuras(cliente, relogio):
    turma = criar_turma(cliente, vagas=3)
    inscrever(cliente, turma["id"], 1)
    lista = {t["id"]: t for t in cliente.get("/api/turmas").json()}
    assert lista[turma["id"]]["vagas_restantes"] == 2
    ir_para(relogio, INICIO_PADRAO)
    assert turma["id"] not in [t["id"] for t in cliente.get("/api/turmas").json()]
    assert cliente.get(f"/api/turmas/{turma['id']}").status_code == 200


def test_rn_13_presenca_continua_ocupando_vaga(cliente, relogio):
    turma = criar_turma(cliente, vagas=1)
    inscricao = inscrever(cliente, turma["id"], 1).json()
    ir_para(relogio, INICIO_PADRAO)
    cliente.post(f"/api/inscricoes/{inscricao['id']}/presenca", json={"situacao": "AUSENTE"})
    assert cliente.get(f"/api/turmas/{turma['id']}").json()["vagas_restantes"] == 0


def test_carga_inicial_tres_turmas_futuras(cliente, relogio):
    turmas = cliente.get("/api/turmas").json()
    assert len(turmas) == 3
    for t in turmas:
        assert t["vagas_restantes"] == t["vagas"]
    assert [t["inicio"] for t in turmas] == sorted(t["inicio"] for t in turmas)


def test_erros_404(cliente):
    for metodo, url in [
        ("get", "/api/turmas/999"),
        ("get", "/api/turmas/999/inscricoes"),
        ("get", "/api/turmas/999/taxa-presenca"),
        ("post", "/api/turmas/999/inscricoes"),
    ]:
        corpo = {"json": {"nome": "Ana", "email": "ana@exemplo.test"}} if metodo == "post" else {}
        r = getattr(cliente, metodo)(url, **corpo)
        assert r.status_code == 404, url
        assert r.json()["erro"] == "TURMA_NAO_ENCONTRADA"
    r = cliente.post("/api/inscricoes/999/cancelar")
    assert r.status_code == 404 and r.json()["erro"] == "INSCRICAO_NAO_ENCONTRADA"
    r = cliente.post("/api/inscricoes/999/presenca", json={"situacao": "PRESENTE"})
    assert r.status_code == 404 and r.json()["erro"] == "INSCRICAO_NAO_ENCONTRADA"


def test_entradas_invalidas_retornam_4xx(cliente):
    # Revisão: campo faltando, tipo errado, id inexistente/enorme/não numérico, data sem fuso ou fora da faixa.
    assert cliente.post("/api/turmas", json={"titulo": "Excel"}).status_code == 422
    assert cliente.post("/api/turmas", json=corpo_turma(vagas="muitas")).status_code == 422
    assert cliente.post("/api/turmas", json=corpo_turma(inicio="amanhã")).status_code == 422
    assert cliente.post("/api/turmas", json=corpo_turma(inicio="9999-12-31T23:00:00-03:00")).status_code == 422
    assert cliente.post("/api/turmas", json=corpo_turma(inicio="1999-12-31T23:00:00-03:00")).status_code == 422
    enorme = "99999999999999999999"
    assert cliente.get(f"/api/turmas/{enorme}").status_code == 422
    assert cliente.get("/api/turmas/abc").status_code == 422
    assert cliente.get("/api/turmas/0").status_code == 422
    assert cliente.post(f"/api/inscricoes/{enorme}/cancelar").status_code == 422
    assert cliente.post(f"/api/inscricoes/{enorme}/presenca", json={"situacao": "PRESENTE"}).status_code == 422
    turma = criar_turma(cliente)
    url = f"/api/turmas/{turma['id']}/inscricoes"
    assert cliente.post(url, json={"nome": "Ana"}).status_code == 422
    assert cliente.post(url, json={"nome": 123, "email": "ana@exemplo.test"}).status_code == 422


def test_rn_03_texto_so_com_espacos_recusado(cliente):
    assert cliente.post("/api/turmas", json=corpo_turma(titulo="   ")).status_code == 422
    turma = criar_turma(cliente)
    r = cliente.post(f"/api/turmas/{turma['id']}/inscricoes", json={"nome": "   ", "email": "ana@exemplo.test"})
    assert r.status_code == 422
