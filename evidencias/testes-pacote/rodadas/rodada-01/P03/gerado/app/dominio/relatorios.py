"""Cálculos de relatório."""

from decimal import ROUND_HALF_UP, Decimal


def taxa_presenca(presentes: int, ausentes: int) -> float | None:
    # RN-12: presentes / (presentes + ausentes) x 100, 1 casa, meio para cima; sem marcações, vazio (PR-10)
    total = presentes + ausentes
    if total == 0:
        return None
    taxa = Decimal(presentes) * 100 / Decimal(total)
    return float(taxa.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
