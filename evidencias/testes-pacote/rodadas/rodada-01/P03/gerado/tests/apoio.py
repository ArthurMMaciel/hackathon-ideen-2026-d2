"""Funções de apoio dos testes: criar turma e inscrições pela API."""

from datetime import datetime, timedelta

from app.relogio import FUSO

# Turma padrão dos testes: 3 dias depois de T0 (2030-01-07 09:00).
INICIO_PADRAO = datetime(2030, 1, 10, 9, 0, tzinfo=FUSO)


def criar_turma(cliente, vagas=2, inicio=INICIO_PADRAO, **extra):
    corpo = {
        "titulo": "Excel avançado",
        "inicio": inicio.isoformat(),
        "duracao_minutos": 60,
        "modalidade": "ONLINE",
        "vagas": vagas,
        **extra,
    }
    resposta = cliente.post("/api/turmas", json=corpo)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def inscrever(cliente, turma_id, n, nome=None):
    return cliente.post(
        f"/api/turmas/{turma_id}/inscricoes",
        json={"nome": nome or f"Pessoa {n}", "email": f"pessoa{n}@exemplo.test"},
    )


def ir_para(relogio, momento: datetime):
    relogio.agora = momento


def inicio_mais(minutos: int) -> datetime:
    return INICIO_PADRAO + timedelta(minutes=minutos)
