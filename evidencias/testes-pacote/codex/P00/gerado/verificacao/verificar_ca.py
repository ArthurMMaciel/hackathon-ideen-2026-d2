"""Verifica os critérios contra uvicorn real."""

from harness import RAIZ, Verificacao, resumo, servidor

AGORA = "2030-01-07T09:00:00-03:00"


def corpo(inicio="10:00", fim="11:00", **extras):
    dados = {"sala_id": 1, "responsavel_nome": "Pessoa Fictícia",
             "responsavel_email": "teste@example.test", "titulo": "Teste",
             "participantes": 2, "inicio": f"2030-01-07T{inicio}:00-03:00",
             "fim": f"2030-01-07T{fim}:00-03:00"}
    dados.update(extras)
    return dados


def registrar(v, codigo, cenario, esperado, resposta, passou, *campos):
    v.registrar(codigo, cenario, esperado, resumo(resposta, *campos), passou)


def main():
    v = Verificacao()
    banco = RAIZ / ".tmp" / "aceite.db"
    banco.parent.mkdir(exist_ok=True)
    banco.unlink(missing_ok=True)
    with servidor(AGORA, banco) as c:
        r = c.post("/api/reservas", json=corpo())
        registrar(v, "CA-01", "Reserva livre", "201 ATIVA", r,
                  r.status_code == 201 and r.json().get("status") == "ATIVA", "status")
        primeira = r.json()["id"]

        r = c.post("/api/reservas", json=corpo("10:30", "11:30"))
        registrar(v, "CA-02", "Sobreposição", "409 CONFLITO_HORARIO", r,
                  r.status_code == 409 and r.json().get("erro") == "CONFLITO_HORARIO", "erro", "mensagem")

        r = c.post("/api/reservas", json=corpo("11:00", "12:00"))
        registrar(v, "CA-03", "Intervalos encostam", "201 ATIVA", r,
                  r.status_code == 201 and r.json().get("status") == "ATIVA", "status")
        segunda = r.json()["id"]

        a = c.post("/api/reservas", json=corpo("12:00", "12:10"))
        b = c.post("/api/reservas", json=corpo("12:00", "16:01"))
        v.registrar("CA-04", "Duração 10min ou 4h01", "ambos 422 DURACAO_INVALIDA",
                    f"{resumo(a, 'erro')}; {resumo(b, 'erro')}",
                    all(x.status_code == 422 and x.json().get("erro") == "DURACAO_INVALIDA" for x in (a, b)))

        r = c.post("/api/reservas", json=corpo("08:00", "09:00"))
        registrar(v, "CA-05", "Início no passado", "422 INICIO_PASSADO", r,
                  r.status_code == 422 and r.json().get("erro") == "INICIO_PASSADO", "erro")

        r = c.post("/api/reservas", json=corpo("12:00", "13:00", participantes=9))
        registrar(v, "CA-06", "Capacidade excedida", "422 CAPACIDADE_EXCEDIDA", r,
                  r.status_code == 422 and r.json().get("erro") == "CAPACIDADE_EXCEDIDA", "erro")

        cancelada = c.post(f"/api/reservas/{primeira}/cancelar")
        liberada = c.post("/api/reservas", json=corpo())
        v.registrar("CA-07", "Cancelar e liberar", "200 CANCELADA; 201 ATIVA",
                    f"{resumo(cancelada, 'status')}; {resumo(liberada, 'status')}",
                    cancelada.status_code == 200 and cancelada.json().get("status") == "CANCELADA"
                    and liberada.status_code == 201 and liberada.json().get("status") == "ATIVA")

        params = {"inicio": "2030-01-07T10:00:00-03:00", "fim": "2030-01-07T11:00:00-03:00",
                  "local": "SAO_PAULO", "capacidade_minima": 5}
        r = c.get("/api/salas/livres", params=params)
        v.registrar("CA-09", "Filtro de salas livres", "200 lista vazia",
                    f"HTTP {r.status_code}, salas={r.json() if r.status_code == 200 else 'erro'}",
                    r.status_code == 200 and r.json() == [])

        c.post(f"/api/reservas/{liberada.json()['id']}/cancelar")
        c.post(f"/api/reservas/{segunda}/cancelar")
        ativa = c.post("/api/reservas", json=corpo("10:00", "10:30"))
        ativa_id = ativa.json()["id"]
        r = c.get("/api/relatorios/ocupacao", params={"dia": "2030-01-07"})
        item = next((x for x in r.json() if x["sala_id"] == 1), {}) if r.status_code == 200 else {}
        v.registrar("CA-10", "Ocupação sem canceladas", "200; sala 1 = 5%",
                    f"HTTP {r.status_code}, percentual={item.get('percentual')}",
                    r.status_code == 200 and item.get("percentual") == 5.0)

        tela = c.get("/")
        v.registrar("TELA", "Tela web", "200, formulário e agenda", f"HTTP {tela.status_code}",
                    tela.status_code == 200 and "form-reserva" in tela.text and "agenda" in tela.text)

    with servidor("2030-01-07T13:00:00-03:00", banco) as c:
        r = c.post(f"/api/reservas/{ativa_id}/cancelar")
        registrar(v, "CA-08", "Cancelar reserva passada", "422 CANCELAMENTO_FORA_DO_PRAZO", r,
                  r.status_code == 422 and r.json().get("erro") == "CANCELAMENTO_FORA_DO_PRAZO", "erro")
    return 0 if v.salvar() else 1


if __name__ == "__main__":
    raise SystemExit(main())
