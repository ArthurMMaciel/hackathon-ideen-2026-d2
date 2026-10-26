"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, servidor

AGORA = "2030-01-07T09:00:00-03:00"  # hoje = 2030-01-07 no fuso America/Sao_Paulo
AGORA_MARCO = "2030-03-20T10:00:00-03:00"  # reinício com o tempo "passado", para o CA-10


def despesa(**mudancas) -> dict:
    base = {
        "colaborador_nome": "Verificacao Ficticia",
        "colaborador_email": "verificacao@empresa.example",
        "data_despesa": "2030-01-05",
        "categoria": "TRANSPORTE",
        "valor": 150.00,
        "descricao": "Táxi aeroporto",
        "numero_comprovante": "VER-001",
    }
    base.update(mudancas)
    return base


def resumo_http(r) -> str:
    return f"HTTP {r.status_code} {r.text[:160]}"


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", f"HTTP {r.status_code}",
                    r.status_code == 200 and "<html" in r.text.lower() and "Reembolso de despesas" in r.text)

        # CA-01
        r = api.post("/api/despesas", json=despesa(numero_comprovante="VER-CA01"))
        v.registrar("CA-01", "Lançar despesa válida", "201, situacao PENDENTE", resumo_http(r),
                    r.status_code == 201 and r.json().get("situacao") == "PENDENTE")

        # CA-02
        r = api.post("/api/despesas", json=despesa(categoria="ALIMENTACAO", valor=120.01,
                                                   numero_comprovante="VER-CA02"))
        v.registrar("CA-02", "Lançar ALIMENTACAO de R$ 120,01", "422 LIMITE_EXCEDIDO", resumo_http(r),
                    r.status_code == 422 and r.json().get("erro") == "LIMITE_EXCEDIDO")

        # CA-03
        r = api.post("/api/despesas", json=despesa(categoria="HOSPEDAGEM", valor=450.00,
                                                   numero_comprovante="VER-CA03"))
        v.registrar("CA-03", "Lançar HOSPEDAGEM de R$ 450,00", "201, despesa criada", resumo_http(r),
                    r.status_code == 201 and r.json().get("valor") == 450.0
                    and r.json().get("situacao") == "PENDENTE")

        # CA-04: 61 dias antes de 2030-01-07 = 2029-11-07
        r = api.post("/api/despesas", json=despesa(data_despesa="2029-11-07", numero_comprovante="VER-CA04"))
        v.registrar("CA-04", "Lançar despesa com data de 61 dias atrás (2029-11-07)", "422 DATA_ANTIGA",
                    resumo_http(r), r.status_code == 422 and r.json().get("erro") == "DATA_ANTIGA")

        # CA-05
        r = api.post("/api/despesas", json=despesa(data_despesa="2030-01-08", numero_comprovante="VER-CA05"))
        v.registrar("CA-05", "Lançar despesa com data de amanhã (2030-01-08)", "422 DATA_FUTURA",
                    resumo_http(r), r.status_code == 422 and r.json().get("erro") == "DATA_FUTURA")

        # CA-06
        r1 = api.post("/api/despesas", json=despesa(numero_comprovante="VER-CA06"))
        r2 = api.post("/api/despesas", json=despesa(numero_comprovante="VER-CA06", valor=20))
        v.registrar("CA-06", "Lançar o mesmo comprovante duas vezes para o mesmo colaborador",
                    "1ª 201; 2ª 409 COMPROVANTE_DUPLICADO",
                    f"1ª HTTP {r1.status_code}; 2ª {resumo_http(r2)}",
                    r1.status_code == 201 and r2.status_code == 409
                    and r2.json().get("erro") == "COMPROVANTE_DUPLICADO")

        # CA-07
        alvo = api.post("/api/despesas", json=despesa(numero_comprovante="VER-CA07")).json()["id"]
        r = api.post(f"/api/despesas/{alvo}/recusar", json={})
        situacao = api.get(f"/api/despesas/{alvo}").json()["situacao"]
        v.registrar("CA-07", "Recusar despesa sem informar motivo", "422 MOTIVO_OBRIGATORIO, segue PENDENTE",
                    f"{resumo_http(r)}; situação depois: {situacao}",
                    r.status_code == 422 and r.json().get("erro") == "MOTIVO_OBRIGATORIO"
                    and situacao == "PENDENTE")

        # CA-08
        alvo = api.post("/api/despesas", json=despesa(numero_comprovante="VER-CA08")).json()["id"]
        r = api.post(f"/api/despesas/{alvo}/pagar")
        situacao = api.get(f"/api/despesas/{alvo}").json()["situacao"]
        v.registrar("CA-08", "Marcar como paga uma despesa PENDENTE", "409 TRANSICAO_INVALIDA, segue PENDENTE",
                    f"{resumo_http(r)}; situação depois: {situacao}",
                    r.status_code == 409 and r.json().get("erro") == "TRANSICAO_INVALIDA"
                    and situacao == "PENDENTE")

        # CA-09
        alvo = api.post("/api/despesas", json=despesa(numero_comprovante="VER-CA09")).json()["id"]
        ra = api.post(f"/api/despesas/{alvo}/aprovar")
        rp = api.post(f"/api/despesas/{alvo}/pagar")
        v.registrar("CA-09", "Aprovar e depois pagar uma despesa", "200 APROVADA; 200 PAGA",
                    f"aprovar HTTP {ra.status_code} {ra.json().get('situacao')}; "
                    f"pagar HTTP {rp.status_code} {rp.json().get('situacao')}",
                    ra.status_code == 200 and ra.json().get("situacao") == "APROVADA"
                    and rp.status_code == 200 and rp.json().get("situacao") == "PAGA")

    # CA-10: mês 2030-03, sem despesas da carga inicial; o servidor reinicia com o relógio em março.
    with servidor(AGORA_MARCO, banco) as api:
        def criar(situacao, categoria, valor, comprovante):
            d = api.post("/api/despesas", json=despesa(data_despesa="2030-03-10", categoria=categoria,
                                                        valor=valor, numero_comprovante=comprovante)).json()
            if situacao in ("APROVADA", "PAGA"):
                api.post(f"/api/despesas/{d['id']}/aprovar")
            if situacao == "PAGA":
                api.post(f"/api/despesas/{d['id']}/pagar")
            if situacao == "RECUSADA":
                api.post(f"/api/despesas/{d['id']}/recusar", json={"motivo": "Fora da política"})

        criar("PAGA", "TRANSPORTE", 200.00, "VER-CA10-A")
        criar("APROVADA", "ALIMENTACAO", 80.50, "VER-CA10-B")
        criar("RECUSADA", "OUTROS", 300.00, "VER-CA10-C")
        criar("PENDENTE", "HOSPEDAGEM", 400.00, "VER-CA10-D")
        r = api.get("/api/relatorios/mensal", params={"mes": "2030-03"})
        corpo = r.json()
        esperado = {"TRANSPORTE": 200.0, "HOSPEDAGEM": 0.0, "ALIMENTACAO": 80.5, "OUTROS": 0.0}
        v.registrar("CA-10",
                    "Resumo de 2030-03 com PAGA 200,00, APROVADA 80,50, RECUSADA 300,00 e PENDENTE 400,00",
                    "RECUSADA e PENDENTE fora: total 280,50; HOSPEDAGEM e OUTROS 0",
                    f"HTTP {r.status_code} total_geral={corpo.get('total_geral')} "
                    f"por_categoria={corpo.get('totais_por_categoria')}",
                    r.status_code == 200 and corpo.get("total_geral") == 280.5
                    and corpo.get("totais_por_categoria") == esperado)

    passou = v.salvar(RAIZ.parent / "evidencias" / "criterios-aceite.md")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
