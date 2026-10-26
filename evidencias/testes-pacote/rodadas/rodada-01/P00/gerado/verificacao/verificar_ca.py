"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, servidor

AGORA = "2030-01-07T09:00:00-03:00"  # segunda-feira, 09:00
DEPOIS = "2030-01-09T09:00:00-03:00"  # dois dias depois: reservas de 08/01 já passaram
D1 = "2030-01-08"
SALA_PAULISTA, SALA_IBIRAPUERA, SALA_LARANJEIRA, SALA_MORADA = 1, 2, 3, 4


def h(dia: str, hora: str) -> str:
    return f"{dia}T{hora}:00-03:00"


def reserva(sala_id, inicio, fim, participantes=4, titulo="Reunião de verificação"):
    return {
        "sala_id": sala_id,
        "responsavel_nome": "Pessoa Ficticia",
        "responsavel_email": "pessoa@exemplo.com",
        "titulo": titulo,
        "participantes": participantes,
        "inicio": inicio,
        "fim": fim,
    }


def resumo(r) -> str:
    try:
        corpo = r.json()
    except ValueError:
        corpo = r.text[:80]
    if isinstance(corpo, dict):
        chaves = ("id", "status", "erro", "mensagem")
        corpo = {k: corpo[k] for k in chaves if k in corpo} or corpo
    return f"HTTP {r.status_code} {corpo}"


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", f"HTTP {r.status_code}",
                    r.status_code == 200 and "<html" in r.text.lower() and "Reserva de salas" in r.text)

        # CA-01
        r = api.post("/api/reservas", json=reserva(SALA_PAULISTA, h(D1, "10:00"), h(D1, "11:00")))
        ca01 = r.json() if r.status_code == 201 else {}
        v.registrar("CA-01", "Reservar sala livre dentro das regras (Paulista 08/01 10h–11h)",
                    "201, status ATIVA", resumo(r), r.status_code == 201 and ca01.get("status") == "ATIVA")

        # CA-02
        r = api.post("/api/reservas", json=reserva(SALA_PAULISTA, h(D1, "10:30"), h(D1, "11:30")))
        v.registrar("CA-02", "Reservar Paulista 10h30–11h30 sobre reserva 10h–11h",
                    "409 CONFLITO_HORARIO com mensagem de conflito", resumo(r),
                    r.status_code == 409 and r.json().get("erro") == "CONFLITO_HORARIO"
                    and "conflito" in r.json().get("mensagem", "").lower())

        # CA-03
        r = api.post("/api/reservas", json=reserva(SALA_PAULISTA, h(D1, "11:00"), h(D1, "12:00")))
        v.registrar("CA-03", "Reservar Paulista 11h–12h com reserva 10h–11h existente",
                    "201, status ATIVA", resumo(r), r.status_code == 201 and r.json().get("status") == "ATIVA")

        # CA-04
        curta = api.post("/api/reservas", json=reserva(SALA_IBIRAPUERA, h(D1, "10:00"), h(D1, "10:10")))
        longa = api.post("/api/reservas", json=reserva(SALA_IBIRAPUERA, h(D1, "13:00"), h(D1, "17:01")))
        v.registrar("CA-04", "Reserva com 10 minutos e com 4h01",
                    "422 DURACAO_INVALIDA nas duas", f"10 min: {resumo(curta)}; 4h01: {resumo(longa)}",
                    all(x.status_code == 422 and x.json().get("erro") == "DURACAO_INVALIDA" for x in (curta, longa)))

        # CA-05
        r = api.post("/api/reservas", json=reserva(SALA_IBIRAPUERA, h("2030-01-07", "08:00"), h("2030-01-07", "09:30")))
        v.registrar("CA-05", "Reserva com início 07/01 08h, relógio em 07/01 09h",
                    "422 INICIO_NO_PASSADO", resumo(r),
                    r.status_code == 422 and r.json().get("erro") == "INICIO_NO_PASSADO")

        # CA-06
        r = api.post("/api/reservas", json=reserva(SALA_IBIRAPUERA, h(D1, "14:00"), h(D1, "15:00"), participantes=5))
        v.registrar("CA-06", "5 participantes na Ibirapuera (capacidade 4)",
                    "422 CAPACIDADE_EXCEDIDA", resumo(r),
                    r.status_code == 422 and r.json().get("erro") == "CAPACIDADE_EXCEDIDA")

        # CA-07
        criada = api.post("/api/reservas", json=reserva(SALA_LARANJEIRA, h(D1, "14:00"), h(D1, "15:00"))).json()
        cancelada = api.post(f"/api/reservas/{criada['id']}/cancelar")
        nova = api.post("/api/reservas", json=reserva(SALA_LARANJEIRA, h(D1, "14:00"), h(D1, "15:00")))
        historico = api.get(f"/api/reservas/{criada['id']}").json()
        v.registrar("CA-07", "Cancelar reserva futura (Laranjeira 08/01 14h–15h) e reservar o mesmo horário",
                    "200 CANCELADA; nova reserva 201; histórico mantém CANCELADA",
                    f"cancelar: {resumo(cancelada)}; nova: {resumo(nova)}; histórico: {historico.get('status')}",
                    cancelada.status_code == 200 and cancelada.json().get("status") == "CANCELADA"
                    and nova.status_code == 201 and historico.get("status") == "CANCELADA")

        # CA-09 (Paulista ocupada 10h–12h)
        params = {"inicio": h(D1, "10:00"), "fim": h(D1, "11:00"), "local": "SAO_PAULO"}
        r4 = api.get("/api/salas/livres", params={**params, "capacidade_minima": 4})
        r5 = api.get("/api/salas/livres", params={**params, "capacidade_minima": 5})
        nomes4 = [s["nome"] for s in r4.json()] if r4.status_code == 200 else None
        nomes5 = [s["nome"] for s in r5.json()] if r5.status_code == 200 else None
        v.registrar("CA-09", "Salas livres 08/01 10h–11h, local SAO_PAULO, capacidade mínima 4 e 5 (Paulista ocupada)",
                    "cap>=4: [Sala Ibirapuera]; cap>=5: []",
                    f"HTTP {r4.status_code} cap>=4: {nomes4}; HTTP {r5.status_code} cap>=5: {nomes5}",
                    nomes4 == ["Sala Ibirapuera"] and nomes5 == [])

        # CA-10
        api.post("/api/reservas", json=reserva(SALA_MORADA, h(D1, "09:00"), h(D1, "10:00")))
        cancelar = api.post("/api/reservas", json=reserva(SALA_MORADA, h(D1, "13:00"), h(D1, "15:00"))).json()
        api.post(f"/api/reservas/{cancelar['id']}/cancelar")
        r = api.get("/api/relatorios/ocupacao", params={"data": D1})
        morada = next((s for s in r.json().get("salas", []) if s["sala_id"] == SALA_MORADA), {}) if r.status_code == 200 else {}
        v.registrar("CA-10", "Ocupação de 08/01 da Morada do Sol: 1h ativa (9h–10h) e 2h canceladas (13h–15h)",
                    "60 min, taxa 10.0% (canceladas fora)",
                    f"HTTP {r.status_code} minutos={morada.get('minutos_ocupados')} taxa={morada.get('taxa_ocupacao')}",
                    morada.get("minutos_ocupados") == 60 and morada.get("taxa_ocupacao") == 10.0)

    # CA-08: o tempo passa (servidor reiniciado com APP_AGORA posterior, mesmo banco).
    with servidor(DEPOIS, banco) as api:
        r = api.post(f"/api/reservas/{ca01.get('id', 0)}/cancelar")
        estado = api.get(f"/api/reservas/{ca01.get('id', 0)}").json().get("status")
        v.registrar("CA-08", "Cancelar a reserva de 08/01 10h–11h com relógio em 09/01 09h",
                    "422 CANCELAMENTO_NAO_PERMITIDO; reserva segue ATIVA",
                    f"{resumo(r)}; status depois: {estado}",
                    r.status_code == 422 and r.json().get("erro") == "CANCELAMENTO_NAO_PERMITIDO" and estado == "ATIVA")

    v.linhas.sort(key=lambda linha: (linha[0] != "TELA", linha[0]))
    passou = v.salvar(RAIZ.parent / "evidencias" / "criterios-aceite.md")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
