"""Regras de turma. Puras: recebem dados e `agora`, sem FastAPI e sem SQL."""

from datetime import datetime

from app.dominio.erros import regra_violada

VAGAS_MINIMAS = 1
VAGAS_MAXIMAS = 50
DURACAO_MINIMA = 1
DURACAO_MAXIMA = 1440
SITUACOES_QUE_OCUPAM_VAGA = ("CONFIRMADA", "PRESENTE", "AUSENTE")


def validar_nova_turma(inicio: datetime, duracao_minutos: int, vagas: int, agora: datetime) -> None:
    # RN-01: vagas de 1 a 50, inclusive.
    if not VAGAS_MINIMAS <= vagas <= VAGAS_MAXIMAS:
        raise regra_violada("VAGAS_INVALIDAS",
                            f"A quantidade de vagas precisa estar entre {VAGAS_MINIMAS} e {VAGAS_MAXIMAS}.")
    # RN-02 / PR-03: duração de 1 a 1440 minutos, inclusive.
    if not DURACAO_MINIMA <= duracao_minutos <= DURACAO_MAXIMA:
        raise regra_violada("DURACAO_INVALIDA",
                            f"A duração precisa estar entre {DURACAO_MINIMA} e {DURACAO_MAXIMA} minutos.")
    # PR-04: turma nova começa depois de agora.
    if inicio <= agora:
        raise regra_violada("INICIO_NO_PASSADO", "O início da turma precisa ser uma data e hora futura.")


def vagas_restantes(vagas: int, ocupadas: int) -> int:
    # RN-13: vagas menos CONFIRMADA + PRESENTE + AUSENTE, nunca negativo.
    return max(0, vagas - ocupadas)


def eh_futura(inicio: datetime, agora: datetime) -> bool:
    # RN-14: turma futura tem início depois de agora.
    return inicio > agora
