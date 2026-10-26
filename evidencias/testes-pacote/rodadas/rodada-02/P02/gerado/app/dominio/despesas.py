"""Regras de negócio das despesas. Puro: recebe dados e `agora`, sem FastAPI e sem SQL."""

from calendar import monthrange
from datetime import date, datetime, timedelta

from app.dominio.erros import conflito, nao_encontrado, regra_violada

CATEGORIAS = ("TRANSPORTE", "HOSPEDAGEM", "ALIMENTACAO", "OUTROS")
SITUACOES = ("PENDENTE", "APROVADA", "RECUSADA", "PAGA")

# RN-06: toda despesa nasce PENDENTE.
SITUACAO_INICIAL = "PENDENTE"

# RN-02: limite por despesa, em centavos, inclusive.
LIMITES_CENTAVOS = {"ALIMENTACAO": 12_000, "HOSPEDAGEM": 45_000, "TRANSPORTE": 100_000, "OUTROS": 100_000}

# RN-04: idade máxima da despesa, em dias, inclusive.
DIAS_MAXIMOS = 60

# RN-07: mudanças de situação permitidas.
TRANSICOES = {("PENDENTE", "APROVADA"), ("PENDENTE", "RECUSADA"), ("APROVADA", "PAGA")}

# RN-10: situações que entram no resumo do mês.
SITUACOES_NO_RESUMO = ("APROVADA", "PAGA")


def _reais(centavos: int) -> str:
    texto = f"{centavos / 100:,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def normalizar_email(email: str) -> str:
    # PR-03: o colaborador é o e-mail, sem diferenciar maiúsculas.
    return email.strip().lower()


def validar_valor(categoria: str, valor_centavos: int) -> None:
    # RN-01: valor maior que zero.
    if valor_centavos <= 0:
        raise regra_violada("VALOR_INVALIDO", "O valor da despesa precisa ser maior que zero.")
    # RN-02: limite por categoria, inclusive.
    limite = LIMITES_CENTAVOS[categoria]
    if valor_centavos > limite:
        raise regra_violada(
            "VALOR_ACIMA_DO_LIMITE",
            f"O valor passa do limite de {_reais(limite)} por despesa da categoria {categoria}.",
        )


def validar_data(data: date, agora: datetime) -> None:
    hoje = agora.date()
    # RN-03: data não pode ser futura (hoje é aceito).
    if data > hoje:
        raise regra_violada("DATA_FUTURA", "A data da despesa não pode ser futura.")
    # RN-04: no máximo 60 dias atrás (60 aceito, 61 recusado).
    if data < hoje - timedelta(days=DIAS_MAXIMOS):
        raise regra_violada(
            "DATA_MUITO_ANTIGA", f"A data da despesa não pode ter mais de {DIAS_MAXIMOS} dias."
        )


def verificar_duplicidade(ja_existe: bool) -> None:
    # RN-05: mesmo comprovante, mesmo colaborador, uma vez só.
    if ja_existe:
        raise conflito(
            "COMPROVANTE_DUPLICADO", "Este número de comprovante já foi lançado por este colaborador."
        )


def garantir_existe(despesa) -> None:
    if despesa is None:
        raise nao_encontrado("DESPESA_NAO_ENCONTRADA", "Despesa não encontrada.")


def validar_transicao(atual: str, nova: str) -> None:
    # RN-07: só as mudanças da tabela TRANSICOES.
    if (atual, nova) not in TRANSICOES:
        raise conflito(
            "TRANSICAO_INVALIDA", f"Não é possível mudar a despesa de {atual} para {nova}."
        )


def validar_motivo(motivo: str | None) -> str:
    # RN-08: recusar exige motivo não vazio.
    texto = (motivo or "").strip()
    if not texto:
        raise regra_violada("MOTIVO_OBRIGATORIO", "Informe o motivo da recusa.")
    return texto


def validar_exclusao(situacao: str) -> None:
    # RN-09: só despesa PENDENTE pode ser excluída.
    if situacao != "PENDENTE":
        raise conflito(
            "EXCLUSAO_NAO_PERMITIDA", f"Só despesa PENDENTE pode ser excluída; esta está {situacao}."
        )


def intervalo_do_mes(mes: str) -> tuple[str, str]:
    # RN-10 / PR-08: mês civil, do dia 1 ao último dia, inclusive.
    ano, numero = int(mes[:4]), int(mes[5:7])
    ultimo = monthrange(ano, numero)[1]
    return date(ano, numero, 1).isoformat(), date(ano, numero, ultimo).isoformat()


def montar_resumo(mes: str, somas: dict[str, int]) -> dict:
    # RN-10: as somas já vêm só de APROVADA e PAGA; as 4 categorias sempre aparecem.
    totais = {categoria: int(somas.get(categoria, 0)) for categoria in CATEGORIAS}
    return {"mes": mes, "totais_centavos": totais, "total_geral_centavos": sum(totais.values())}
