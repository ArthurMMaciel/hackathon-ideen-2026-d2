"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, resumo, servidor

AGORA = "2030-01-07T09:00:00-03:00"  # hoje = 2030-01-07
EMAIL = "verificacao@empresa.example"


def despesa(comprovante: str, **campos) -> dict:
    base = {
        "colaborador_nome": "Verificação Fictícia",
        "colaborador_email": EMAIL,
        "data": "2030-01-05",
        "categoria": "TRANSPORTE",
        "valor_centavos": 5000,
        "descricao": "Despesa de verificação",
        "comprovante": comprovante,
    }
    base.update(campos)
    return base


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", resumo(r),
                    r.status_code == 200 and "<html" in r.text.lower() and "Reembolso de despesas" in r.text)

        # CA-01
        r = api.post("/api/despesas", json=despesa("CA01"))
        v.registrar("CA-01", "Lançar despesa válida", "HTTP 201, situacao=PENDENTE",
                    resumo(r, "id", "situacao", "valor_centavos"),
                    r.status_code == 201 and r.json()["situacao"] == "PENDENTE")

        # CA-02
        r = api.post("/api/despesas", json=despesa("CA02", categoria="ALIMENTACAO", valor_centavos=12001))
        v.registrar("CA-02", "Lançar ALIMENTACAO de R$ 120,01", "HTTP 422, erro=VALOR_ACIMA_DO_LIMITE",
                    resumo(r, "erro", "mensagem"),
                    r.status_code == 422 and r.json()["erro"] == "VALOR_ACIMA_DO_LIMITE")

        # CA-03
        r = api.post("/api/despesas", json=despesa("CA03", categoria="HOSPEDAGEM", valor_centavos=45000))
        v.registrar("CA-03", "Lançar HOSPEDAGEM de R$ 450,00", "HTTP 201, situacao=PENDENTE, valor_centavos=45000",
                    resumo(r, "situacao", "categoria", "valor_centavos"),
                    r.status_code == 201 and r.json()["valor_centavos"] == 45000 and r.json()["situacao"] == "PENDENTE")

        # CA-04: 61 dias antes de 2030-01-07
        r = api.post("/api/despesas", json=despesa("CA04", data="2029-11-07"))
        v.registrar("CA-04", "Lançar despesa com data de 61 dias atrás (2029-11-07)", "HTTP 422, erro=DATA_MUITO_ANTIGA",
                    resumo(r, "erro", "mensagem"),
                    r.status_code == 422 and r.json()["erro"] == "DATA_MUITO_ANTIGA")

        # CA-05
        r = api.post("/api/despesas", json=despesa("CA05", data="2030-01-08"))
        v.registrar("CA-05", "Lançar despesa com data de amanhã (2030-01-08)", "HTTP 422, erro=DATA_FUTURA",
                    resumo(r, "erro", "mensagem"),
                    r.status_code == 422 and r.json()["erro"] == "DATA_FUTURA")

        # CA-06
        r1 = api.post("/api/despesas", json=despesa("CA06"))
        r2 = api.post("/api/despesas", json=despesa("CA06"))
        v.registrar("CA-06", "Lançar o mesmo comprovante duas vezes para o mesmo colaborador",
                    "1ª HTTP 201; 2ª HTTP 409, erro=COMPROVANTE_DUPLICADO",
                    f"1ª {resumo(r1, 'situacao')}; 2ª {resumo(r2, 'erro', 'mensagem')}",
                    r1.status_code == 201 and r2.status_code == 409 and r2.json()["erro"] == "COMPROVANTE_DUPLICADO")

        # CA-07
        d = api.post("/api/despesas", json=despesa("CA07")).json()
        r = api.post(f"/api/despesas/{d['id']}/recusar", json={})
        lista = api.get("/api/despesas", params={"email": EMAIL}).json()
        ainda = next(x["situacao"] for x in lista if x["id"] == d["id"])
        v.registrar("CA-07", "Recusar despesa sem informar motivo", "HTTP 422, erro=MOTIVO_OBRIGATORIO; segue PENDENTE",
                    f"{resumo(r, 'erro', 'mensagem')}; situação após: {ainda}",
                    r.status_code == 422 and r.json()["erro"] == "MOTIVO_OBRIGATORIO" and ainda == "PENDENTE")

        # CA-08
        d = api.post("/api/despesas", json=despesa("CA08")).json()
        r = api.post(f"/api/despesas/{d['id']}/pagar")
        v.registrar("CA-08", "Marcar como paga uma despesa PENDENTE", "HTTP 409, erro=TRANSICAO_INVALIDA",
                    resumo(r, "erro", "mensagem"),
                    r.status_code == 409 and r.json()["erro"] == "TRANSICAO_INVALIDA")

        # CA-09
        d = api.post("/api/despesas", json=despesa("CA09")).json()
        ra = api.post(f"/api/despesas/{d['id']}/aprovar")
        rp = api.post(f"/api/despesas/{d['id']}/pagar")
        v.registrar("CA-09", "Aprovar e depois pagar uma despesa", "aprovar HTTP 200 APROVADA; pagar HTTP 200 PAGA",
                    f"aprovar {resumo(ra, 'situacao')}; pagar {resumo(rp, 'situacao')}",
                    ra.status_code == 200 and ra.json()["situacao"] == "APROVADA"
                    and rp.status_code == 200 and rp.json()["situacao"] == "PAGA")

        # CA-10: mês 2029-11 (sem dados iniciais), uma despesa em cada situação
        antes = api.get("/api/relatorios/mensal", params={"mes": "2029-11"}).json()
        for situacao, categoria, valor, dia in [("APROVADA", "HOSPEDAGEM", 30000, "2029-11-20"),
                                                ("PAGA", "TRANSPORTE", 7000, "2029-11-21"),
                                                ("RECUSADA", "ALIMENTACAO", 11000, "2029-11-22"),
                                                ("PENDENTE", "OUTROS", 50000, "2029-11-23")]:
            d = api.post("/api/despesas", json=despesa(f"CA10-{situacao}", categoria=categoria,
                                                       valor_centavos=valor, data=dia)).json()
            if situacao in ("APROVADA", "PAGA"):
                api.post(f"/api/despesas/{d['id']}/aprovar")
            if situacao == "PAGA":
                api.post(f"/api/despesas/{d['id']}/pagar")
            if situacao == "RECUSADA":
                api.post(f"/api/despesas/{d['id']}/recusar", json={"motivo": "Fora da política"})
        r = api.get("/api/relatorios/mensal", params={"mes": "2029-11"})
        corpo = r.json()
        delta = {c: corpo["totais_centavos"][c] - antes["totais_centavos"][c] for c in corpo["totais_centavos"]}
        delta_total = corpo["total_geral_centavos"] - antes["total_geral_centavos"]
        v.registrar("CA-10",
                    "Resumo de 2029-11 com uma despesa APROVADA (30000), PAGA (7000), RECUSADA (11000) e PENDENTE (50000)",
                    "HTTP 200; HOSPEDAGEM +30000, TRANSPORTE +7000, ALIMENTACAO +0, OUTROS +0, total +37000",
                    f"HTTP {r.status_code}, totais_centavos={corpo['totais_centavos']}, "
                    f"total_geral_centavos={corpo['total_geral_centavos']}, acréscimo={delta}, acréscimo total={delta_total}",
                    r.status_code == 200
                    and delta == {"TRANSPORTE": 7000, "HOSPEDAGEM": 30000, "ALIMENTACAO": 0, "OUTROS": 0}
                    and delta_total == 37000)

        # ---------- Evolução 1 ----------
        resumo_nov_antes = antes  # resumo de 2029-11 antes das despesas do CA-10

        def ler(id_):
            return next(x for x in api.get("/api/despesas", params={"email": EMAIL}).json() if x["id"] == id_)

        # CA-11
        d = api.post("/api/despesas", json=despesa("CA11")).json()
        r = api.put(f"/api/despesas/{d['id']}",
                    json={"categoria": "HOSPEDAGEM", "valor_centavos": 40000, "descricao": "Hotel corrigido"})
        c = r.json()
        v.registrar("CA-11", "Editar valor, descrição e categoria de uma despesa PENDENTE",
                    "HTTP 200; HOSPEDAGEM, 40000, 'Hotel corrigido', segue PENDENTE; data e comprovante iguais",
                    resumo(r, "categoria", "valor_centavos", "descricao", "situacao", "comprovante"),
                    r.status_code == 200 and c["categoria"] == "HOSPEDAGEM" and c["valor_centavos"] == 40000
                    and c["descricao"] == "Hotel corrigido" and c["situacao"] == "PENDENTE"
                    and c["data"] == d["data"] and c["comprovante"] == d["comprovante"])

        # CA-12
        d = api.post("/api/despesas", json=despesa("CA12")).json()
        r = api.put(f"/api/despesas/{d['id']}",
                    json={"categoria": "ALIMENTACAO", "valor_centavos": 12001, "descricao": "Jantar"})
        depois = ler(d["id"])
        v.registrar("CA-12", "Editar despesa PENDENTE para ALIMENTACAO de R$ 120,01",
                    "HTTP 422, erro=VALOR_ACIMA_DO_LIMITE; despesa inalterada",
                    f"{resumo(r, 'erro', 'mensagem')}; depois: {depois['categoria']} {depois['valor_centavos']}",
                    r.status_code == 422 and r.json()["erro"] == "VALOR_ACIMA_DO_LIMITE" and depois == d)

        # CA-13
        d = api.post("/api/despesas", json=despesa("CA13")).json()
        api.post(f"/api/despesas/{d['id']}/aprovar")
        antes13 = ler(d["id"])
        r = api.put(f"/api/despesas/{d['id']}",
                    json={"categoria": "OUTROS", "valor_centavos": 100, "descricao": "Outra"})
        v.registrar("CA-13", "Editar uma despesa APROVADA", "HTTP 409, erro=EDICAO_NAO_PERMITIDA; despesa inalterada",
                    resumo(r, "erro", "mensagem"),
                    r.status_code == 409 and r.json()["erro"] == "EDICAO_NAO_PERMITIDA" and ler(d["id"]) == antes13)

        # CA-14: 2029-11 já tem as 4 do CA-10 (APROVADA HOSPEDAGEM, PAGA TRANSPORTE, RECUSADA, PENDENTE);
        # acrescenta mais uma APROVADA em HOSPEDAGEM.
        d = api.post("/api/despesas", json=despesa("CA14", categoria="HOSPEDAGEM", valor_centavos=10000,
                                                   data="2029-11-24")).json()
        api.post(f"/api/despesas/{d['id']}/aprovar")
        r = api.get("/api/relatorios/mensal", params={"mes": "2029-11"})
        c = r.json()
        dq = {k: c["quantidades"][k] - resumo_nov_antes["quantidades"][k] for k in c["quantidades"]}
        dqt = c["quantidade_total"] - resumo_nov_antes["quantidade_total"]
        v.registrar("CA-14",
                    "Resumo de 2029-11 com 2 APROVADA HOSPEDAGEM, 1 PAGA TRANSPORTE, 1 RECUSADA ALIMENTACAO, 1 PENDENTE OUTROS",
                    "HTTP 200; quantidades HOSPEDAGEM +2, TRANSPORTE +1, ALIMENTACAO +0, OUTROS +0; quantidade_total +3",
                    f"HTTP {r.status_code}, quantidades={c['quantidades']}, quantidade_total={c['quantidade_total']}, "
                    f"acréscimo={dq}, acréscimo total={dqt}",
                    r.status_code == 200
                    and dq == {"TRANSPORTE": 1, "HOSPEDAGEM": 2, "ALIMENTACAO": 0, "OUTROS": 0}
                    and dqt == 3 and c["quantidade_total"] == sum(c["quantidades"].values()))

    passou = v.salvar()
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
