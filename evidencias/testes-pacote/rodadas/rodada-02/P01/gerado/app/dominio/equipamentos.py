"""Regras de equipamento. Módulo puro: sem FastAPI e sem SQL."""

from app.dominio.erros import conflito

TIPOS = ("NOTEBOOK", "PROJETOR", "HEADSET")
SITUACOES = ("DISPONIVEL", "EMPRESTADO", "MANUTENCAO")
PADRAO_PATRIMONIO = r"^EQ-[0-9]{4}$"  # RN-01: formato EQ-0000


def validar_patrimonio_unico(patrimonio: str, ja_existe: bool) -> None:
    # RN-01: patrimônio único
    if ja_existe:
        raise conflito("PATRIMONIO_DUPLICADO", f"Já existe equipamento com o patrimônio {patrimonio}.")
