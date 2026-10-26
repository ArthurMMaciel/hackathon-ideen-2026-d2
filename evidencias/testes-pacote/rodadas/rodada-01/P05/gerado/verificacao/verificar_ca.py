"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py

O tempo "passa" reiniciando o servidor com outro APP_AGORA e o mesmo banco:
  T0      2030-01-07T09:00-03:00  abertura dos chamados, CA-01..CA-04, CA-10, resolução do chamado do CA-09
  T0+2h   2030-01-07T11:00-03:00  resolução do chamado MEDIA do CA-05 (prazo 24h)
  T0+4h01 2030-01-07T13:01-03:00  resolução do CRITICA do CA-06, fila do CA-07, relatório, resolução do CA-08
  +6 dias 2030-01-13T13:01-03:00  reabrir chamado do CA-08 (resolvido há exatamente 6 dias)
  +8 dias 2030-01-15T09:00-03:00  reabrir chamado do CA-09 (resolvido há exatamente 8 dias)
"""

from datetime import datetime, timedelta

from harness import RAIZ, Verificacao, servidor

T0 = "2030-01-07T09:00:00-03:00"
T0_2H = "2030-01-07T11:00:00-03:00"
T0_4H01 = "2030-01-07T13:01:00-03:00"
T_6_DIAS = "2030-01-13T13:01:00-03:00"
T_8_DIAS = "2030-01-15T09:00:00-03:00"


def novo(prioridade: str, titulo: str) -> dict:
    return {
        "titulo": titulo,
        "descricao": "Chamado de verificação",
        "solicitante_nome": "Pessoa Verificacao",
        "solicitante_email": "verificacao@example.com",
        "categoria": "SOFTWARE",
        "prioridade": prioridade,
    }


def resumo(r) -> str:
    try:
        corpo = r.json()
    except ValueError:
        corpo = r.text[:200]
    if isinstance(corpo, dict) and "erro" in corpo:
        return f"HTTP {r.status_code} {corpo['erro']}: {corpo['mensagem']}"
    if isinstance(corpo, dict) and "situacao" in corpo:
        return f"HTTP {r.status_code} situacao={corpo['situacao']}"
    return f"HTTP {r.status_code}"


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)
    ids: dict[str, int] = {}

    with servidor(T0, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", f"HTTP {r.status_code}",
                    r.status_code == 200 and "<html" in r.text.lower())

        # CA-01: abrir chamado ALTA.
        r = api.post("/api/chamados", json=novo("ALTA", "CA-01 VPN não conecta"))
        c = r.json()
        delta = datetime.fromisoformat(c["prazo"]) - datetime.fromisoformat(c["aberto_em"]) if r.status_code == 201 else None
        v.registrar("CA-01", "Abrir chamado ALTA", "ABERTO, prazo 8h após a abertura",
                    f"HTTP {r.status_code} situacao={c.get('situacao')} aberto_em={c.get('aberto_em')} prazo={c.get('prazo')}",
                    r.status_code == 201 and c["situacao"] == "ABERTO" and delta == timedelta(hours=8))

        # CA-02: assumir sem responsável.
        cid = api.post("/api/chamados", json=novo("MEDIA", "CA-02")).json()["id"]
        r = api.post(f"/api/chamados/{cid}/assumir", json={})
        situacao = api.get(f"/api/chamados/{cid}").json()["situacao"]
        v.registrar("CA-02", "Assumir chamado sem informar responsável", "Recusa",
                    f"{resumo(r)}; situação continua {situacao}",
                    r.status_code == 422 and r.json().get("erro") == "RESPONSAVEL_OBRIGATORIO" and situacao == "ABERTO")

        # CA-03: resolver chamado ABERTO direto.
        cid = api.post("/api/chamados", json=novo("MEDIA", "CA-03")).json()["id"]
        r = api.post(f"/api/chamados/{cid}/resolver", json={"solucao": "Tentativa direta"})
        situacao = api.get(f"/api/chamados/{cid}").json()["situacao"]
        v.registrar("CA-03", "Resolver chamado ABERTO direto", "Recusa",
                    f"{resumo(r)}; situação continua {situacao}",
                    r.status_code == 422 and r.json().get("erro") == "TRANSICAO_INVALIDA" and situacao == "ABERTO")

        # CA-04: resolver sem solução.
        cid = api.post("/api/chamados", json=novo("MEDIA", "CA-04")).json()["id"]
        api.post(f"/api/chamados/{cid}/assumir", json={"responsavel": "Carla Suporte"})
        r = api.post(f"/api/chamados/{cid}/resolver", json={})
        situacao = api.get(f"/api/chamados/{cid}").json()["situacao"]
        v.registrar("CA-04", "Resolver chamado sem informar solução", "Recusa",
                    f"{resumo(r)}; situação continua {situacao}",
                    r.status_code == 422 and r.json().get("erro") == "SOLUCAO_OBRIGATORIA" and situacao == "EM_ATENDIMENTO")

        # CA-10: fechar chamado ABERTO (registrado no fim, para manter a ordem dos códigos).
        cid = api.post("/api/chamados", json=novo("BAIXA", "CA-10")).json()["id"]
        r = api.post(f"/api/chamados/{cid}/fechar")
        situacao = api.get(f"/api/chamados/{cid}").json()["situacao"]
        ca10 = (r.status_code == 422 and r.json().get("erro") == "TRANSICAO_INVALIDA" and situacao == "ABERTO",
                f"{resumo(r)}; situação continua {situacao}")

        # Preparação dos cenários que dependem do tempo.
        for chave, prioridade in (("ca05", "MEDIA"), ("ca06", "CRITICA"), ("ca07", "CRITICA"),
                                  ("ca08", "ALTA"), ("ca09", "ALTA")):
            ids[chave] = api.post("/api/chamados", json=novo(prioridade, chave.upper())).json()["id"]
        for chave in ("ca05", "ca06", "ca08", "ca09"):
            api.post(f"/api/chamados/{ids[chave]}/assumir", json={"responsavel": "Carla Suporte"})
        r = api.post(f"/api/chamados/{ids['ca09']}/resolver", json={"solucao": "Resolvido em T0"})
        assert r.status_code == 200, r.text

    with servidor(T0_2H, banco) as api:
        r5 = api.post(f"/api/chamados/{ids['ca05']}/resolver", json={"solucao": "Resolvido 2h após abrir"})

    with servidor(T0_4H01, banco) as api:
        r6 = api.post(f"/api/chamados/{ids['ca06']}/resolver", json={"solucao": "Resolvido 4h01 após abrir"})
        r8 = api.post(f"/api/chamados/{ids['ca08']}/resolver", json={"solucao": "Resolvido em T0+4h01"})
        assert r8.status_code == 200, r8.text
        rel = api.get("/api/relatorios/prazo", params={"data_inicial": "2030-01-07", "data_final": "2030-01-07"}).json()
        por_prioridade = {p["prioridade"]: p for p in rel["prioridades"]}

        # CA-05: dentro do prazo no relatório (MEDIA resolvido 2h após a abertura, prazo 24h).
        media = por_prioridade["MEDIA"]
        c5 = api.get(f"/api/chamados/{ids['ca05']}").json()
        v.registrar("CA-05", "Resolver chamado dentro do prazo", "Conta como dentro do prazo no relatório",
                    f"resolver: HTTP {r5.status_code} dentro_do_prazo={c5['dentro_do_prazo']}; relatório MEDIA "
                    f"resolvidos={media['resolvidos']} dentro={media['dentro_do_prazo']} "
                    f"percentual={media['percentual_dentro_do_prazo']}",
                    r5.status_code == 200 and c5["dentro_do_prazo"] is True
                    and media["resolvidos"] == 1 and media["dentro_do_prazo"] == 1
                    and media["percentual_dentro_do_prazo"] == 100.0)

        # CA-06: CRITICA resolvido 4h01 depois da abertura.
        critica = por_prioridade["CRITICA"]
        c6 = r6.json()
        v.registrar("CA-06", "Resolver chamado CRITICA 4h01 depois da abertura", "Conta como fora do prazo",
                    f"resolver: HTTP {r6.status_code} aberto_em={c6.get('aberto_em')} resolvido_em={c6.get('resolvido_em')} "
                    f"dentro_do_prazo={c6.get('dentro_do_prazo')}; relatório CRITICA resolvidos={critica['resolvidos']} "
                    f"dentro={critica['dentro_do_prazo']} percentual={critica['percentual_dentro_do_prazo']}",
                    r6.status_code == 200 and c6["dentro_do_prazo"] is False
                    and critica["resolvidos"] == 1 and critica["dentro_do_prazo"] == 0)

        # CA-07: fila com chamado de prazo vencido (CRITICA aberto há 4h01).
        r = api.get("/api/chamados/fila")
        fila = {item["id"]: item for item in r.json()}
        item = fila.get(ids["ca07"], {})
        v.registrar("CA-07", "Consultar a fila com um chamado de prazo vencido", "Chamado aparece como ATRASADO",
                    f"HTTP {r.status_code} chamado {ids['ca07']} prazo={item.get('prazo')} indicacao={item.get('indicacao')}",
                    r.status_code == 200 and item.get("indicacao") == "ATRASADO")

    with servidor(T_6_DIAS, banco) as api:
        # CA-08: reabrir chamado resolvido há 6 dias.
        r = api.post(f"/api/chamados/{ids['ca08']}/reabrir")
        v.registrar("CA-08", "Reabrir chamado resolvido há 6 dias", "Chamado EM_ATENDIMENTO",
                    f"{resumo(r)} (resolvido em {T0_4H01}, agora {T_6_DIAS})",
                    r.status_code == 200 and r.json().get("situacao") == "EM_ATENDIMENTO")

    with servidor(T_8_DIAS, banco) as api:
        # CA-09: reabrir chamado resolvido há 8 dias.
        r = api.post(f"/api/chamados/{ids['ca09']}/reabrir")
        situacao = api.get(f"/api/chamados/{ids['ca09']}").json()["situacao"]
        v.registrar("CA-09", "Reabrir chamado resolvido há 8 dias", "Recusa",
                    f"{resumo(r)}; situação continua {situacao} (resolvido em {T0}, agora {T_8_DIAS})",
                    r.status_code == 422 and r.json().get("erro") == "REABERTURA_EXPIRADA" and situacao == "RESOLVIDO")

    v.registrar("CA-10", "Fechar chamado ABERTO", "Recusa", ca10[1], ca10[0])

    passou = v.salvar(RAIZ.parent / "evidencias" / "criterios-aceite.md")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
