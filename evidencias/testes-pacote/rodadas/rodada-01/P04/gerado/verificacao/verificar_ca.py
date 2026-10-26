"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, servidor

# Relógio fixo: hoje = 2030-01-07. Início mínimo (30 dias) = 2030-02-06.
AGORA = "2030-01-07T09:00:00-03:00"


def resumo(r) -> str:
    try:
        corpo = r.json()
    except ValueError:
        corpo = r.text[:120]
    return f"HTTP {r.status_code} {corpo}"


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", f"HTTP {r.status_code}",
                    r.status_code == 200 and "<html" in r.text.lower() and "Férias da equipe" in r.text)

        def solicitar(colab, inicio, fim):
            return api.post("/api/solicitacoes", json={"colaborador_id": colab, "inicio": inicio, "fim": fim})

        def saldo(colab):
            return api.get(f"/api/colaboradores/{colab}").json()

        # Carga: 1-3 DADOS, 4-6 PRODUTO, 7-9 SUPORTE. Cada CA usa colaboradores próprios.

        # CA-01: 10 dias, início em 2030-02-16 (40 dias depois de hoje). Colaborador 1 (DADOS).
        r = solicitar(1, "2030-02-16", "2030-02-25")
        c = r.json()
        v.registrar("CA-01", "Solicitar 10 dias com 40 dias de antecedência", "201, SOLICITADA, 10 dias",
                    f"HTTP {r.status_code} situacao={c.get('situacao')} dias={c.get('dias')}",
                    r.status_code == 201 and c.get("situacao") == "SOLICITADA" and c.get("dias") == 10)

        # CA-02: 4 dias.
        r = solicitar(2, "2030-03-01", "2030-03-04")
        v.registrar("CA-02", "Solicitar 4 dias", "Recusa (422 DURACAO_INVALIDA)", resumo(r),
                    r.status_code == 422 and r.json().get("erro") == "DURACAO_INVALIDA")

        # CA-03: início em 29 dias = 2030-02-05.
        r = solicitar(2, "2030-02-05", "2030-02-14")
        v.registrar("CA-03", "Solicitar com início em 29 dias", "Recusa por antecedência (422 ANTECEDENCIA_INSUFICIENTE)",
                    resumo(r), r.status_code == 422 and r.json().get("erro") == "ANTECEDENCIA_INSUFICIENTE")

        # CA-04: colaborador 3 pede 20 dias (fica com 10 disponíveis) e depois 15.
        r1 = solicitar(3, "2030-06-01", "2030-06-20")
        r = solicitar(3, "2030-07-01", "2030-07-15")
        v.registrar("CA-04", "Solicitar mais dias que o saldo disponível (10 disponíveis, pede 15)",
                    "Recusa (422 SALDO_INSUFICIENTE)", f"1º pedido HTTP {r1.status_code}; 2º {resumo(r)}",
                    r1.status_code == 201 and r.status_code == 422 and r.json().get("erro") == "SALDO_INSUFICIENTE")

        # CA-05: aprovar a solicitação do CA-01 (colaborador 1, 10 dias).
        antes = saldo(1)["saldo"]
        sid = c["id"]
        r = api.post(f"/api/solicitacoes/{sid}/aprovar")
        depois = saldo(1)["saldo"]
        v.registrar("CA-05", "Aprovar solicitação válida", "200 APROVADA e saldo reduzido (30 -> 20)",
                    f"HTTP {r.status_code} situacao={r.json().get('situacao')} saldo {antes} -> {depois}",
                    r.status_code == 200 and r.json().get("situacao") == "APROVADA" and antes == 30 and depois == 20)

        # CA-06: colaborador 2 (DADOS) com dias em comum com o colaborador 1 (2030-02-16..25).
        s2 = solicitar(2, "2030-02-20", "2030-03-01").json()
        r = api.post(f"/api/solicitacoes/{s2['id']}/aprovar")
        situacao = next(s["situacao"] for s in api.get("/api/solicitacoes").json() if s["id"] == s2["id"])
        v.registrar("CA-06", "Aprovar segunda pessoa da mesma equipe com dias em comum",
                    "Recusa (409 LIMITE_EQUIPE), continua SOLICITADA", f"{resumo(r)}; situação {situacao}",
                    r.status_code == 409 and r.json().get("erro") == "LIMITE_EQUIPE" and situacao == "SOLICITADA")

        # CA-07: colaborador 4 (PRODUTO) no mesmo período do colaborador 1.
        s4 = solicitar(4, "2030-02-16", "2030-02-25").json()
        r = api.post(f"/api/solicitacoes/{s4['id']}/aprovar")
        v.registrar("CA-07", "Aprovar pessoa de outra equipe no mesmo período", "200 APROVADA", resumo(r),
                    r.status_code == 200 and r.json().get("situacao") == "APROVADA")

        # CA-08: colaborador 5 (PRODUTO) começa em 2030-02-26, dia seguinte ao fim do colaborador 4.
        s5 = solicitar(5, "2030-02-26", "2030-03-07").json()
        r = api.post(f"/api/solicitacoes/{s5['id']}/aprovar")
        v.registrar("CA-08", "Aprovar mesma equipe com férias começando no dia seguinte ao fim de outra",
                    "200 APROVADA", resumo(r), r.status_code == 200 and r.json().get("situacao") == "APROVADA")

        # CA-09: colaborador 7 (SUPORTE), aprovada, cancelada antes do início.
        s7 = solicitar(7, "2030-04-01", "2030-04-10").json()
        api.post(f"/api/solicitacoes/{s7['id']}/aprovar")
        aprovado = saldo(7)["saldo"]
        r = api.post(f"/api/solicitacoes/{s7['id']}/cancelar")
        devolvido = saldo(7)["saldo"]
        v.registrar("CA-09", "Cancelar solicitação aprovada antes do início",
                    "200 CANCELADA e saldo devolvido (20 -> 30)",
                    f"HTTP {r.status_code} situacao={r.json().get('situacao')} saldo {aprovado} -> {devolvido}",
                    r.status_code == 200 and r.json().get("situacao") == "CANCELADA"
                    and aprovado == 20 and devolvido == 30)

        # CA-10: maio/2030 com uma APROVADA (8), uma SOLICITADA (9) e uma REPROVADA (6).
        a = solicitar(8, "2030-05-10", "2030-05-19").json()
        solicitar(9, "2030-05-10", "2030-05-19")
        rep = solicitar(6, "2030-05-10", "2030-05-19").json()
        api.post(f"/api/solicitacoes/{a['id']}/aprovar")
        api.post(f"/api/solicitacoes/{rep['id']}/reprovar")
        r = api.get("/api/calendario", params={"mes": "2030-05"})
        dias = r.json()["dias"]
        nomes = sorted({p["nome"] for d in dias for eq in d["equipes"].values() for p in eq})
        dia10 = {eq: [p["nome"] for p in ps] for eq, ps in dias[9]["equipes"].items()}
        v.registrar("CA-10", "Calendário do mês com solicitações SOLICITADA e REPROVADA",
                    "Só as aprovadas aparecem (Heitor Vilela)",
                    f"HTTP {r.status_code} nomes no mês={nomes}; 2030-05-10={dia10}",
                    r.status_code == 200 and nomes == ["Heitor Vilela"] and len(dias) == 31
                    and dia10 == {"DADOS": [], "PRODUTO": [], "SUPORTE": ["Heitor Vilela"]})

    passou = v.salvar(RAIZ.parent / "evidencias" / "criterios-aceite.md")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
