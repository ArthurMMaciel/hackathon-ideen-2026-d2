"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py

Relógio fixo em 2030-01-07 (hoje). +29 dias = 2030-02-05; +40 dias = 2030-02-16.
"""

from harness import RAIZ, Verificacao, resumo, servidor

AGORA = "2030-01-07T09:00:00-03:00"


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", resumo(r),
                    r.status_code == 200 and "<html" in r.text.lower() and "Férias da equipe" in r.text)

        def novo(nome, email, equipe, saldo=30):
            resposta = api.post("/api/colaboradores", json={"nome": nome, "email": email, "equipe": equipe, "saldo": saldo})
            assert resposta.status_code == 201, resposta.text
            return resposta.json()["id"]

        def solicitar(cid, inicio, fim):
            return api.post("/api/solicitacoes", json={"colaborador_id": cid, "inicio": inicio, "fim": fim})

        def saldo(cid):
            return api.get(f"/api/colaboradores/{cid}").json()["saldo"]

        dados_a = novo("Verif Dados A", "verif.dados.a@exemplo.com", "DADOS")
        dados_b = novo("Verif Dados B", "verif.dados.b@exemplo.com", "DADOS")
        dados_c = novo("Verif Dados C", "verif.dados.c@exemplo.com", "DADOS")
        produto_a = novo("Verif Produto A", "verif.produto.a@exemplo.com", "PRODUTO")
        suporte_a = novo("Verif Suporte A", "verif.suporte.a@exemplo.com", "SUPORTE")
        suporte_b = novo("Verif Suporte B", "verif.suporte.b@exemplo.com", "SUPORTE")
        saldo_baixo = novo("Verif Saldo Baixo", "verif.saldo@exemplo.com", "SUPORTE", saldo=8)

        # CA-01: 10 dias, início 40 dias depois de hoje.
        r = solicitar(dados_a, "2030-02-16", "2030-02-25")
        sol_a = r.json().get("id")
        v.registrar("CA-01", "Solicitar 10 dias com 40 dias de antecedência (2030-02-16 a 2030-02-25)",
                    "HTTP 201, situacao=SOLICITADA, dias=10", resumo(r, "situacao", "dias"),
                    r.status_code == 201 and r.json()["situacao"] == "SOLICITADA" and r.json()["dias"] == 10)

        # CA-02: 4 dias.
        r = solicitar(dados_b, "2030-03-01", "2030-03-04")
        v.registrar("CA-02", "Solicitar 4 dias (2030-03-01 a 2030-03-04)", "HTTP 422, erro=DURACAO_INVALIDA",
                    resumo(r, "erro"), r.status_code == 422 and r.json()["erro"] == "DURACAO_INVALIDA")

        # CA-03: início em 29 dias.
        r = solicitar(dados_b, "2030-02-05", "2030-02-14")
        v.registrar("CA-03", "Solicitar com início em 29 dias (2030-02-05)", "HTTP 422, erro=ANTECEDENCIA_INSUFICIENTE",
                    resumo(r, "erro"), r.status_code == 422 and r.json()["erro"] == "ANTECEDENCIA_INSUFICIENTE")

        # CA-04: saldo 8, pede 10.
        r = solicitar(saldo_baixo, "2030-04-01", "2030-04-10")
        v.registrar("CA-04", "Solicitar 10 dias com saldo disponível de 8", "HTTP 409, erro=SALDO_INSUFICIENTE",
                    resumo(r, "erro"), r.status_code == 409 and r.json()["erro"] == "SALDO_INSUFICIENTE")

        # CA-05: aprovar a solicitação do CA-01.
        antes = saldo(dados_a)
        r = api.post(f"/api/solicitacoes/{sol_a}/aprovar")
        depois = saldo(dados_a)
        v.registrar("CA-05", "Aprovar solicitação válida de 10 dias", "HTTP 200, situacao=APROVADA, saldo 30 → 20",
                    f"{resumo(r, 'situacao')}, saldo {antes} → {depois}",
                    r.status_code == 200 and r.json()["situacao"] == "APROVADA" and (antes, depois) == (30, 20))

        # CA-06: segunda pessoa de DADOS com dias em comum.
        sol_b = solicitar(dados_b, "2030-02-20", "2030-03-01").json()["id"]
        r = api.post(f"/api/solicitacoes/{sol_b}/aprovar")
        situacao_b = api.get(f"/api/solicitacoes/{sol_b}").json()["situacao"]
        v.registrar("CA-06", "Aprovar segunda pessoa de DADOS em 2030-02-20 a 2030-03-01 (dias em comum)",
                    "HTTP 409, erro=LIMITE_EQUIPE; segue SOLICITADA",
                    f"{resumo(r, 'erro')}; situação {situacao_b}",
                    r.status_code == 409 and r.json()["erro"] == "LIMITE_EQUIPE" and situacao_b == "SOLICITADA")

        # CA-07: pessoa de PRODUTO no mesmo período.
        sol_p = solicitar(produto_a, "2030-02-16", "2030-02-25").json()["id"]
        r = api.post(f"/api/solicitacoes/{sol_p}/aprovar")
        v.registrar("CA-07", "Aprovar pessoa de PRODUTO em 2030-02-16 a 2030-02-25", "HTTP 200, situacao=APROVADA",
                    resumo(r, "situacao"), r.status_code == 200 and r.json()["situacao"] == "APROVADA")

        # CA-08: DADOS começando no dia seguinte ao fim das férias de dados_a.
        sol_c = solicitar(dados_c, "2030-02-26", "2030-03-07").json()["id"]
        r = api.post(f"/api/solicitacoes/{sol_c}/aprovar")
        v.registrar("CA-08", "Aprovar pessoa de DADOS em 2030-02-26 (dia seguinte ao fim de outra, 2030-02-25)",
                    "HTTP 200, situacao=APROVADA",
                    resumo(r, "situacao"), r.status_code == 200 and r.json()["situacao"] == "APROVADA")

        # CA-09: cancelar aprovada antes do início.
        sol_s = solicitar(suporte_a, "2030-03-10", "2030-03-19").json()["id"]
        api.post(f"/api/solicitacoes/{sol_s}/aprovar")
        antes = saldo(suporte_a)
        r = api.post(f"/api/solicitacoes/{sol_s}/cancelar")
        depois = saldo(suporte_a)
        v.registrar("CA-09", "Cancelar solicitação aprovada (início 2030-03-10) em 2030-01-07",
                    "HTTP 200, situacao=CANCELADA, saldo 20 → 30",
                    f"{resumo(r, 'situacao')}, saldo {antes} → {depois}",
                    r.status_code == 200 and r.json()["situacao"] == "CANCELADA" and (antes, depois) == (20, 30))

        # CA-10: calendário de abril com uma APROVADA, uma SOLICITADA e uma REPROVADA.
        sol_ap = solicitar(dados_a, "2030-04-08", "2030-04-12").json()["id"]
        api.post(f"/api/solicitacoes/{sol_ap}/aprovar")
        solicitar(produto_a, "2030-04-08", "2030-04-12")
        sol_rep = solicitar(suporte_b, "2030-04-08", "2030-04-12").json()["id"]
        api.post(f"/api/solicitacoes/{sol_rep}/reprovar")
        r = api.get("/api/calendario", params={"mes": "2030-04"})
        dias = r.json()["dias"]
        nomes = sorted({p["nome"] for d in dias for lista in d["equipes"].values() for p in lista})
        dia_10 = next(d for d in dias if d["data"] == "2030-04-10")["equipes"]
        v.registrar("CA-10", "Calendário de 2030-04 com APROVADA (DADOS), SOLICITADA (PRODUTO) e REPROVADA (SUPORTE)",
                    "HTTP 200, só a aprovada (Verif Dados A) aparece",
                    f"HTTP {r.status_code}, {len(dias)} dias, nomes no mês={nomes}, "
                    f"2030-04-10 DADOS={[p['nome'] for p in dia_10['DADOS']]} PRODUTO={dia_10['PRODUTO']} "
                    f"SUPORTE={dia_10['SUPORTE']}",
                    r.status_code == 200 and nomes == ["Verif Dados A"] and len(dias) == 30)

    passou = v.salvar()
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
