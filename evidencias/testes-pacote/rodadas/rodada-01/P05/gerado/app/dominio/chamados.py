"""Regras de negócio dos chamados. Funções puras: recebem dados e `agora`, sem HTTP e sem SQL."""

from datetime import datetime, timedelta

from app.erros import regra_violada

PRIORIDADES = ("CRITICA", "ALTA", "MEDIA", "BAIXA")  # ordem de exibição do relatório

# RN-01: prazo de resolução em horas corridas por prioridade.
HORAS_PRAZO = {"CRITICA": 4, "ALTA": 8, "MEDIA": 24, "BAIXA": 72}

# RN-06: janela de reabertura, inclusive.
JANELA_REABERTURA = timedelta(days=7)

# RN-07: únicas transições permitidas, por ação: ação -> (origem, destino).
# A origem é conferida por ação: "assumir" um RESOLVIDO não pode virar uma reabertura sem a regra RN-06.
TRANSICOES = {
    "assumir": ("ABERTO", "EM_ATENDIMENTO"),
    "resolver": ("EM_ATENDIMENTO", "RESOLVIDO"),
    "fechar": ("RESOLVIDO", "FECHADO"),
    "reabrir": ("RESOLVIDO", "EM_ATENDIMENTO"),
}


def calcular_prazo(prioridade: str, aberto_em: datetime) -> datetime:
    # RN-01 / RN-02: calculado só na abertura; nenhuma outra operação recalcula.
    return aberto_em + timedelta(hours=HORAS_PRAZO[prioridade])


def dentro_do_prazo(resolvido_em: datetime | None, prazo: datetime) -> bool | None:
    # RN-03: resolvido até o prazo, inclusive.
    if resolvido_em is None:
        return None
    return resolvido_em <= prazo


def validar_transicao(atual: str, acao: str) -> str:
    """Devolve a situação de destino. RN-07: qualquer mudança fora da tabela é recusada."""
    origem, destino = TRANSICOES[acao]
    if atual != origem:
        raise regra_violada(
            "TRANSICAO_INVALIDA",
            f"Não é permitido {acao} um chamado {atual}: essa ação só vale para chamados {origem}.",
        )
    return destino


def _texto_preenchido(texto: str | None) -> str | None:
    if texto is None:
        return None
    texto = texto.strip()
    return texto or None


def exigir_responsavel(texto: str | None) -> str:
    # RN-04: assumir exige o nome do responsável.
    valor = _texto_preenchido(texto)
    if valor is None:
        raise regra_violada("RESPONSAVEL_OBRIGATORIO", "Informe o nome do responsável para assumir o chamado.")
    return valor


def exigir_solucao(texto: str | None) -> str:
    # RN-05: resolver exige a descrição da solução.
    valor = _texto_preenchido(texto)
    if valor is None:
        raise regra_violada("SOLUCAO_OBRIGATORIA", "Informe a descrição da solução para resolver o chamado.")
    return valor


def verificar_reabertura(resolvido_em: datetime, agora: datetime) -> None:
    # RN-06: reabrir só até 7 dias depois da resolução, inclusive.
    if agora > resolvido_em + JANELA_REABERTURA:
        raise regra_violada(
            "REABERTURA_EXPIRADA",
            "O chamado só pode ser reaberto até 7 dias depois da resolução.",
        )


def indicacao_fila(prazo: datetime, agora: datetime) -> str | None:
    # RN-08: atrasado quando o prazo já passou (no exato prazo ainda não está).
    return "ATRASADO" if agora > prazo else None
