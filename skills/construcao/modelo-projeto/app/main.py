"""Cria a aplicação: API em /api, tela em /."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app import banco
from app.erros import ErroNegocio, tratar_erro_negocio

ESTATICO = Path(__file__).parent / "estatico"


def criar_app(caminho_db: str | None = None) -> FastAPI:
    caminho = caminho_db or banco.caminho_padrao()

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        banco.iniciar(caminho)
        yield

    app = FastAPI(title="Sistema gerado", lifespan=ciclo_de_vida)
    app.state.caminho_db = caminho
    app.add_exception_handler(ErroNegocio, tratar_erro_negocio)

    @app.get("/api/saude")
    def saude():
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    def tela():
        return FileResponse(ESTATICO / "index.html")

    # Registre aqui os routers de app/rotas/: app.include_router(modulo.router)
    return app


app = criar_app()
