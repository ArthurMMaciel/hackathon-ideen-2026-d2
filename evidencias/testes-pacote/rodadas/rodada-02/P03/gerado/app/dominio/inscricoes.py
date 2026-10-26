"""Regras de inscrição, espera, cancelamento e presença. Puras: sem FastAPI e sem SQL."""

from datetime import datetime, timedelta

from app.dominio.erros import conflito, regra_violada

ANTECEDENCIA_INSCRICAO = timedelta(hours=24)
ATIVAS = ("CONFIRMADA", "ESPERA")
MARCACOES_PRESENCA = ("PRESENTE", "AUSENTE")


def normalizar_email(email: str) -> str:
    # PR-05: e-mail comparado e guardado em minúsculas.
    return email.strip().lower()


def validar_janela_inscricao(inicio_turma: datetime, agora: datetime) -> None:
    # RN-06: aceita até 24 horas antes do início, inclusive (agora <= início - 24h).
    if agora > inicio_turma - ANTECEDENCIA_INSCRICAO:
        raise regra_violada("INSCRICOES_ENCERRADAS",
                            "As inscrições fecham 24 horas antes do início da turma.")


def validar_email_unico(ja_tem_inscricao_ativa: bool) -> None:
    # RN-05: um e-mail só pode ter uma inscrição CONFIRMADA ou ESPERA por turma.
    if ja_tem_inscricao_ativa:
        raise conflito("INSCRICAO_DUPLICADA",
                       "Este e-mail já tem uma inscrição confirmada ou em espera nesta turma.")


def situacao_inicial(vagas: int, ocupadas: int) -> str:
    # RN-03: com vaga nasce CONFIRMADA; lotada nasce ESPERA.
    return "CONFIRMADA" if ocupadas < vagas else "ESPERA"


def validar_cancelamento(situacao: str, inicio_turma: datetime, agora: datetime) -> None:
    # RN-07: cancelamento só antes do início (agora < início).
    if agora >= inicio_turma:
        raise regra_violada("CANCELAMENTO_ENCERRADO",
                            "Não é possível cancelar depois do início da turma.")
    # RN-08: só inscrição ativa pode ser cancelada.
    if situacao not in ATIVAS:
        raise conflito("SITUACAO_NAO_CANCELAVEL",
                       f"Só inscrição CONFIRMADA ou em ESPERA pode ser cancelada; esta está {situacao}.")


def deve_promover(situacao_cancelada: str) -> bool:
    # RN-09: só o cancelamento de uma CONFIRMADA libera vaga para a espera.
    return situacao_cancelada == "CONFIRMADA"


def primeira_da_espera(inscricoes: list[dict]) -> dict | None:
    # RN-04: a mais antiga (menor id) em ESPERA é a primeira da fila.
    espera = [i for i in inscricoes if i["situacao"] == "ESPERA"]
    return min(espera, key=lambda i: i["id"]) if espera else None


def posicoes_espera(inscricoes: list[dict]) -> dict[int, int]:
    # RN-04: posição 1 para a mais antiga em ESPERA, por ordem de chegada (id).
    espera = sorted((i["id"] for i in inscricoes if i["situacao"] == "ESPERA"))
    return {id_: posicao for posicao, id_ in enumerate(espera, start=1)}


def validar_presenca(situacao: str, inicio_turma: datetime, agora: datetime) -> None:
    # RN-10: presença só a partir do início (agora >= início).
    if agora < inicio_turma:
        raise regra_violada("TURMA_NAO_INICIADA", "A presença só pode ser marcada depois do início da turma.")
    # RN-11 / PR-09: só inscrição CONFIRMADA recebe presença.
    if situacao != "CONFIRMADA":
        raise conflito("SITUACAO_SEM_PRESENCA",
                       f"Só inscrição CONFIRMADA pode receber presença; esta está {situacao}.")
