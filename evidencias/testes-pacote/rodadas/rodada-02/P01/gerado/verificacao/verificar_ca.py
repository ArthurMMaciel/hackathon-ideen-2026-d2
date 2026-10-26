"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, resumo, servidor

AGORA = "2030-01-07T09:00:00-03:00"  # hoje = 2030-01-07
DOIS_DIAS_DEPOIS = "2030-01-09T09:00:00-03:00"


def cadastrar(api, patrimonio: str, tipo: str) -> int:
    r = api.post("/api/equipamentos", json={"patrimonio": patrimonio, "tipo": tipo, "descricao": f"{tipo} da verificação"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def emprestar(api, equipamento_id: int, prevista: str, email: str):
    return api.post(
        "/api/emprestimos",
        json={"equipamento_id": equipamento_id, "nome": "Pessoa Fictícia", "email": email, "data_prevista": prevista},
    )


def situacao(api, equipamento_id: int) -> str:
    return api.get(f"/api/equipamentos/{equipamento_id}").json()["situacao"]


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", resumo(r),
                    r.status_code == 200 and "<html" in r.text.lower() and "Empréstimo de equipamentos" in r.text)

        # CA-01: notebook disponível, prevista +7 dias
        nb = cadastrar(api, "EQ-0101", "NOTEBOOK")
        r = emprestar(api, nb, "2030-01-14", "ca01@exemplo.com")
        sit = situacao(api, nb)
        v.registrar("CA-01", "Emprestar notebook disponível com prevista em 7 dias",
                    "HTTP 201, status=ABERTO; equipamento EMPRESTADO",
                    resumo(r, "status", "data_retirada", "data_prevista") + f"; equipamento situacao={sit}",
                    r.status_code == 201 and r.json()["status"] == "ABERTO" and sit == "EMPRESTADO")

        # CA-02: mesmo notebook, já emprestado
        r = emprestar(api, nb, "2030-01-10", "ca02@exemplo.com")
        v.registrar("CA-02", "Emprestar equipamento já emprestado", "HTTP 409, erro=EQUIPAMENTO_INDISPONIVEL",
                    resumo(r, "erro", "mensagem"),
                    r.status_code == 409 and r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL")

        # CA-03: headset da carga inicial em manutenção
        manut = next(e for e in api.get("/api/equipamentos").json() if e["situacao"] == "MANUTENCAO")
        r = emprestar(api, manut["id"], "2030-01-08", "ca03@exemplo.com")
        v.registrar("CA-03", f"Emprestar {manut['patrimonio']} ({manut['tipo']}) em manutenção",
                    "HTTP 409, erro=EQUIPAMENTO_INDISPONIVEL", resumo(r, "erro", "mensagem"),
                    r.status_code == 409 and r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL")

        # CA-04: notebook com prevista +15 dias
        nb2 = cadastrar(api, "EQ-0102", "NOTEBOOK")
        r = emprestar(api, nb2, "2030-01-22", "ca04@exemplo.com")
        sit = situacao(api, nb2)
        v.registrar("CA-04", "Emprestar notebook com prevista em 15 dias", "HTTP 422, erro=PRAZO_EXCEDIDO",
                    resumo(r, "erro", "mensagem") + f"; equipamento situacao={sit}",
                    r.status_code == 422 and r.json()["erro"] == "PRAZO_EXCEDIDO" and sit == "DISPONIVEL")

        # CA-05: projetor com prevista +3 dias
        pj = cadastrar(api, "EQ-0103", "PROJETOR")
        r = emprestar(api, pj, "2030-01-10", "ca05@exemplo.com")
        v.registrar("CA-05", "Emprestar projetor com prevista em 3 dias", "HTTP 201, status=ABERTO",
                    resumo(r, "status", "data_retirada", "data_prevista"),
                    r.status_code == 201 and r.json()["status"] == "ABERTO")

        # CA-06: mesma pessoa com 2 abertos pede o terceiro
        ids = [cadastrar(api, f"EQ-010{n}", "HEADSET") for n in (4, 5, 6)]
        primeiros = [emprestar(api, i, "2030-01-08", "ca06@exemplo.com").status_code for i in ids[:2]]
        r = emprestar(api, ids[2], "2030-01-08", "ca06@exemplo.com")
        v.registrar("CA-06", "Pessoa com 2 empréstimos em aberto pede um terceiro",
                    "2 x HTTP 201, depois HTTP 409 erro=LIMITE_EMPRESTIMOS",
                    f"anteriores={primeiros}; " + resumo(r, "erro", "mensagem"),
                    primeiros == [201, 201] and r.status_code == 409 and r.json()["erro"] == "LIMITE_EMPRESTIMOS")

        # CA-07: devolver sem defeito
        eq7 = cadastrar(api, "EQ-0107", "NOTEBOOK")
        emp7 = emprestar(api, eq7, "2030-01-10", "ca07@exemplo.com").json()
        r = api.post(f"/api/emprestimos/{emp7['id']}/devolver", json={"defeito": False})
        sit = situacao(api, eq7)
        v.registrar("CA-07", "Devolver sem defeito", "HTTP 200, status=DEVOLVIDO; equipamento DISPONIVEL",
                    resumo(r, "status", "data_devolucao", "defeito") + f"; equipamento situacao={sit}",
                    r.status_code == 200 and r.json()["status"] == "DEVOLVIDO" and sit == "DISPONIVEL")

        # CA-10: devolver de novo o empréstimo do CA-07
        r = api.post(f"/api/emprestimos/{emp7['id']}/devolver", json={"defeito": False})
        v.registrar("CA-10", "Devolver empréstimo já devolvido", "HTTP 409, erro=EMPRESTIMO_JA_DEVOLVIDO",
                    resumo(r, "erro", "mensagem"),
                    r.status_code == 409 and r.json()["erro"] == "EMPRESTIMO_JA_DEVOLVIDO")

        # CA-08: devolver com defeito
        eq8 = cadastrar(api, "EQ-0108", "PROJETOR")
        emp8 = emprestar(api, eq8, "2030-01-09", "ca08@exemplo.com").json()
        r = api.post(f"/api/emprestimos/{emp8['id']}/devolver", json={"defeito": True})
        sit = situacao(api, eq8)
        v.registrar("CA-08", "Devolver com defeito", "HTTP 200; equipamento MANUTENCAO",
                    resumo(r, "status", "defeito") + f"; equipamento situacao={sit}",
                    r.status_code == 200 and sit == "MANUTENCAO")

        # CA-09 (parte 1): empréstimo com prevista amanhã (2030-01-08)
        eq9 = cadastrar(api, "EQ-0109", "HEADSET")
        emp9 = emprestar(api, eq9, "2030-01-08", "ca09@exemplo.com").json()

    # CA-09 (parte 2): o tempo passa; servidor reiniciado em 2030-01-09, a prevista virou "ontem"
    with servidor(DOIS_DIAS_DEPOIS, banco) as api:
        r = api.get("/api/emprestimos/atrasados")
        item = next((a for a in r.json() if a["id"] == emp9["id"]), None)
        detalhe = (f"; emprestimo {emp9['id']} prevista={item['data_prevista']} status={item['status']} "
                   f"dias_atraso={item['dias_atraso']}") if item else "; empréstimo ausente"
        v.registrar("CA-09", "Prevista ontem (2030-01-08), hoje 2030-01-09, ainda aberto",
                    "aparece nos atrasados com dias_atraso=1", resumo(r) + detalhe,
                    r.status_code == 200 and item is not None and item["dias_atraso"] == 1 and item["status"] == "ABERTO")

    passou = v.salvar()
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
