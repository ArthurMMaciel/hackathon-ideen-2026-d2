"""Entradas inválidas comuns: sempre 4xx, nunca 500 (revisão de qualidade)."""

import pytest

VALIDO = {
    "titulo": "Teste", "descricao": "Desc", "solicitante_nome": "Ana",
    "solicitante_email": "ana@example.com", "categoria": "ACESSO", "prioridade": "ALTA",
}


@pytest.mark.parametrize("campo", list(VALIDO))
def test_campo_faltando_422(cliente, campo):
    corpo = {k: v for k, v in VALIDO.items() if k != campo}
    assert cliente.post("/api/chamados", json=corpo).status_code == 422


def test_tipo_errado_422(cliente):
    assert cliente.post("/api/chamados", json={**VALIDO, "titulo": 123}).status_code == 422
    assert cliente.get("/api/chamados/abc").status_code == 422
    assert cliente.post("/api/chamados/1/assumir", json={"responsavel": 123}).status_code == 422
    assert cliente.post("/api/chamados/1/assumir", json=["x"]).status_code == 422


@pytest.mark.parametrize("caminho", ["/api/chamados/{}", "/api/chamados/{}/fechar"])
@pytest.mark.parametrize("valor", ["0", "-1", "99999999999999999999999"])
def test_id_fora_da_faixa_nao_gera_500(cliente, caminho, valor):
    url = caminho.format(valor)
    r = cliente.get(url) if url.count("/") == 3 else cliente.post(url)
    assert 400 <= r.status_code < 500


def test_campo_desconhecido_422(cliente):
    assert cliente.post("/api/chamados", json={**VALIDO, "situacao": "RESOLVIDO"}).status_code == 422


@pytest.mark.parametrize("params", [
    {"data_inicial": "2030-01-07"},
    {"data_inicial": "abc", "data_final": "2030-01-07"},
    {"data_inicial": "2030-13-01", "data_final": "2030-12-31"},
    {"data_inicial": "0001-01-01", "data_final": "9999-12-31"},
])
def test_relatorio_datas_invalidas_nao_gera_500(cliente, params):
    r = cliente.get("/api/relatorios/prazo", params=params)
    assert r.status_code == 422


def test_relatorio_periodo_amplo_funciona(cliente):
    r = cliente.get("/api/relatorios/prazo", params={"data_inicial": "0001-01-01", "data_final": "9999-12-30"})
    assert r.status_code == 200
    assert len(r.json()["prioridades"]) == 4
