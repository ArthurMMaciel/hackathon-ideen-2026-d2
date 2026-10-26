"""Cria a aplicação: API em /api, tela em /."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app import banco
from app.erros import ErroNegocio, tratar_erro_negocio
from app.rotas import despesas as rotas_despesas

ESTATICO = Path(__file__).parent / "estatico"


def criar_app(caminho_db: str | None = None) -> FastAPI:
    caminho = caminho_db or banco.caminho_padrao()

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        banco.iniciar(caminho)
        yield

    app = FastAPI(title="Reembolso de despesas", lifespan=ciclo_de_vida)
    app.state.caminho_db = caminho
    app.add_exception_handler(ErroNegocio, tratar_erro_negocio)

    @app.get("/api/saude")
    def saude():
        return {"status": "ok"}

    # HTMLResponse em vez de FileResponse: sem processamento do cabeçalho Range
    # (CVE-2025-62727 no starlette 0.41.3, versão presa pelo fastapi da stack padrão).
    pagina = (ESTATICO / "index.html").read_text(encoding="utf-8")

    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    def tela():
        return HTMLResponse(pagina)

    app.include_router(rotas_despesas.router)
    return app


app = criar_app()
