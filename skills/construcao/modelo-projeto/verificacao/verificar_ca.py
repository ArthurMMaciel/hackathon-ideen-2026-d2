"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py"""

from harness import RAIZ, Verificacao, resumo, servidor

AGORA = "2030-01-07T09:00:00-03:00"


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", resumo(r),
                    r.status_code == 200 and "<html" in r.text.lower())

        # Um bloco por CA-xx: requisições reais do cenário, conferência de status e campos,
        # e registro com resumo(resposta, "campo_conferido", ...). Exemplo:
        # r = api.post("/api/itens", json={...})
        # v.registrar("CA-01", "<cenário>", "HTTP 201, status=ATIVO", resumo(r, "status"),
        #             r.status_code == 201 and r.json()["status"] == "ATIVO")

    # Cenários em que o tempo passa: novo `with servidor(<agora posterior>, banco) as api:` com o mesmo banco.

    passou = v.salvar()
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
