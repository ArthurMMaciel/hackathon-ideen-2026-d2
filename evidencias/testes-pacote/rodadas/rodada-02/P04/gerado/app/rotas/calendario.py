"""RF-09: calendário do mês com quem está de férias aprovadas, por equipe."""

import calendar
import sqlite3
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.banco import obter_conexao
from app.dominio import ferias
from app.repositorio import ferias as repo
from app.tipos import Mes

router = APIRouter(prefix="/api/calendario", tags=["calendario"])


@router.get("")
def calendario_do_mes(mes: Annotated[Mes, Query()], conn: sqlite3.Connection = Depends(obter_conexao)):
    ano, numero = int(mes[:4]), int(mes[5:7])
    primeiro = date(ano, numero, 1)
    ultimo = date(ano, numero, calendar.monthrange(ano, numero)[1])
    aprovadas = repo.aprovadas_no_periodo(conn, primeiro, ultimo)
    return {"mes": mes, "dias": ferias.montar_calendario(ano, numero, aprovadas)}
