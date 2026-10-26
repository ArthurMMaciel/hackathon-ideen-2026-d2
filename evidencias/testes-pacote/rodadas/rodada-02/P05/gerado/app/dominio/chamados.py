"""Regras do chamado: prazo, transições de situação e indicação de atraso. Sem FastAPI e sem SQL."""

from datetime import datetime, timedelta

from app.dominio.erros import conflito, regra_violada

CATEGORIAS = ("ACESSO", "HARDWARE", "SOFTWARE")
PRIORIDADES = ("CRITICA", "ALTA", "MEDIA", "BAIXA")  # ordem do relatório (PR-05)
SITUACOES = ("ABERTO", "EM_ATENDIMENTO", "RESOLVIDO", "FECHADO")

# RN-01: horas corridas de prazo por prioridade.
HORAS_DE_PRAZO = {"CRITICA": 4, "ALTA": 8, "MEDIA": 24, "BAIXA": 72}

# RN-06: janela de reabertura, inclusive.
JANELA_REABERTURA = timedelta(days=7)


def calcular_prazo(prioridade: str, aberto_em: datetime) -> datetime:
    # RN-01 e RN-02: calculado uma vez, na abertura.
    return aberto_em + timedelta(hours=HORAS_DE_PRAZO[prioridade])


def dentro_do_prazo(resolvido_em: datetime, prazo_em: datetime) -> bool:
    # RN-03: resolvido até o prazo, inclusive.
    return resolvido_em <= prazo_em


def indicacao_fila(prazo_em: datetime, agora: datetime) -> str:
    # RN-08: atrasado só depois do instante do prazo.
    return "ATRASADO" if agora > prazo_em else "NO_PRAZO"


def exigir_situacao(chamado: dict, esperada: str, acao: str) -> None:
    # RN-07: só as transições do pedido são aceitas.
    if chamado["situacao"] != esperada:
        raise conflito(
            "TRANSICAO_INVALIDA",
            f"Não é possível {acao} um chamado na situação {chamado['situacao']}; "
            f"a ação só vale para chamados {esperada}.",
        )


def _texto_preenchido(valor: str | None) -> str | None:
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


def assumir(chamado: dict, responsavel: str | None) -> dict:
    exigir_situacao(chamado, "ABERTO", "assumir")
    nome = _texto_preenchido(responsavel)
    if nome is None:
        # RN-04
        raise regra_violada("RESPONSAVEL_OBRIGATORIO", "Informe o nome do responsável para assumir o chamado.")
    return {**chamado, "situacao": "EM_ATENDIMENTO", "responsavel": nome}


def resolver(chamado: dict, solucao: str | None, agora: datetime) -> dict:
    # PR-11: a transição é conferida antes da solução.
    exigir_situacao(chamado, "EM_ATENDIMENTO", "resolver")
    texto = _texto_preenchido(solucao)
    if texto is None:
        # RN-05
        raise regra_violada("SOLUCAO_OBRIGATORIA", "Informe a descrição da solução para resolver o chamado.")
    return {**chamado, "situacao": "RESOLVIDO", "solucao": texto, "resolvido_em": agora}


def fechar(chamado: dict) -> dict:
    exigir_situacao(chamado, "RESOLVIDO", "fechar")
    return {**chamado, "situacao": "FECHADO"}


def reabrir(chamado: dict, agora: datetime) -> dict:
    exigir_situacao(chamado, "RESOLVIDO", "reabrir")
    # RN-06: até 7 dias depois da resolução, inclusive.
    if agora > chamado["resolvido_em"] + JANELA_REABERTURA:
        raise conflito(
            "PRAZO_REABERTURA_ENCERRADO",
            "O chamado só pode ser reaberto até 7 dias depois da resolução.",
        )
    # RN-02 e PR-06: prazo e responsável mantidos; solução e resolução anteriores apagadas.
    return {**chamado, "situacao": "EM_ATENDIMENTO", "solucao": None, "resolvido_em": None}
