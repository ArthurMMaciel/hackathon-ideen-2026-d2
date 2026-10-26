"""Regras de cadastro de colaborador."""

from app.dominio.erros import conflito


def validar_email_livre(ja_existe: bool) -> None:
    # RN-11 / PR-11: e-mail único, sem diferenciar maiúsculas.
    if ja_existe:
        raise conflito("EMAIL_DUPLICADO", "Já existe um colaborador cadastrado com este e-mail.")
