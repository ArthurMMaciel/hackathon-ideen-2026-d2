"""Regras de sala. Funções puras."""

from collections.abc import Iterable

from app.erros import conflito

LOCAIS = ("SAO_PAULO", "ARARAQUARA", "COWORKING")
RECURSOS = ("TV", "VIDEOCONFERENCIA", "QUADRO")


def validar_nome_unico(ja_existe: bool, nome: str) -> None:
    # RN-10: nome único, sem diferenciar maiúsculas.
    if ja_existe:
        raise conflito("SALA_NOME_DUPLICADO", f"Já existe uma sala com o nome \"{nome}\".")


def filtrar_livres(
    salas: Iterable[dict], ocupadas: set[int], local: str | None, capacidade_minima: int | None
) -> list[dict]:
    # RN-07: sem reserva ativa sobreposta e atendendo aos filtros opcionais.
    return [
        s
        for s in salas
        if s["id"] not in ocupadas
        and (local is None or s["local"] == local)
        and (capacidade_minima is None or s["capacidade"] >= capacidade_minima)
    ]
