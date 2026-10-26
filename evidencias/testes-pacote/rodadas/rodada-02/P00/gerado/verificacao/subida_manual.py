"""Sobe o sistema como um usuário faria (relógio real, banco novo), confere API e tela e derruba o servidor.

Rode a partir de gerado/: PY verificacao/subida_manual.py
"""

from harness import RAIZ, Verificacao, resumo, servidor


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "subida-manual.db"
    banco.unlink(missing_ok=True)

    with servidor(None, banco) as api:
        r = api.get("/api/saude")
        v.registrar("API", "GET /api/saude", "HTTP 200", resumo(r, "status"), r.status_code == 200)
        r = api.get("/")
        v.registrar("TELA", "GET /", "HTTP 200 com HTML", resumo(r),
                    r.status_code == 200 and "<html" in r.text.lower())
        r = api.get("/docs")
        v.registrar("DOCS", "GET /docs", "HTTP 200", resumo(r), r.status_code == 200)

    passou = v.salvar("subida-manual.md")
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
