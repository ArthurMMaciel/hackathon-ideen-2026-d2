"""Regras puras de inscrição. Recebem dados e `agora`; não conhecem HTTP nem SQL."""

from datetime import datetime, timedelta

from app.erros import conflito, regra_violada

CONFIRMADA = "CONFIRMADA"
ESPERA = "ESPERA"
CANCELADA = "CANCELADA"
PRESENTE = "PRESENTE"
AUSENTE = "AUSENTE"

ATIVAS = (CONFIRMADA, ESPERA)
OCUPAM_VAGA = (CONFIRMADA, PRESENTE, AUSENTE)
ANTECEDENCIA_MINIMA = timedelta(hours=24)


def situacao_inicial(vagas: int, ocupadas: int) -> str:
    # RN-05: com vaga nasce CONFIRMADA; lotada nasce ESPERA
    return CONFIRMADA if ocupadas < vagas else ESPERA


def posicao_na_espera(inscricao_id: int, ids_espera_em_ordem: list[int]) -> int | None:
    # RN-06: fila por ordem de chegada; a mais antiga é a posição 1
    if inscricao_id in ids_espera_em_ordem:
        return ids_espera_em_ordem.index(inscricao_id) + 1
    return None


def validar_nao_duplicada(existe_ativa: bool) -> None:
    # RN-07: o mesmo e-mail não pode ter duas inscrições ativas na mesma turma
    if existe_ativa:
        raise conflito("INSCRICAO_DUPLICADA", "Este e-mail já tem uma inscrição confirmada ou em espera nesta turma.")


def validar_prazo_inscricao(inicio: datetime, agora: datetime) -> None:
    # RN-08: inscrições fecham 24 horas antes do início (exatamente 24 h antes já recusa)
    if agora >= inicio - ANTECEDENCIA_MINIMA:
        raise regra_violada("INSCRICOES_ENCERRADAS", "As inscrições fecham 24 horas antes do início da turma.")


def validar_cancelamento(situacao: str, inicio: datetime, agora: datetime) -> None:
    # RN-09: cancelamento só antes do início e só para inscrição CONFIRMADA ou ESPERA
    if situacao not in ATIVAS:
        raise regra_violada(
            "SITUACAO_NAO_CANCELAVEL",
            f"Só inscrições confirmadas ou em espera podem ser canceladas; esta está {situacao}.",
        )
    if agora >= inicio:
        raise regra_violada("CANCELAMENTO_ENCERRADO", "O cancelamento só é permitido até o início da turma.")


def promove_espera(situacao_anterior: str) -> bool:
    # RN-10: cancelar uma CONFIRMADA libera a vaga para a primeira da espera
    return situacao_anterior == CONFIRMADA


def validar_presenca(situacao: str, inicio: datetime, agora: datetime) -> None:
    # RN-11: presença só depois do início e só para inscrição CONFIRMADA
    if agora < inicio:
        raise regra_violada("PRESENCA_ANTES_DO_INICIO", "A presença só pode ser marcada depois do início da turma.")
    if situacao != CONFIRMADA:
        raise regra_violada(
            "PRESENCA_SITUACAO_INVALIDA",
            f"A presença só pode ser marcada em inscrição confirmada; esta está {situacao}.",
        )
