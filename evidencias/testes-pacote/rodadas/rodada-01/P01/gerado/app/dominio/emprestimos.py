"""Regras de empréstimo, devolução, atraso e relatório. Sem FastAPI e sem SQL."""

from datetime import date, datetime

from app.erros import conflito, regra_violada
from app.relogio import FUSO

# RN-04: prazo máximo em dias corridos, contados da retirada, inclusive
PRAZO_MAXIMO_DIAS = {"NOTEBOOK": 14, "PROJETOR": 3, "HEADSET": 3}
# RN-06: máximo de empréstimos ABERTO por pessoa (e-mail)
MAXIMO_ABERTOS = 2


def hoje(agora: datetime) -> date:
    # RN-03 / PR-01: data civil de America/Sao_Paulo no momento do registro
    return agora.astimezone(FUSO).date()


def normalizar_email(email: str) -> str:
    # PR-04: e-mail identifica a pessoa sem diferenciar maiúsculas
    return email.strip().lower()


def validar_disponivel(situacao: str) -> None:
    # RN-02: só equipamento DISPONIVEL pode ser emprestado
    if situacao != "DISPONIVEL":
        raise conflito(
            "EQUIPAMENTO_INDISPONIVEL",
            f"O equipamento está {situacao} e só equipamento DISPONIVEL pode ser emprestado.",
        )


def validar_prazo(tipo: str, retirada: date, prevista: date) -> None:
    # RN-05: data prevista não pode ser anterior à retirada
    if prevista < retirada:
        raise regra_violada(
            "DATA_PREVISTA_ANTERIOR",
            f"A data prevista de devolução não pode ser anterior à retirada ({retirada.isoformat()}).",
        )
    # RN-04: prazo máximo por tipo, inclusive
    limite = PRAZO_MAXIMO_DIAS[tipo]
    if (prevista - retirada).days > limite:
        raise regra_violada(
            "PRAZO_EXCEDIDO",
            f"O prazo máximo para {tipo} é de {limite} dias a partir da retirada.",
        )


def validar_limite_pessoa(abertos: int) -> None:
    # RN-06: no máximo 2 empréstimos em aberto por e-mail
    if abertos >= MAXIMO_ABERTOS:
        raise regra_violada(
            "LIMITE_EMPRESTIMOS",
            f"Esta pessoa já tem {abertos} empréstimos em aberto; o máximo é {MAXIMO_ABERTOS}.",
        )


def situacao_ao_emprestar() -> str:
    # RN-07: equipamento emprestado passa a EMPRESTADO
    return "EMPRESTADO"


def validar_devolucao(status: str) -> None:
    # RN-10: só empréstimo ABERTO pode ser devolvido
    if status != "ABERTO":
        raise conflito("EMPRESTIMO_JA_DEVOLVIDO", "Este empréstimo já foi devolvido.")


def situacao_apos_devolucao(defeito: bool) -> str:
    # RN-09: com defeito vai para MANUTENCAO, senão volta a DISPONIVEL
    return "MANUTENCAO" if defeito else "DISPONIVEL"


def dias_atraso(prevista: date, dia: date) -> int:
    # RN-11: dias de calendário entre a data prevista e hoje; 0 quando não há atraso
    return max((dia - prevista).days, 0)


def intervalo_do_mes(mes: str) -> tuple[date, date]:
    # RN-12: mês civil [primeiro dia, primeiro dia do mês seguinte)
    ano, numero = int(mes[:4]), int(mes[5:7])
    if not 1 <= ano <= 9998 or not 1 <= numero <= 12:
        raise regra_violada("MES_INVALIDO", "O mês deve estar entre 01 e 12, no formato AAAA-MM.")
    inicio = date(ano, numero, 1)
    fim = date(ano + 1, 1, 1) if numero == 12 else date(ano, numero + 1, 1)
    return inicio, fim
