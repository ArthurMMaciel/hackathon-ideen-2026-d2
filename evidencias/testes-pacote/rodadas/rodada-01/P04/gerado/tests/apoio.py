"""Atalhos usados pelos testes de férias."""


def solicitar(cliente, colaborador_id: int, inicio: str, fim: str):
    return cliente.post("/api/solicitacoes", json={"colaborador_id": colaborador_id, "inicio": inicio, "fim": fim})


def criar_solicitacao(cliente, colaborador_id: int, inicio: str, fim: str) -> dict:
    r = solicitar(cliente, colaborador_id, inicio, fim)
    assert r.status_code == 201, r.text
    return r.json()


def acao(cliente, solicitacao_id: int, nome: str):
    return cliente.post(f"/api/solicitacoes/{solicitacao_id}/{nome}")


def colaborador(cliente, colaborador_id: int) -> dict:
    r = cliente.get(f"/api/colaboradores/{colaborador_id}")
    assert r.status_code == 200, r.text
    return r.json()


def novo_colaborador(cliente, email: str, equipe: str = "DADOS", saldo: int | None = None) -> dict:
    corpo = {"nome": "Pessoa Teste", "email": email, "equipe": equipe}
    if saldo is not None:
        corpo["saldo"] = saldo
    r = cliente.post("/api/colaboradores", json=corpo)
    assert r.status_code == 201, r.text
    return r.json()
