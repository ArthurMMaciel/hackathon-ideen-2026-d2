from datetime import datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.banco import obter_conexao
from app.dominio.relatorios import ocupacao
from app.relogio import FUSO
from app.repositorio import reservas as repo_reservas, salas as repo_salas
from app.tipos import Data

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


@router.get("/ocupacao")
def relatorio(dia: Annotated[Data, Query()], conn=Depends(obter_conexao)):
    inicio = datetime.combine(dia, time(8), FUSO)
    fim = datetime.combine(dia, time(18), FUSO)
    resultado = []
    for sala in repo_salas.listar(conn):
        intervalos = repo_reservas.intervalos(conn, sala["id"], inicio, fim)
        minutos, percentual = ocupacao(intervalos, inicio, fim)
        resultado.append({"sala_id": sala["id"], "sala_nome": sala["nome"],
                          "dia": dia.isoformat(), "minutos_ocupados": minutos,
                          "percentual": percentual})
    return resultado
