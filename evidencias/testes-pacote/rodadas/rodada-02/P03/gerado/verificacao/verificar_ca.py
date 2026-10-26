"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, resumo, servidor

AGORA = "2030-01-07T09:00:00-03:00"
# Uma hora depois do início das turmas: o tempo "passa" reabrindo o servidor com o mesmo banco.
DEPOIS_DO_INICIO = "2030-01-10T10:00:00-03:00"
INICIO = "2030-01-10T09:00:00-03:00"
INICIO_EM_23H = "2030-01-08T08:00:00-03:00"


def criar_turma(api, titulo, vagas, inicio=INICIO):
    r = api.post("/api/turmas", json={"titulo": titulo, "inicio": inicio, "duracao_minutos": 60,
                                      "modalidade": "ONLINE", "vagas": vagas})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def inscrever(api, turma_id, email, nome="Pessoa Fictícia"):
    return api.post("/api/inscricoes", json={"turma_id": turma_id, "nome": nome, "email": email})


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        tela_ok = r.status_code == 200 and "<html" in r.text.lower() and "Inscrição em treinamentos" in r.text
        r_turmas = api.get("/api/turmas")
        v.registrar("TELA", "Abrir a tela web e carregar as turmas que ela lista",
                    "HTTP 200 com HTML; GET /api/turmas 200 com as 3 turmas iniciais",
                    f"{resumo(r)}; turmas: {resumo(r_turmas, 'x')}",
                    tela_ok and r_turmas.status_code == 200 and len(r_turmas.json()) == 3)

        # CA-01
        t1 = criar_turma(api, "CA-01 Comunicação", vagas=2)
        r = inscrever(api, t1, "ana.ca01@exemplo.test")
        v.registrar("CA-01", "Inscrever em turma com vaga (2 vagas, nenhuma ocupada)", "HTTP 201, situacao=CONFIRMADA",
                    resumo(r, "situacao"), r.status_code == 201 and r.json()["situacao"] == "CONFIRMADA")

        # CA-02
        t2 = criar_turma(api, "CA-02 Liderança", vagas=1)
        inscrever(api, t2, "primeira.ca02@exemplo.test")
        r = inscrever(api, t2, "segunda.ca02@exemplo.test")
        v.registrar("CA-02", "Inscrever em turma lotada (1 vaga já confirmada)",
                    "HTTP 201, situacao=ESPERA, posicao_espera=1", resumo(r, "situacao", "posicao_espera"),
                    r.status_code == 201 and r.json()["situacao"] == "ESPERA" and r.json()["posicao_espera"] == 1)

        # CA-03
        t3 = criar_turma(api, "CA-03 Negociação", vagas=1)
        a = inscrever(api, t3, "a.ca03@exemplo.test").json()
        b = inscrever(api, t3, "b.ca03@exemplo.test").json()
        inscrever(api, t3, "c.ca03@exemplo.test")
        r = api.post(f"/api/inscricoes/{a['id']}/cancelar")
        lista = {i["id"]: i for i in api.get(f"/api/turmas/{t3}/inscricoes").json()}
        promovida = r.json().get("promovida") or {}
        v.registrar("CA-03", "Cancelar a confirmada com 2 na espera",
                    "HTTP 200, cancelada=CANCELADA, primeira da espera (B) passa a CONFIRMADA",
                    f"HTTP {r.status_code}, cancelada={r.json()['inscricao']['situacao']}, "
                    f"promovida_id={promovida.get('id')} (B={b['id']}), situacao B na lista={lista[b['id']]['situacao']}",
                    r.status_code == 200 and promovida.get("id") == b["id"]
                    and lista[b["id"]]["situacao"] == "CONFIRMADA")

        # CA-04
        inscrever(api, t1, "repetido.ca04@exemplo.test")
        r = inscrever(api, t1, "repetido.ca04@exemplo.test")
        v.registrar("CA-04", "Inscrever o mesmo e-mail duas vezes na mesma turma",
                    "HTTP 409, erro=INSCRICAO_DUPLICADA", resumo(r, "erro", "mensagem"),
                    r.status_code == 409 and r.json()["erro"] == "INSCRICAO_DUPLICADA")

        # CA-05
        t5 = criar_turma(api, "CA-05 Excel", vagas=10, inicio=INICIO_EM_23H)
        r = inscrever(api, t5, "atrasada.ca05@exemplo.test")
        v.registrar("CA-05", "Inscrever 23 horas antes do início", "HTTP 422, erro=INSCRICOES_ENCERRADAS",
                    resumo(r, "erro", "mensagem"),
                    r.status_code == 422 and r.json()["erro"] == "INSCRICOES_ENCERRADAS")

        # CA-07 (antes do início)
        t7 = criar_turma(api, "CA-06/07 Oratória", vagas=5)
        insc7 = inscrever(api, t7, "pessoa.ca07@exemplo.test").json()
        r = api.post(f"/api/inscricoes/{insc7['id']}/presenca", json={"situacao": "PRESENTE"})
        v.registrar("CA-07", "Marcar presença antes do início da turma", "HTTP 422, erro=TURMA_NAO_INICIADA",
                    resumo(r, "erro", "mensagem"), r.status_code == 422 and r.json()["erro"] == "TURMA_NAO_INICIADA")

        # Preparação de CA-08 e CA-10 (as marcações só valem depois do início)
        t8 = criar_turma(api, "CA-08 Feedback", vagas=1)
        inscrever(api, t8, "confirmada.ca08@exemplo.test")
        espera8 = inscrever(api, t8, "espera.ca08@exemplo.test").json()
        t10 = criar_turma(api, "CA-10 Segurança", vagas=4)
        ids10 = [inscrever(api, t10, f"p{n}.ca10@exemplo.test").json()["id"] for n in range(1, 5)]

        # CA-09
        t9 = criar_turma(api, "CA-09 Planejamento", vagas=2)
        inscrever(api, t9, "um.ca09@exemplo.test")
        inscrever(api, t9, "dois.ca09@exemplo.test")
        r = api.get("/api/turmas")
        turma9 = next((t for t in r.json() if t["id"] == t9), {})
        v.registrar("CA-09", "Consultar turmas futuras depois de lotar uma turma (2 de 2 vagas)",
                    "HTTP 200, turma lotada listada com vagas_restantes=0",
                    f"HTTP {r.status_code}, turma {t9} listada={bool(turma9)}, "
                    f"vagas_restantes={turma9.get('vagas_restantes')}",
                    r.status_code == 200 and turma9.get("vagas_restantes") == 0)

    with servidor(DEPOIS_DO_INICIO, banco) as api:
        # CA-06
        r = api.post(f"/api/inscricoes/{insc7['id']}/cancelar")
        v.registrar("CA-06", "Cancelar inscrição 1 hora depois do início da turma",
                    "HTTP 422, erro=CANCELAMENTO_ENCERRADO", resumo(r, "erro", "mensagem"),
                    r.status_code == 422 and r.json()["erro"] == "CANCELAMENTO_ENCERRADO")

        # CA-08
        r = api.post(f"/api/inscricoes/{espera8['id']}/presenca", json={"situacao": "PRESENTE"})
        v.registrar("CA-08", "Marcar presença de uma inscrição em ESPERA (depois do início)",
                    "HTTP 409, erro=SITUACAO_SEM_PRESENCA", resumo(r, "erro", "mensagem"),
                    r.status_code == 409 and r.json()["erro"] == "SITUACAO_SEM_PRESENCA")

        # CA-10
        for inscricao_id, situacao in zip(ids10, ["PRESENTE", "PRESENTE", "PRESENTE", "AUSENTE"]):
            marcada = api.post(f"/api/inscricoes/{inscricao_id}/presenca", json={"situacao": situacao})
            assert marcada.status_code == 200, marcada.text
        r = api.get(f"/api/turmas/{t10}/relatorio-presenca")
        v.registrar("CA-10", "Taxa de presença com 3 presentes e 1 ausente", "HTTP 200, taxa_presenca_percentual=75.0",
                    resumo(r, "presentes", "ausentes", "taxa_presenca_percentual"),
                    r.status_code == 200 and r.json()["taxa_presenca_percentual"] == 75.0)

    passou = v.salvar()
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
