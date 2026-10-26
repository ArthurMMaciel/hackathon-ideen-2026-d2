"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, servidor

AGORA = "2030-01-07T09:00:00-03:00"
INICIO = "2030-01-10T09:00:00-03:00"  # turmas da verificação começam 3 dias depois de AGORA
DEPOIS_DO_INICIO = "2030-01-10T09:30:00-03:00"
VINTE_E_TRES_HORAS_DEPOIS = "2030-01-08T08:00:00-03:00"


def criar_turma(api, titulo, vagas, inicio=INICIO):
    r = api.post("/api/turmas", json={
        "titulo": titulo, "inicio": inicio, "duracao_minutos": 60, "modalidade": "ONLINE", "vagas": vagas,
    })
    r.raise_for_status()
    return r.json()


def inscrever(api, turma_id, apelido):
    return api.post(f"/api/turmas/{turma_id}/inscricoes",
                    json={"nome": f"Pessoa {apelido}", "email": f"{apelido}@exemplo.test"})


def resumo(r):
    return f"HTTP {r.status_code} {r.text[:160]}"


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    # Fase 1: relógio em AGORA, antes do início das turmas.
    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", f"HTTP {r.status_code}",
                    r.status_code == 200 and "<html" in r.text.lower() and "Inscrição em treinamentos" in r.text)

        # CA-01: turma com vaga
        t1 = criar_turma(api, "Verificação CA-01/CA-06/CA-09", vagas=2)
        r = inscrever(api, t1["id"], "ca01")
        insc_t1 = r.json()
        v.registrar("CA-01", "Inscrever em turma com vaga", "Inscrição CONFIRMADA", resumo(r),
                    r.status_code == 201 and r.json()["situacao"] == "CONFIRMADA")

        # CA-02: turma lotada
        t2 = criar_turma(api, "Verificação CA-02/CA-03/CA-08", vagas=1)
        a = inscrever(api, t2["id"], "ca02a").json()
        r = inscrever(api, t2["id"], "ca02b")
        b = r.json()
        v.registrar("CA-02", "Inscrever em turma lotada", "Inscrição ESPERA, primeira da fila", resumo(r),
                    r.status_code == 201 and b["situacao"] == "ESPERA" and b["posicao_espera"] == 1)

        # CA-03: cancelar confirmada com fila
        c = inscrever(api, t2["id"], "ca02c").json()
        r = api.post(f"/api/inscricoes/{a['id']}/cancelar")
        promovida = r.json().get("promovida") if r.status_code == 200 else None
        inscritos = {i["id"]: i for i in api.get(f"/api/turmas/{t2['id']}/inscricoes").json()}
        v.registrar("CA-03", "Cancelar confirmada numa turma com fila de espera",
                    "A primeira da espera passa a CONFIRMADA",
                    f"HTTP {r.status_code}; cancelada #{a['id']} {r.json()['cancelada']['situacao']}; "
                    f"promovida {promovida and (promovida['id'], promovida['situacao'])} (era ESPERA posição 1: #{b['id']}); "
                    f"próxima da fila #{c['id']} {inscritos[c['id']]['situacao']} posição {inscritos[c['id']]['posicao_espera']}",
                    r.status_code == 200 and r.json()["cancelada"]["situacao"] == "CANCELADA"
                    and promovida is not None and promovida["id"] == b["id"]
                    and inscritos[b["id"]]["situacao"] == "CONFIRMADA"
                    and inscritos[c["id"]]["situacao"] == "ESPERA" and inscritos[c["id"]]["posicao_espera"] == 1)

        # CA-04: mesmo e-mail duas vezes
        t3 = criar_turma(api, "Verificação CA-04", vagas=5)
        primeira = inscrever(api, t3["id"], "ca04")
        r = inscrever(api, t3["id"], "ca04")
        v.registrar("CA-04", "Inscrever o mesmo e-mail duas vezes na mesma turma", "Segunda recusada",
                    f"1ª HTTP {primeira.status_code}; 2ª {resumo(r)}",
                    primeira.status_code == 201 and r.status_code == 409 and r.json()["erro"] == "INSCRICAO_DUPLICADA")

        # CA-05: 23 horas antes do início
        t4 = criar_turma(api, "Verificação CA-05", vagas=5, inicio=VINTE_E_TRES_HORAS_DEPOIS)
        r = inscrever(api, t4["id"], "ca05")
        v.registrar("CA-05", "Inscrever 23 horas antes do início", "Recusa", resumo(r),
                    r.status_code == 422 and r.json()["erro"] == "INSCRICOES_ENCERRADAS")

        # CA-07: presença antes do início
        t5 = criar_turma(api, "Verificação CA-07/CA-10", vagas=4)
        ids_t5 = [inscrever(api, t5["id"], f"ca10_{n}").json()["id"] for n in range(1, 5)]
        r = api.post(f"/api/inscricoes/{ids_t5[0]}/presenca", json={"situacao": "PRESENTE"})
        v.registrar("CA-07", "Marcar presença antes do início da turma", "Recusa", resumo(r),
                    r.status_code == 422 and r.json()["erro"] == "PRESENCA_ANTES_DO_INICIO")

        # CA-09: turmas futuras depois de lotar uma turma
        inscrever(api, t1["id"], "ca09")
        r = api.get("/api/turmas")
        lotada = [t for t in r.json() if t["id"] == t1["id"]]
        v.registrar("CA-09", "Consultar turmas futuras depois de lotar uma turma",
                    "Turma lotada aparece com 0 vagas restantes",
                    f"HTTP {r.status_code} turma {t1['id']}: {lotada}",
                    r.status_code == 200 and len(lotada) == 1 and lotada[0]["vagas_restantes"] == 0)

    # Fase 2: mesmo banco, relógio depois do início das turmas.
    with servidor(DEPOIS_DO_INICIO, banco) as api:
        # CA-06: cancelar depois do início
        r = api.post(f"/api/inscricoes/{insc_t1['id']}/cancelar")
        v.registrar("CA-06", "Cancelar inscrição depois do início da turma", "Recusa", resumo(r),
                    r.status_code == 422 and r.json()["erro"] == "CANCELAMENTO_ENCERRADO")

        # CA-08: presença de inscrição em ESPERA
        r = api.post(f"/api/inscricoes/{c['id']}/presenca", json={"situacao": "PRESENTE"})
        v.registrar("CA-08", "Marcar presença de uma inscrição em ESPERA", "Recusa", resumo(r),
                    r.status_code == 422 and r.json()["erro"] == "PRESENCA_SITUACAO_INVALIDA")

        # CA-10: 3 presentes e 1 ausente
        marcacoes = [
            api.post(f"/api/inscricoes/{i}/presenca", json={"situacao": s}).status_code
            for i, s in zip(ids_t5, ["PRESENTE", "PRESENTE", "PRESENTE", "AUSENTE"])
        ]
        r = api.get(f"/api/turmas/{t5['id']}/taxa-presenca")
        v.registrar("CA-10", "Taxa de presença com 3 presentes e 1 ausente", "75%",
                    f"marcações {marcacoes}; {resumo(r)}",
                    marcacoes == [200, 200, 200, 200] and r.status_code == 200 and r.json()["taxa_presenca"] == 75.0)

    # Ordem do relatório: CA-01..CA-10 e depois TELA.
    v.linhas.sort(key=lambda linha: (linha[0] == "TELA", linha[0]))
    passou = v.salvar(RAIZ.parent / "evidencias" / "criterios-aceite.md")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
