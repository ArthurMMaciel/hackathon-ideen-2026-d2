"""Cria a aplicação: API em /api, tela em /."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app import banco
from app.erros import ErroNegocio, tratar_erro_negocio
from app.rotas import emprestimos, equipamentos, relatorios

ESTATICO = Path(__file__).parent / "estatico"


def criar_app(caminho_db: str | None = None) -> FastAPI:
    caminho = caminho_db or banco.caminho_padrao()

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        banco.iniciar(caminho)
        yield

    app = FastAPI(title="Empréstimo de equipamentos", lifespan=ciclo_de_vida)
    app.state.caminho_db = caminho
    app.add_exception_handler(ErroNegocio, tratar_erro_negocio)

    @app.get("/api/saude")
    def saude():
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    def tela():
        # HTMLResponse em vez de FileResponse: sem tratamento de cabeçalho Range,
        # o que evita a CVE-2025-62727 (DoS por Range) do starlette 0.41.3 fixado na stack.
        return HTMLResponse((ESTATICO / "index.html").read_text(encoding="utf-8"))

    app.include_router(equipamentos.router)
    app.include_router(emprestimos.router)
    app.include_router(relatorios.router)
    return app


app = criar_app()
