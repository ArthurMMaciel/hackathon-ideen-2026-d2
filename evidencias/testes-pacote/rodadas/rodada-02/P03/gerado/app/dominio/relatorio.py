"""Cálculo do relatório de presença. Puro."""


def taxa_presenca(presentes: int, ausentes: int) -> float | None:
    # RN-12 / PR-08: presentes / (presentes + ausentes) em percentual, 2 casas; sem marcação, None.
    total = presentes + ausentes
    if total == 0:
        return None
    return round(presentes * 100 / total, 2)
