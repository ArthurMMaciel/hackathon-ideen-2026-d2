"""Regras de negócio das despesas. Puras: sem FastAPI e sem SQL."""

from datetime import date, datetime, timedelta

from app.erros import conflito, regra_violada

CATEGORIAS = ("TRANSPORTE", "HOSPEDAGEM", "ALIMENTACAO", "OUTROS")
SITUACOES = ("PENDENTE", "APROVADA", "RECUSADA", "PAGA")

# RN-06: toda despesa nasce PENDENTE.
SITUACAO_INICIAL = "PENDENTE"

# RN-02: limite por despesa, em centavos, inclusive.
LIMITE_CENTAVOS = {
    "ALIMENTACAO": 12000,
    "HOSPEDAGEM": 45000,
    "TRANSPORTE": 100000,
    "OUTROS": 100000,
}

# RN-04: idade máxima da despesa, em dias, inclusive.
DIAS_MAXIMOS = 60

# RN-07: transições permitidas.
TRANSICOES = {
    ("PENDENTE", "APROVADA"),
    ("PENDENTE", "RECUSADA"),
    ("APROVADA", "PAGA"),
}

# RN-10: situações que entram no resumo do mês.
SITUACOES_NO_RESUMO = ("APROVADA", "PAGA")


def formatar_reais(centavos: int) -> str:
    inteiro, resto = divmod(centavos, 100)
    return f"R$ {inteiro:,}".replace(",", ".") + f",{resto:02d}"


def validar_valor(valor_centavos: int) -> None:
    # RN-01: valor maior que zero.
    if valor_centavos <= 0:
        raise regra_violada("VALOR_INVALIDO", "O valor da despesa precisa ser maior que zero.")


def validar_limite(categoria: str, valor_centavos: int) -> None:
    # RN-02: limite por categoria, inclusive.
    limite = LIMITE_CENTAVOS[categoria]
    if valor_centavos > limite:
        raise regra_violada(
            "LIMITE_EXCEDIDO",
            f"O valor ultrapassa o limite de {formatar_reais(limite)} por despesa da categoria {categoria}.",
        )


def validar_data(data_despesa: date, agora: datetime) -> None:
    hoje = agora.date()
    # RN-03: a data não pode ser futura (hoje é aceito).
    if data_despesa > hoje:
        raise regra_violada("DATA_FUTURA", "A data da despesa não pode ser futura.")
    # RN-04: a data não pode ter mais de 60 dias (exatamente 60 é aceito).
    if data_despesa < hoje - timedelta(days=DIAS_MAXIMOS):
        raise regra_violada(
            "DATA_ANTIGA", f"A data da despesa não pode ter mais de {DIAS_MAXIMOS} dias."
        )


def validar_comprovante_unico(ja_existe: bool) -> None:
    # RN-05: o mesmo comprovante não pode ser lançado duas vezes pelo mesmo colaborador.
    if ja_existe:
        raise conflito(
            "COMPROVANTE_DUPLICADO",
            "Este número de comprovante já foi lançado por este colaborador.",
        )


def validar_transicao(atual: str, nova: str) -> None:
    # RN-07: só PENDENTE→APROVADA, PENDENTE→RECUSADA e APROVADA→PAGA.
    if (atual, nova) not in TRANSICOES:
        raise conflito(
            "TRANSICAO_INVALIDA",
            f"Não é possível mudar a situação de {atual} para {nova}.",
        )


def validar_motivo(motivo: str | None) -> str:
    # RN-08: recusar exige motivo não vazio.
    if motivo is None or not motivo.strip():
        raise regra_violada("MOTIVO_OBRIGATORIO", "Informe o motivo para recusar a despesa.")
    return motivo.strip()


def validar_exclusao(situacao: str) -> None:
    # RN-09: só despesa PENDENTE pode ser excluída.
    if situacao != "PENDENTE":
        raise conflito(
            "EXCLUSAO_NAO_PERMITIDA",
            f"Só despesa PENDENTE pode ser excluída; esta está {situacao}.",
        )


def intervalo_do_mes(ano: int, mes: int) -> tuple[date, date]:
    """RN-10 / PR-08: mês como intervalo semiaberto [dia 1, dia 1 do mês seguinte)."""
    inicio = date(ano, mes, 1)
    fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio, fim


def resumir_mes(despesas: list[tuple[str, str, int]]) -> dict:
    """RN-10: recebe (categoria, situacao, valor_centavos) do mês; soma só APROVADA e PAGA."""
    totais = {categoria: 0 for categoria in CATEGORIAS}
    quantidade = 0
    for categoria, situacao, valor_centavos in despesas:
        if situacao in SITUACOES_NO_RESUMO:
            totais[categoria] += valor_centavos
            quantidade += 1
    return {
        "totais_centavos": totais,
        "total_centavos": sum(totais.values()),
        "quantidade": quantidade,
    }
