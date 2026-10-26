"""Relatório de cumprimento de prazo por prioridade. Sem FastAPI e sem SQL."""

from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.dominio.chamados import PRIORIDADES, dentro_do_prazo
from app.dominio.erros import regra_violada


def validar_periodo(data_inicial: date, data_final: date) -> None:
    # RN-09
    if data_inicial > data_final:
        raise regra_violada("PERIODO_INVALIDO", "A data inicial precisa ser igual ou anterior à data final.")


def limites_periodo(data_inicial: date, data_final: date, fuso) -> tuple[datetime, datetime]:
    # RN-09 e PR-04: dias fechados no fuso padrão, viram o intervalo [início, fim + 1 dia).
    inicio = datetime.combine(data_inicial, time(0, 0), tzinfo=fuso)
    fim = datetime.combine(data_final + timedelta(days=1), time(0, 0), tzinfo=fuso)
    return inicio, fim


def _percentual(parte: int, total: int) -> float:
    # PR-05: meio para cima (6,25 vira 6,3), sem o arredondamento bancário do round() de float.
    valor = (Decimal(parte) * 100 / Decimal(total)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return float(valor)


def montar_relatorio(resolvidos: list[dict]) -> list[dict]:
    """resolvidos: chamados com prioridade, resolvido_em e prazo_em já dentro do período."""
    linhas = []
    for prioridade in PRIORIDADES:
        da_prioridade = [c for c in resolvidos if c["prioridade"] == prioridade]
        no_prazo = sum(1 for c in da_prioridade if dentro_do_prazo(c["resolvido_em"], c["prazo_em"]))  # RN-03
        total = len(da_prioridade)
        # PR-05: 1 casa decimal; sem resolvidos, percentual vazio.
        percentual = _percentual(no_prazo, total) if total else None
        linhas.append({
            "prioridade": prioridade,
            "resolvidos": total,
            "dentro_do_prazo": no_prazo,
            "percentual_dentro_do_prazo": percentual,
        })
    return linhas
