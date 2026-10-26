"""Garante os limites dos tipos prontos e o relógio da carga inicial. Mantenha estes testes."""

from typing import Annotated

import pytest
from fastapi import FastAPI, Path, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.tipos import Data, DataHora, Id, Texto


def _app_de_teste() -> FastAPI:
    app = FastAPI()

    class Corpo(BaseModel):
        inicio: DataHora
        titulo: Texto

    @app.get("/itens/{id}")
    def item(id: Annotated[Id, Path()]):
        return {"id": id}

    @app.get("/dia")
    def dia(data: Annotated[Data, Query()]):
        return {"data": data.isoformat()}

    @app.post("/corpo")
    def corpo(dados: Corpo):
        return {"titulo": dados.titulo}

    return app


@pytest.fixture
def api():
    with TestClient(_app_de_teste()) as c:
        yield c


def test_id_gigante_recusado_sem_erro_500(api):
    assert api.get("/itens/99999999999999999999").status_code == 422
    assert api.get("/itens/0").status_code == 422
    assert api.get("/itens/7").json() == {"id": 7}


@pytest.mark.parametrize("valor", ["2030-01-05T00:00:00", "05/01/2030", "1999-12-31", "9999-12-31"])
def test_data_estrita_recusa_formatos_e_anos_fora_da_faixa(api, valor):
    assert api.get("/dia", params={"data": valor}).status_code == 422


def test_data_valida(api):
    assert api.get("/dia", params={"data": "2030-01-05"}).json() == {"data": "2030-01-05"}


@pytest.mark.parametrize("inicio", ["2030-01-07T10:00:00", "9999-12-31T23:00:00-03:00"])
def test_data_hora_exige_fuso_e_ano_na_faixa(api, inicio):
    assert api.post("/corpo", json={"inicio": inicio, "titulo": "x"}).status_code == 422


def test_texto_so_com_espacos_recusado(api):
    assert api.post("/corpo", json={"inicio": "2030-01-07T10:00:00-03:00", "titulo": "   "}).status_code == 422


def test_carga_inicial_recebe_relogio_de_teste(tmp_path, relogio, monkeypatch):
    from app import banco
    from app.main import criar_app
    from app.relogio import obter_agora

    recebido = {}
    monkeypatch.setattr(banco, "carga_inicial", lambda conn, agora: recebido.setdefault("agora", agora))
    app = criar_app(str(tmp_path / "t.db"))
    app.dependency_overrides[obter_agora] = relogio
    with TestClient(app):
        pass
    assert recebido["agora"] == relogio.agora
