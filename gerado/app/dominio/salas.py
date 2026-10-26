"""Regras da sala e da consulta de salas livres."""

from datetime import datetime

from app.dominio.erros import conflito, regra_violada

LOCAIS = ("SAO_PAULO", "ARARAQUARA", "COWORKING")
RECURSOS = ("TV", "VIDEOCONFERENCIA", "QUADRO")


def normalizar_recursos(recursos: list[str]) -> list[str]:
    # RN-09: recursos sem repetição; guardados na ordem fixa TV, VIDEOCONFERENCIA, QUADRO.
    if len(set(recursos)) != len(recursos):
        raise regra_violada("RECURSOS_REPETIDOS", "A lista de recursos não pode repetir itens.")
    return [r for r in RECURSOS if r in recursos]


def verificar_nome_unico(nome: str, local: str, existentes: list[tuple[str, str]]) -> None:
    # RN-10: nome único dentro do mesmo local, sem diferenciar maiúsculas.
    for outro_nome, outro_local in existentes:
        if outro_local == local and outro_nome.casefold() == nome.casefold():
            raise conflito("SALA_DUPLICADA", f"Já existe uma sala chamada '{nome}' neste local.")


def validar_intervalo_consulta(inicio: datetime, fim: datetime) -> None:
    # RN-07: o intervalo da consulta exige fim depois do início.
    if fim <= inicio:
        raise regra_violada("INTERVALO_INVALIDO", "O fim do intervalo precisa ser depois do início.")


def filtrar_livres(
    salas: list[dict], ocupadas: set[int], local: str | None, capacidade_minima: int | None
) -> list[dict]:
    # RN-07: sem reserva ATIVA sobreposta; filtros opcionais de local e capacidade mínima (inclusive).
    return [
        s
        for s in salas
        if s["id"] not in ocupadas
        and (local is None or s["local"] == local)
        and (capacidade_minima is None or s["capacidade"] >= capacidade_minima)
    ]
