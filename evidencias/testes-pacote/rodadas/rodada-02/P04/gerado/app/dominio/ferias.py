"""Regras de férias. Funções puras: recebem dados e `agora`, levantam erros de app.dominio.erros."""

import calendar
from datetime import date, datetime, timedelta

from app.dominio.erros import conflito, regra_violada

EQUIPES = ("DADOS", "PRODUTO", "SUPORTE")
SOLICITADA, APROVADA, REPROVADA, CANCELADA = "SOLICITADA", "APROVADA", "REPROVADA", "CANCELADA"
ATIVAS = (SOLICITADA, APROVADA)

DIAS_MINIMOS = 5
DIAS_MAXIMOS = 30
ANTECEDENCIA_MINIMA = 30


def hoje(agora: datetime) -> date:
    """"Hoje" é a data de `agora` no fuso padrão (o relógio injetável já entrega nesse fuso)."""
    return agora.date()


def sobrepoe(inicio_a: date, fim_a: date, inicio_b: date, fim_b: date) -> bool:
    """Períodos fechados [início, fim]: dias seguidos não se sobrepõem."""
    return inicio_a <= fim_b and inicio_b <= fim_a


def calcular_dias(inicio: date, fim: date) -> int:
    # RN-01: dias corridos contando o primeiro e o último.
    if fim < inicio:
        raise regra_violada("PERIODO_INVALIDO", "A data de fim não pode ser anterior à data de início.")
    return (fim - inicio).days + 1


def validar_duracao(dias: int) -> None:
    # RN-02: mínimo 5 e máximo 30 dias, inclusive.
    if not DIAS_MINIMOS <= dias <= DIAS_MAXIMOS:
        raise regra_violada(
            "DURACAO_INVALIDA",
            f"O período de férias precisa ter de {DIAS_MINIMOS} a {DIAS_MAXIMOS} dias; foram pedidos {dias}.",
        )


def validar_antecedencia(inicio: date, agora: datetime) -> None:
    # RN-03: início com pelo menos 30 dias de antecedência.
    limite = hoje(agora) + timedelta(days=ANTECEDENCIA_MINIMA)
    if inicio < limite:
        raise regra_violada(
            "ANTECEDENCIA_INSUFICIENTE",
            f"As férias precisam começar com pelo menos {ANTECEDENCIA_MINIMA} dias de antecedência "
            f"(a partir de {limite.isoformat()}).",
        )


def saldo_disponivel(saldo: int, dias_pendentes: int) -> int:
    # RN-04 / PR-04: o saldo guardado já exclui os aprovados; descontam-se os pendentes.
    return saldo - dias_pendentes


def validar_saldo(dias: int, saldo: int, dias_pendentes: int) -> None:
    # RN-04: dias pedidos não passam do saldo disponível.
    disponivel = saldo_disponivel(saldo, dias_pendentes)
    if dias > disponivel:
        raise conflito(
            "SALDO_INSUFICIENTE",
            f"Saldo insuficiente: foram pedidos {dias} dias e o saldo disponível é de {disponivel} dias.",
        )


def validar_sem_sobreposicao(inicio: date, fim: date, periodos_ativos: list[tuple[date, date]]) -> None:
    # RN-05: o colaborador não pode ter duas solicitações SOLICITADA/APROVADA com dias em comum.
    for outro_inicio, outro_fim in periodos_ativos:
        if sobrepoe(inicio, fim, outro_inicio, outro_fim):
            raise conflito(
                "SOBREPOSICAO",
                f"O colaborador já tem férias solicitadas ou aprovadas de {outro_inicio.isoformat()} "
                f"a {outro_fim.isoformat()}, com dias em comum.",
            )


def validar_decisao(situacao: str) -> None:
    # RN-06: só SOLICITADA pode ser aprovada ou reprovada.
    if situacao != SOLICITADA:
        raise conflito(
            "TRANSICAO_INVALIDA",
            f"Só solicitações SOLICITADA podem ser aprovadas ou reprovadas; esta está {situacao}.",
        )


def validar_limite_equipe(inicio: date, fim: date, aprovadas_equipe: list[tuple[date, date, str]]) -> None:
    # RN-07: no máximo 1 pessoa da equipe com férias APROVADA em um mesmo dia.
    for outro_inicio, outro_fim, nome in aprovadas_equipe:
        if sobrepoe(inicio, fim, outro_inicio, outro_fim):
            raise conflito(
                "LIMITE_EQUIPE",
                f"{nome}, da mesma equipe, já tem férias aprovadas de {outro_inicio.isoformat()} "
                f"a {outro_fim.isoformat()}. Só uma pessoa por equipe pode estar de férias no mesmo dia.",
            )


def saldo_apos_aprovacao(saldo: int, dias: int) -> int:
    # RN-08: ao aprovar, os dias saem do saldo.
    return saldo - dias


def validar_cancelamento(situacao: str, inicio: date, agora: datetime) -> None:
    # RN-09: só SOLICITADA ou APROVADA, e só até o dia anterior ao início.
    if situacao not in ATIVAS:
        raise conflito(
            "TRANSICAO_INVALIDA",
            f"Só solicitações SOLICITADA ou APROVADA podem ser canceladas; esta está {situacao}.",
        )
    if hoje(agora) >= inicio:
        raise regra_violada(
            "CANCELAMENTO_FORA_DO_PRAZO",
            f"O cancelamento só é possível até o dia anterior ao início ({(inicio - timedelta(days=1)).isoformat()}).",
        )


def saldo_apos_cancelamento(saldo: int, dias: int, situacao: str) -> int:
    # RN-10: se estava aprovada, os dias voltam para o saldo.
    return saldo + dias if situacao == APROVADA else saldo


def montar_calendario(ano: int, mes: int, aprovadas: list[dict]) -> list[dict]:
    """RF-09: um item por dia do mês, com quem tem férias APROVADA em cada equipe.

    `aprovadas`: dicts com inicio, fim (date), colaborador_id, nome, equipe, solicitacao_id.
    """
    ultimo = calendar.monthrange(ano, mes)[1]
    dias = []
    for numero in range(1, ultimo + 1):
        dia = date(ano, mes, numero)
        equipes: dict[str, list[dict]] = {equipe: [] for equipe in EQUIPES}
        for s in aprovadas:
            if s["inicio"] <= dia <= s["fim"]:
                equipes[s["equipe"]].append(
                    {"colaborador_id": s["colaborador_id"], "nome": s["nome"], "solicitacao_id": s["solicitacao_id"]}
                )
        for lista in equipes.values():
            lista.sort(key=lambda p: (p["nome"], p["colaborador_id"]))
        dias.append({"data": dia.isoformat(), "equipes": equipes})
    return dias
