"""Relatório de cumprimento de prazo por prioridade. Funções puras."""

from datetime import date, datetime, time, timedelta

from app.dominio.chamados import PRIORIDADES
from app.erros import regra_violada
from app.relogio import FUSO


def periodo(data_inicial: date, data_final: date) -> tuple[datetime, datetime]:
    # RN-10: datas inclusivas pelo dia local; intervalo semiaberto [inicial 00:00, final+1 00:00).
    if data_final < data_inicial:
        raise regra_violada("PERIODO_INVALIDO", "A data final deve ser igual ou posterior à data inicial.")
    if data_final >= date.max:
        raise regra_violada("PERIODO_INVALIDO", "A data final deve ser anterior a 31/12/9999.")
    inicio = datetime.combine(data_inicial, time(0, 0), tzinfo=FUSO)
    fim = datetime.combine(data_final + timedelta(days=1), time(0, 0), tzinfo=FUSO)
    return inicio, fim


def montar(resolvidos: list[tuple[str, bool]]) -> list[dict]:
    """Recebe (prioridade, dentro_do_prazo) de cada chamado resolvido no período."""
    linhas = []
    for prioridade in PRIORIDADES:
        da_prioridade = [dentro for p, dentro in resolvidos if p == prioridade]
        total = len(da_prioridade)
        dentro = sum(1 for d in da_prioridade if d)
        # PR-05: percentual com 1 casa decimal; vazio quando não há resolvidos.
        percentual = round(dentro * 100 / total, 1) if total else None
        linhas.append({
            "prioridade": prioridade,
            "resolvidos": total,
            "dentro_do_prazo": dentro,
            "percentual_dentro_do_prazo": percentual,
        })
    return linhas
