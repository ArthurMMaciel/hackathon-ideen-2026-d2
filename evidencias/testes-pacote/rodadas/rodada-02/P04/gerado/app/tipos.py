"""Tipos de entrada prontos. Os limites evitam HTTP 500 com valores extremos (id gigante, ano 9999).

No corpo (modelos Pydantic): use os tipos direto, ex.: `inicio: DataHora`.
Em caminho e consulta: sempre na forma Annotated[Tipo, Path()] ou Annotated[Tipo, Query()],
ex.: `id: Annotated[Id, Path()]`, `dia: Annotated[Data, Query()]`. Com `= Query(...)` o validador é ignorado.
"""

import re
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, BeforeValidator, Field, StringConstraints

ID_MAXIMO = 2_147_483_647
ANO_MINIMO = 2000
ANO_MAXIMO = 2100

_FORMATO_MES = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
_FORMATO_DATA = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def _ano_na_faixa(valor):
    if not ANO_MINIMO <= valor.year <= ANO_MAXIMO:
        raise ValueError(f"o ano precisa estar entre {ANO_MINIMO} e {ANO_MAXIMO}")
    return valor


def _data_estrita(valor):
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if not isinstance(valor, str) or not _FORMATO_DATA.match(valor):
        raise ValueError("a data precisa estar no formato AAAA-MM-DD")
    return date.fromisoformat(valor)


Id = Annotated[int, Field(ge=1, le=ID_MAXIMO)]

# Data e hora com fuso obrigatório (ISO 8601 com offset).
DataHora = Annotated[AwareDatetime, AfterValidator(_ano_na_faixa)]

# Data de calendário, sem horário: só "AAAA-MM-DD".
Data = Annotated[date, BeforeValidator(_data_estrita), AfterValidator(_ano_na_faixa)]

def _mes_estrito(valor):
    if not isinstance(valor, str) or not _FORMATO_MES.match(valor):
        raise ValueError("o mês precisa estar no formato AAAA-MM")
    if not ANO_MINIMO <= int(valor[:4]) <= ANO_MAXIMO:
        raise ValueError(f"o ano precisa estar entre {ANO_MINIMO} e {ANO_MAXIMO}")
    return valor


# Mês de calendário: só "AAAA-MM", mês 01 a 12.
Mes = Annotated[str, BeforeValidator(_mes_estrito)]

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
TextoLongo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Email = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
]

# Valor em dinheiro: guarde em centavos (inteiro). Ajuste o teto ao pedido.
Centavos = Annotated[int, Field(ge=0, le=100_000_000)]
