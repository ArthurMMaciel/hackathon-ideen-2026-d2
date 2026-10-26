"""Validações de salas."""


def validar_sala(capacidade: int, recursos: list[str]) -> None:
    # RN-07
    if len(recursos) != len(set(recursos)):
        from app.dominio.erros import regra_violada
        raise regra_violada("RECURSOS_DUPLICADOS", "Recursos não podem se repetir.")
