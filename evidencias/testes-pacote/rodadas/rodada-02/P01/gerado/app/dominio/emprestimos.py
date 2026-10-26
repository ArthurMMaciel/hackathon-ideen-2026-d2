"""Regras de empréstimo e devolução. Módulo puro: recebe dados e `agora`, sem FastAPI e sem SQL."""

from datetime import date, datetime

from app.dominio.erros import conflito, regra_violada

PRAZO_MAXIMO_DIAS = {"NOTEBOOK": 14, "PROJETOR": 3, "HEADSET": 3}  # RN-04
LIMITE_ABERTOS = 2  # RN-06
NOMES_TIPO = {"NOTEBOOK": "notebook", "PROJETOR": "projetor", "HEADSET": "headset"}


def data_hoje(agora: datetime) -> date:
    # RN-03: a retirada é o dia do registro, no fuso padrão (PR-01)
    return agora.date()


def validar_disponivel(situacao: str) -> None:
    # RN-02: só equipamento DISPONIVEL pode ser emprestado
    if situacao != "DISPONIVEL":
        motivo = "está em manutenção" if situacao == "MANUTENCAO" else "já está emprestado"
        raise conflito("EQUIPAMENTO_INDISPONIVEL", f"O equipamento {motivo}; só equipamento disponível pode ser emprestado.")


def validar_prazo(tipo: str, retirada: date, prevista: date) -> None:
    # RN-05: a data prevista não pode ser anterior à retirada (igual é aceita)
    if prevista < retirada:
        raise regra_violada(
            "DATA_PREVISTA_ANTERIOR",
            f"A data prevista de devolução não pode ser anterior à retirada ({retirada.isoformat()}).",
        )
    # RN-04: prazo máximo inclusivo, contado da retirada
    maximo = PRAZO_MAXIMO_DIAS[tipo]
    if (prevista - retirada).days > maximo:
        raise regra_violada(
            "PRAZO_EXCEDIDO",
            f"O prazo máximo para {NOMES_TIPO[tipo]} é de {maximo} dias a partir da retirada.",
        )


def validar_limite_pessoa(abertos_da_pessoa: int) -> None:
    # RN-06: no máximo 2 empréstimos em aberto por e-mail
    if abertos_da_pessoa >= LIMITE_ABERTOS:
        raise conflito(
            "LIMITE_EMPRESTIMOS",
            f"Esta pessoa já tem {LIMITE_ABERTOS} empréstimos em aberto; devolva um antes de pegar outro.",
        )


def validar_devolucao(status: str) -> None:
    # RN-07: só empréstimo ABERTO pode ser devolvido
    if status != "ABERTO":
        raise conflito("EMPRESTIMO_JA_DEVOLVIDO", "Este empréstimo já foi devolvido.")


def situacao_apos_devolucao(defeito: bool) -> str:
    # RN-08: com defeito vai para manutenção; sem defeito volta a ficar disponível
    return "MANUTENCAO" if defeito else "DISPONIVEL"


def dias_atraso(prevista: date, hoje: date) -> int:
    # RN-09: dias inteiros entre a data prevista e hoje (prevista ontem = 1); 0 quando não está atrasado
    return max((hoje - prevista).days, 0)


def normalizar_email(email: str) -> str:
    # RN-06 / PR-04: a pessoa é identificada pelo e-mail, sem diferença de maiúsculas e minúsculas
    return email.strip().lower()
