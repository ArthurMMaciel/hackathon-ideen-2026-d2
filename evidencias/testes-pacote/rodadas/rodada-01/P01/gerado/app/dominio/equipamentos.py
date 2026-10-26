"""Regras de equipamento. Sem FastAPI e sem SQL."""

import re

from app.erros import conflito, regra_violada

TIPOS = ("NOTEBOOK", "PROJETOR", "HEADSET")
SITUACOES = ("DISPONIVEL", "EMPRESTADO", "MANUTENCAO")

_PATRIMONIO = re.compile(r"EQ-[0-9]{4}")


def validar_patrimonio(patrimonio: str) -> None:
    # RN-01: formato EQ-0000 (EQ, hífen, exatamente 4 dígitos)
    if not _PATRIMONIO.fullmatch(patrimonio):
        raise regra_violada("PATRIMONIO_INVALIDO", "O patrimônio deve seguir o formato EQ-0000 (EQ, hífen e 4 dígitos).")


def garantir_patrimonio_unico(ja_existe: bool, patrimonio: str) -> None:
    # RN-01: patrimônio único
    if ja_existe:
        raise conflito("PATRIMONIO_DUPLICADO", f"Já existe equipamento com o patrimônio {patrimonio}.")
