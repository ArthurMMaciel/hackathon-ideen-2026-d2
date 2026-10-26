"""Regras de férias. Funções puras: recebem dados e `hoje`/`agora`, sem FastAPI e sem SQL."""

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.erros import conflito, regra_violada

DURACAO_MINIMA = 5
DURACAO_MAXIMA = 30
ANTECEDENCIA_DIAS = 30
ATIVAS = ("SOLICITADA", "APROVADA")
EQUIPES = ("DADOS", "PRODUTO", "SUPORTE")


@dataclass(frozen=True)
class Periodo:
    inicio: date
    fim: date


def sobrepoe(a: Periodo, b: Periodo) -> bool:
    """Períodos fechados [inicio, fim]: dias consecutivos não se sobrepõem."""
    return a.inicio <= b.fim and b.inicio <= a.fim


def contar_dias(periodo: Periodo) -> int:
    # RN-01: dias corridos contando o primeiro e o último dia.
    if periodo.fim < periodo.inicio:
        raise regra_violada("PERIODO_INVALIDO", "A data de fim não pode ser anterior à data de início.")
    return (periodo.fim - periodo.inicio).days + 1


def validar_duracao(dias: int) -> None:
    # RN-02: mínimo 5 e máximo 30 dias, inclusive.
    if not DURACAO_MINIMA <= dias <= DURACAO_MAXIMA:
        raise regra_violada(
            "DURACAO_INVALIDA",
            f"As férias devem ter entre {DURACAO_MINIMA} e {DURACAO_MAXIMA} dias; o pedido tem {dias}.",
        )


def validar_antecedencia(inicio: date, hoje: date) -> None:
    # RN-03: início pelo menos 30 dias depois da data do pedido.
    minimo = hoje + timedelta(days=ANTECEDENCIA_DIAS)
    if inicio < minimo:
        raise regra_violada(
            "ANTECEDENCIA_INSUFICIENTE",
            f"O início precisa ter pelo menos {ANTECEDENCIA_DIAS} dias de antecedência (a partir de {minimo.isoformat()}).",
        )


def saldo_disponivel(saldo_atual: int, dias_solicitados_pendentes: int) -> int:
    # RN-04 / PR-04: aprovadas já saíram do saldo atual; descontam-se só as pendentes.
    return saldo_atual - dias_solicitados_pendentes


def validar_saldo(dias: int, disponivel: int) -> None:
    # RN-04: dias do pedido não podem passar do saldo disponível.
    if dias > disponivel:
        raise regra_violada(
            "SALDO_INSUFICIENTE",
            f"O pedido tem {dias} dias, mas o saldo disponível é de {disponivel} dias.",
        )


def validar_sem_sobreposicao_colaborador(novo: Periodo, ativos: list[Periodo]) -> None:
    # RN-05: sem duas solicitações SOLICITADA/APROVADA do mesmo colaborador com dias em comum.
    if any(sobrepoe(novo, p) for p in ativos):
        raise conflito(
            "SOBREPOSICAO_COLABORADOR",
            "O colaborador já tem férias solicitadas ou aprovadas com dias em comum com esse período.",
        )


def validar_pode_decidir(situacao: str) -> None:
    # RN-06: só SOLICITADA pode ser aprovada ou reprovada.
    if situacao != "SOLICITADA":
        raise conflito(
            "SITUACAO_INVALIDA",
            f"Só solicitações SOLICITADA podem ser aprovadas ou reprovadas; esta está {situacao}.",
        )


def validar_limite_equipe(periodo: Periodo, aprovadas_da_equipe: list[Periodo]) -> None:
    # RN-07: no máximo 1 pessoa por equipe com férias APROVADA no mesmo dia.
    if any(sobrepoe(periodo, p) for p in aprovadas_da_equipe):
        raise conflito(
            "LIMITE_EQUIPE",
            "Já existe outra pessoa da mesma equipe com férias aprovadas em pelo menos um desses dias.",
        )


def saldo_apos_aprovar(saldo: int, dias: int) -> int:
    # RN-08: ao aprovar, os dias saem do saldo.
    return saldo - dias


def validar_cancelamento(situacao: str, inicio: date, hoje: date) -> None:
    # RN-09: SOLICITADA ou APROVADA, até o dia anterior ao início.
    if situacao not in ATIVAS:
        raise conflito(
            "SITUACAO_INVALIDA",
            f"Só solicitações SOLICITADA ou APROVADA podem ser canceladas; esta está {situacao}.",
        )
    if hoje >= inicio:
        raise regra_violada(
            "CANCELAMENTO_FORA_DO_PRAZO",
            "O cancelamento só é permitido até o dia anterior ao início das férias.",
        )


def saldo_apos_cancelar(saldo: int, situacao_anterior: str, dias: int) -> int:
    # RN-10: se estava aprovada, os dias voltam para o saldo.
    return saldo + dias if situacao_anterior == "APROVADA" else saldo


_MES = re.compile(r"^(\d{4})-(\d{2})$")


def interpretar_mes(texto: str) -> tuple[date, date]:
    """'YYYY-MM' -> (primeiro dia, último dia). PR-06."""
    m = _MES.match(texto or "")
    if not m or not 1 <= int(m.group(2)) <= 12 or int(m.group(1)) < 1:
        raise regra_violada("MES_INVALIDO", "Informe o mês no formato AAAA-MM, por exemplo 2030-03.")
    ano, mes = int(m.group(1)), int(m.group(2))
    return date(ano, mes, 1), date(ano, mes, calendar.monthrange(ano, mes)[1])


def montar_calendario(primeiro: date, ultimo: date, aprovadas: list[dict]) -> list[dict]:
    """Um item por dia do mês com quem está de férias aprovadas, por equipe (RF-09)."""
    dias = []
    atual = primeiro
    while atual <= ultimo:
        equipes: dict[str, list[dict]] = {e: [] for e in EQUIPES}
        for s in aprovadas:
            if s["inicio"] <= atual <= s["fim"]:
                equipes[s["equipe"]].append(
                    {"colaborador_id": s["colaborador_id"], "nome": s["nome"], "solicitacao_id": s["id"]}
                )
        dias.append({"data": atual.isoformat(), "equipes": equipes})
        atual += timedelta(days=1)
    return dias
