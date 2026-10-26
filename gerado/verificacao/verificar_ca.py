"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, resumo, servidor

AGORA = "2030-01-07T09:00:00-03:00"  # segunda-feira, 09:00
DEPOIS = "2030-01-07T12:00:00-03:00"  # mesmo dia, 12:00: a reserva das 10h-11h já passou
D1 = "2030-01-08"


def h(hora: str, dia: str = D1) -> str:
    return f"{dia}T{hora}:00-03:00"


def reserva(sala_id: int, inicio: str, fim: str, participantes: int = 2) -> dict:
    return {
        "sala_id": sala_id,
        "responsavel_nome": "Pessoa Ficticia",
        "responsavel_email": "pessoa@exemplo.com",
        "titulo": "Reunião de verificação",
        "participantes": participantes,
        "inicio": inicio,
        "fim": fim,
    }


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", resumo(r),
                    r.status_code == 200 and "<html" in r.text.lower() and "Reserva de salas" in r.text)

        salas = {s["nome"]: s for s in api.get("/api/salas").json()}
        paulista = salas["Paulista"]  # SAO_PAULO, capacidade 8
        ibirapuera = salas["Ibirapuera"]  # SAO_PAULO, capacidade 4
        laranjeira = salas["Laranjeira"]  # ARARAQUARA, capacidade 10

        # CA-01
        r = api.post("/api/reservas", json=reserva(paulista["id"], h("10:00"), h("11:00"), 4))
        v.registrar("CA-01", "Reservar Paulista 08/01 10h-11h, 4 pessoas", "HTTP 201, status=ATIVA",
                    resumo(r, "id", "status"), r.status_code == 201 and r.json()["status"] == "ATIVA")

        # CA-02
        r = api.post("/api/reservas", json=reserva(paulista["id"], h("10:30"), h("11:30")))
        v.registrar("CA-02", "Reservar Paulista 10h30-11h30 (sobrepõe 10h-11h)",
                    "HTTP 409, erro=CONFLITO_HORARIO, mensagem de conflito", resumo(r, "erro", "mensagem"),
                    r.status_code == 409 and r.json()["erro"] == "CONFLITO_HORARIO"
                    and "conflito" in r.json()["mensagem"].lower())

        # CA-03
        r = api.post("/api/reservas", json=reserva(paulista["id"], h("11:00"), h("12:00")))
        v.registrar("CA-03", "Reservar Paulista 11h-12h com reserva 10h-11h", "HTTP 201, status=ATIVA",
                    resumo(r, "id", "status"), r.status_code == 201 and r.json()["status"] == "ATIVA")

        # CA-04
        r1 = api.post("/api/reservas", json=reserva(laranjeira["id"], h("14:00"), h("14:10")))
        r2 = api.post("/api/reservas", json=reserva(laranjeira["id"], h("14:00"), h("18:01")))
        v.registrar("CA-04", "Reservas de 10 minutos e de 4h01",
                    "HTTP 422, erro=DURACAO_INVALIDA nas duas",
                    f"10 min: {resumo(r1, 'erro')}; 4h01: {resumo(r2, 'erro')}",
                    all(x.status_code == 422 and x.json()["erro"] == "DURACAO_INVALIDA" for x in (r1, r2)))

        # CA-05
        r = api.post("/api/reservas", json=reserva(laranjeira["id"], h("08:00", "2030-01-07"),
                                                   h("08:45", "2030-01-07")))
        v.registrar("CA-05", "Reservar 07/01 08h-08h45 com relógio em 07/01 09h",
                    "HTTP 422, erro=INICIO_NO_PASSADO", resumo(r, "erro"),
                    r.status_code == 422 and r.json()["erro"] == "INICIO_NO_PASSADO")

        # CA-06
        r = api.post("/api/reservas", json=reserva(ibirapuera["id"], h("15:00"), h("16:00"), 5))
        v.registrar("CA-06", "Reservar Ibirapuera (capacidade 4) com 5 participantes",
                    "HTTP 422, erro=CAPACIDADE_EXCEDIDA", resumo(r, "erro"),
                    r.status_code == 422 and r.json()["erro"] == "CAPACIDADE_EXCEDIDA")

        # CA-07
        alvo = api.post("/api/reservas", json=reserva(ibirapuera["id"], h("09:00"), h("10:00"))).json()
        r = api.post(f"/api/reservas/{alvo['id']}/cancelar")
        nova = api.post("/api/reservas", json=reserva(ibirapuera["id"], h("09:00"), h("10:00")))
        v.registrar("CA-07", "Cancelar reserva futura de Ibirapuera 09h-10h e reservar o mesmo horário",
                    "HTTP 200, status=CANCELADA; nova reserva HTTP 201",
                    f"cancelar: {resumo(r, 'status')}; nova: {resumo(nova, 'status')}",
                    r.status_code == 200 and r.json()["status"] == "CANCELADA" and nova.status_code == 201)

        # CA-08 (preparação): reserva hoje 10h-11h, que estará no passado às 12h.
        passada = api.post("/api/reservas", json=reserva(laranjeira["id"], h("10:00", "2030-01-07"),
                                                          h("11:00", "2030-01-07"))).json()

        # CA-09: Paulista ocupada 10h-11h; filtro SAO_PAULO e capacidade mínima 4.
        r = api.get("/api/salas/livres", params={"inicio": h("10:30"), "fim": h("11:30"),
                                                 "local": "SAO_PAULO", "capacidade_minima": 4})
        nomes = sorted(s["nome"] for s in r.json()) if r.status_code == 200 else []
        v.registrar("CA-09", "Salas livres 08/01 10h30-11h30, local SAO_PAULO, capacidade >= 4",
                    "HTTP 200, só Ibirapuera (Paulista ocupada; outros locais fora)",
                    f"{resumo(r)}: {nomes}", r.status_code == 200 and nomes == ["Ibirapuera"])

        # CA-10: Laranjeira 08/01 ativa 08h-10h e cancelada 10h-12h.
        api.post("/api/reservas", json=reserva(laranjeira["id"], h("08:00"), h("10:00")))
        cancelar = api.post("/api/reservas", json=reserva(laranjeira["id"], h("10:00"), h("12:00"))).json()
        api.post(f"/api/reservas/{cancelar['id']}/cancelar")
        r = api.get("/api/relatorios/ocupacao", params={"dia": D1})
        linha = next(x for x in r.json()["salas"] if x["sala_id"] == laranjeira["id"])
        v.registrar("CA-10", "Ocupação de 08/01 com Laranjeira 08h-10h ativa e 10h-12h cancelada",
                    "HTTP 200, Laranjeira 120 min, 20.0% (cancelada fora)",
                    f"HTTP {r.status_code}, minutos_ocupados={linha['minutos_ocupados']}, "
                    f"taxa_ocupacao={linha['taxa_ocupacao']}",
                    r.status_code == 200 and linha["minutos_ocupados"] == 120.0 and linha["taxa_ocupacao"] == 20.0)

    # O tempo passa: mesmo banco, relógio em 07/01 12h.
    with servidor(DEPOIS, banco) as api:
        r = api.post(f"/api/reservas/{passada['id']}/cancelar")
        v.registrar("CA-08", "Cancelar às 12h a reserva de 07/01 10h-11h",
                    "HTTP 409, erro=RESERVA_NAO_FUTURA", resumo(r, "erro"),
                    r.status_code == 409 and r.json()["erro"] == "RESERVA_NAO_FUTURA")

    passou = v.salvar()
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
