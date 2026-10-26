def test_api_responde(cliente):
    resposta = cliente.get("/api/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_tela_e_servida(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "<html" in resposta.text.lower()
