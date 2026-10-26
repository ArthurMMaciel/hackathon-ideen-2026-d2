"""Funções de apoio dos testes: criam turmas e inscrições pela API."""

from datetime import timedelta

from tests.conftest import AGORA_INICIAL

# Turma padrão do plano de testes: 3 dias depois do relógio inicial, às 09:00.
INICIO_PADRAO = AGORA_INICIAL + timedelta(days=3)


def criar_turma(cliente, vagas=2, inicio=INICIO_PADRAO, duracao_minutos=60, titulo="Turma de teste",
                modalidade="ONLINE"):
    resposta = cliente.post("/api/turmas", json={
        "titulo": titulo,
        "inicio": inicio.isoformat(),
        "duracao_minutos": duracao_minutos,
        "modalidade": modalidade,
        "vagas": vagas,
    })
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def inscrever(cliente, turma_id, n=1, email=None, nome=None):
    return cliente.post("/api/inscricoes", json={
        "turma_id": turma_id,
        "nome": f"Pessoa {n}" if nome is None else nome,
        "email": f"pessoa{n}@exemplo.test" if email is None else email,
    })


def ir_para(relogio, momento):
    relogio.agora = momento


def presenca(cliente, inscricao_id, situacao):
    return cliente.post(f"/api/inscricoes/{inscricao_id}/presenca", json={"situacao": situacao})


def cancelar(cliente, inscricao_id):
    return cliente.post(f"/api/inscricoes/{inscricao_id}/cancelar")


def inscritos(cliente, turma_id):
    resposta = cliente.get(f"/api/turmas/{turma_id}/inscricoes")
    assert resposta.status_code == 200, resposta.text
    return {i["id"]: i for i in resposta.json()}
