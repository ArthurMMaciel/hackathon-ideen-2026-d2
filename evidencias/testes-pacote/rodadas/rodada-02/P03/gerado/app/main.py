"""Cria a aplicação: API em /api, tela em /."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app import banco
from app.dominio.erros import ErroNegocio
from app.relogio import obter_agora
from app.rotas import inscricoes, turmas

ESTATICO = Path(__file__).parent / "estatico"


def criar_app(caminho_db: str | None = None) -> FastAPI:
    caminho = caminho_db or banco.caminho_padrao()

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        # Mesmo relógio das rotas: o de teste nos testes, APP_AGORA ou a hora real no servidor.
        agora = app.dependency_overrides.get(obter_agora, obter_agora)()
        banco.iniciar(caminho, agora)
        yield

    app = FastAPI(title="Inscrição em treinamentos", lifespan=ciclo_de_vida)
    app.state.caminho_db = caminho

    @app.exception_handler(ErroNegocio)
    async def tratar_erro_negocio(request: Request, exc: ErroNegocio) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content={"erro": exc.codigo, "mensagem": exc.mensagem})

    @app.get("/api/saude")
    def saude():
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def tela():
        # HTMLResponse com o conteúdo lido, sem FileResponse (CVE-2025-62727 em versões antigas do starlette).
        return HTMLResponse((ESTATICO / "index.html").read_text(encoding="utf-8"))

    app.include_router(turmas.router)
    app.include_router(inscricoes.router)
    return app


app = criar_app()
