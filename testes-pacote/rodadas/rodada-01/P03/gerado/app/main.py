"""Cria a aplicação: API em /api, tela em /."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app import banco
from app.erros import ErroNegocio, tratar_erro_negocio
from app.relogio import obter_agora
from app.rotas import inscricoes, turmas

ESTATICO = Path(__file__).parent / "estatico"


def criar_app(caminho_db: str | None = None) -> FastAPI:
    caminho = caminho_db or banco.caminho_padrao()

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        # Mesmo relógio da API (inclusive o substituto dos testes), para a carga inicial nascer no futuro.
        relogio = app.dependency_overrides.get(obter_agora, obter_agora)
        banco.iniciar(caminho, relogio())
        yield

    app = FastAPI(title="Inscrição em treinamentos", lifespan=ciclo_de_vida)
    app.state.caminho_db = caminho
    app.add_exception_handler(ErroNegocio, tratar_erro_negocio)

    @app.get("/api/saude")
    def saude():
        return {"status": "ok"}

    # HTMLResponse em vez de FileResponse: a tela é pequena e assim não há tratamento do cabeçalho Range
    # (CVE-2025-62727, DoS no FileResponse do starlette 0.41.3 fixado pela stack).
    pagina = (ESTATICO / "index.html").read_text(encoding="utf-8")

    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    def tela():
        return HTMLResponse(pagina)

    app.include_router(turmas.router)
    app.include_router(inscricoes.router)
    return app


app = criar_app()
