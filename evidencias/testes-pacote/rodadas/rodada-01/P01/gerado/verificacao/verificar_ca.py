"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, servidor

AGORA = "2030-01-07T09:00:00-03:00"  # segunda-feira; "hoje" = 2030-01-07
DIA_SEGUINTE = "2030-01-08T09:00:00-03:00"

# Ids da carga inicial (RF-12): 1-3 NOTEBOOK, 4-5 PROJETOR, 6-8 HEADSET, 8 em MANUTENCAO.
NOTEBOOK_1, NOTEBOOK_2, NOTEBOOK_3 = 1, 2, 3
PROJETOR_1, PROJETOR_2 = 4, 5
HEADSET_1, HEADSET_2, HEADSET_MANUTENCAO = 6, 7, 8


def emprestar(api, equipamento_id, data_prevista, email, nome="Pessoa Exemplo"):
    return api.post(
        "/api/emprestimos",
        json={"equipamento_id": equipamento_id, "nome": nome, "email": email, "data_prevista": data_prevista},
    )


def resumo(r) -> str:
    """Status HTTP mais os campos que o critério confere (sucesso) ou o corpo de erro inteiro."""
    try:
        corpo = r.json()
    except ValueError:
        return f"HTTP {r.status_code} {r.text[:200]}"
    if isinstance(corpo, dict) and "status" in corpo:
        campos = ("id", "patrimonio", "data_retirada", "data_prevista", "data_devolucao", "status", "situacao_equipamento")
        return f"HTTP {r.status_code} " + ", ".join(f"{c}={corpo.get(c)}" for c in campos)
    return f"HTTP {r.status_code} {r.text[:200]}"


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", f"HTTP {r.status_code}",
                    r.status_code == 200 and "<html" in r.text.lower())

        # CA-01: notebook disponível, prevista em 3 dias (limite 14)
        r = emprestar(api, NOTEBOOK_1, "2030-01-10", "ana@exemplo.test", "Ana Exemplo")
        equip = api.get(f"/api/equipamentos/{NOTEBOOK_1}").json()
        ok = r.status_code == 201 and r.json()["status"] == "ABERTO" and equip["situacao"] == "EMPRESTADO"
        v.registrar("CA-01", "Emprestar equipamento disponível com prazo dentro do limite",
                    "Empréstimo ABERTO e equipamento EMPRESTADO",
                    f"{resumo(r)} | equipamento {equip['situacao']}", ok)

        # CA-02: o mesmo notebook, agora emprestado, para outra pessoa
        r = emprestar(api, NOTEBOOK_1, "2030-01-10", "bruno@exemplo.test", "Bruno Exemplo")
        v.registrar("CA-02", "Emprestar equipamento já emprestado", "Recusa", resumo(r),
                    r.status_code == 409 and r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL")

        # CA-03: headset em manutenção da carga inicial
        r = emprestar(api, HEADSET_MANUTENCAO, "2030-01-08", "bruno@exemplo.test", "Bruno Exemplo")
        v.registrar("CA-03", "Emprestar equipamento em manutenção", "Recusa", resumo(r),
                    r.status_code == 409 and r.json()["erro"] == "EQUIPAMENTO_INDISPONIVEL")

        # CA-04: notebook com prevista 15 dias depois da retirada (2030-01-07 + 15)
        r = emprestar(api, NOTEBOOK_2, "2030-01-22", "bruno@exemplo.test", "Bruno Exemplo")
        equip = api.get(f"/api/equipamentos/{NOTEBOOK_2}").json()
        v.registrar("CA-04", "Emprestar notebook com devolução prevista para 15 dias depois", "Recusa por prazo",
                    f"{resumo(r)} | equipamento {equip['situacao']}",
                    r.status_code == 422 and r.json()["erro"] == "PRAZO_EXCEDIDO" and equip["situacao"] == "DISPONIVEL")

        # CA-05: projetor com prevista 3 dias depois
        r = emprestar(api, PROJETOR_1, "2030-01-10", "bruno@exemplo.test", "Bruno Exemplo")
        v.registrar("CA-05", "Emprestar projetor com devolução prevista para 3 dias depois", "Empréstimo criado",
                    resumo(r), r.status_code == 201 and r.json()["status"] == "ABERTO")

        # CA-06: Carla pega 2 e pede o terceiro
        r1 = emprestar(api, NOTEBOOK_2, "2030-01-10", "carla@exemplo.test", "Carla Exemplo")
        r2 = emprestar(api, HEADSET_1, "2030-01-10", "carla@exemplo.test", "Carla Exemplo")
        r3 = emprestar(api, NOTEBOOK_3, "2030-01-10", "carla@exemplo.test", "Carla Exemplo")
        ok = (r1.status_code == 201 and r2.status_code == 201
              and r3.status_code == 422 and r3.json()["erro"] == "LIMITE_EMPRESTIMOS")
        v.registrar("CA-06", "Pessoa com 2 empréstimos em aberto pede um terceiro", "Recusa",
                    f"1º HTTP {r1.status_code}, 2º HTTP {r2.status_code}, 3º {resumo(r3)}", ok)

        # CA-07: devolver o notebook de Ana sem defeito
        id_ana = api.get("/api/emprestimos", params={"status": "ABERTO"}).json()[0]["id"]
        r = api.post(f"/api/emprestimos/{id_ana}/devolver", json={"defeito": False})
        equip = api.get(f"/api/equipamentos/{NOTEBOOK_1}").json()
        ok = r.status_code == 200 and r.json()["status"] == "DEVOLVIDO" and equip["situacao"] == "DISPONIVEL"
        v.registrar("CA-07", "Devolver sem defeito", "Empréstimo DEVOLVIDO e equipamento DISPONIVEL",
                    f"{resumo(r)} | equipamento {equip['situacao']}", ok)

        # CA-08: devolver o headset de Carla com defeito
        id_headset = next(e["id"] for e in api.get("/api/emprestimos", params={"status": "ABERTO"}).json()
                          if e["equipamento_id"] == HEADSET_1)
        r = api.post(f"/api/emprestimos/{id_headset}/devolver", json={"defeito": True})
        equip = api.get(f"/api/equipamentos/{HEADSET_1}").json()
        v.registrar("CA-08", "Devolver com defeito", "Equipamento MANUTENCAO",
                    f"{resumo(r)} | equipamento {equip['situacao']}",
                    r.status_code == 200 and equip["situacao"] == "MANUTENCAO")

        # CA-10: devolver de novo o empréstimo de Ana
        r = api.post(f"/api/emprestimos/{id_ana}/devolver", json={"defeito": False})
        v.registrar("CA-10", "Devolver empréstimo já devolvido", "Recusa", resumo(r),
                    r.status_code == 409 and r.json()["erro"] == "EMPRESTIMO_JA_DEVOLVIDO")

        # CA-09 (preparação): Davi pega um projetor com prevista para hoje (2030-01-07)
        r = emprestar(api, PROJETOR_2, "2030-01-07", "davi@exemplo.test", "Davi Exemplo")
        id_davi = r.json()["id"] if r.status_code == 201 else None
        atrasados_hoje = api.get("/api/emprestimos/atrasados").json()

    # CA-09: o tempo passa um dia; a prevista (2030-01-07) passa a ser "ontem"
    with servidor(DIA_SEGUINTE, banco) as api:
        r = api.get("/api/emprestimos/atrasados")
        atrasado = next((a for a in r.json() if a["id"] == id_davi), None) if r.status_code == 200 else None
        ok = (id_davi is not None and atrasado is not None and atrasado["dias_atraso"] == 1
              and atrasado["status"] == "ABERTO" and all(a["id"] != id_davi for a in atrasados_hoje))
        obtido = (f"HTTP {r.status_code}; empréstimo {id_davi} "
                  f"{'com dias_atraso ' + str(atrasado['dias_atraso']) if atrasado else 'ausente'}"
                  f" (no dia anterior: {'ausente' if all(a['id'] != id_davi for a in atrasados_hoje) else 'presente'})")
        v.registrar("CA-09", "Empréstimo com devolução prevista para ontem e ainda aberto",
                    "Aparece nos atrasados com 1 dia de atraso", obtido, ok)

    v.linhas.sort(key=lambda linha: (linha[0] != "TELA", linha[0]))
    passou = v.salvar(RAIZ.parent / "evidencias" / "criterios-aceite.md")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
