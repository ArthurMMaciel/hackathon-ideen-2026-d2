"""Regras puras de turma. Recebem dados e `agora`; não conhecem HTTP nem SQL."""

from datetime import datetime

from app.erros import regra_violada


def validar_inicio_futuro(inicio: datetime, agora: datetime) -> None:
    # RN-04: turma só é cadastrada com início posterior ao momento do cadastro
    if inicio <= agora:
        raise regra_violada("INICIO_NO_PASSADO", "O início da turma precisa ser posterior ao momento do cadastro.")


def vagas_restantes(vagas: int, ocupadas: int) -> int:
    # RN-13: vagas restantes = vagas - ocupadas, nunca menor que 0
    return max(vagas - ocupadas, 0)
