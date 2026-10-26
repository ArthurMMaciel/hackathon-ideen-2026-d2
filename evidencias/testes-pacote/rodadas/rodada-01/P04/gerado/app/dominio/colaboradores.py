"""Regras de colaboradores. Sem FastAPI e sem SQL."""

from app.erros import conflito


def validar_email_unico(email_ja_existe: bool) -> None:
    # RN-12: e-mail único entre colaboradores (sem diferenciar maiúsculas).
    if email_ja_existe:
        raise conflito("EMAIL_DUPLICADO", "Já existe colaborador cadastrado com esse e-mail.")
