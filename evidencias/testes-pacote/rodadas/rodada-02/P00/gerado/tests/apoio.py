"""Funções de apoio dos testes: cada teste cria as salas e reservas que confere."""

from datetime import timedelta

from tests.conftest import AGORA_INICIAL, iso

HOJE = AGORA_INICIAL  # 2030-01-07 09:00 -03:00
AMANHA = AGORA_INICIAL + timedelta(days=1)  # 2030-01-08


def criar_sala(cliente, nome="Sala Teste", local="SAO_PAULO", capacidade=8, recursos=None):
    resposta = cliente.post(
        "/api/salas",
        json={"nome": nome, "local": local, "capacidade": capacidade, "recursos": recursos or []},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def dados_reserva(sala_id, inicio, fim, participantes=2, titulo="Reunião de teste"):
    return {
        "sala_id": sala_id,
        "responsavel_nome": "Pessoa Ficticia",
        "responsavel_email": "pessoa@exemplo.com",
        "titulo": titulo,
        "participantes": participantes,
        "inicio": inicio,
        "fim": fim,
    }


def reservar(cliente, sala_id, inicio, fim, participantes=2):
    return cliente.post("/api/reservas", json=dados_reserva(sala_id, inicio, fim, participantes))


def reservar_ok(cliente, sala_id, inicio, fim, participantes=2):
    resposta = reservar(cliente, sala_id, inicio, fim, participantes)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def amanha(hora, minuto=0):
    return iso(AMANHA, hora, minuto)


def hoje(hora, minuto=0):
    return iso(HOJE, hora, minuto)
