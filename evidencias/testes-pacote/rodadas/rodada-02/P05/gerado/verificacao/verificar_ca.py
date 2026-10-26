"""Verifica os critérios de aceite contra o servidor real. Rode a partir de gerado/: PY verificacao/verificar_ca.py

O tempo "passa" reiniciando o servidor com APP_AGORA posterior sobre o mesmo banco.
"""

from datetime import datetime

from harness import RAIZ, Verificacao, resumo, servidor

AGORA = "2030-01-07T09:00:00-03:00"      # abertura dos chamados
DUAS_HORAS_DEPOIS = "2030-01-07T11:00:00-03:00"
QUATRO_H_UM_MIN_DEPOIS = "2030-01-07T13:01:00-03:00"
SEIS_DIAS_DEPOIS = "2030-01-13T09:00:00-03:00"
OITO_DIAS_DEPOIS = "2030-01-15T09:00:00-03:00"
DIA = "2030-01-07"


def novo_chamado(api, prioridade, titulo):
    corpo = {
        "titulo": titulo,
        "descricao": "Chamado criado pela verificação dos critérios de aceite.",
        "solicitante_nome": "Ana Souza",
        "solicitante_email": "ana.souza@empresa.example",
        "categoria": "SOFTWARE",
        "prioridade": prioridade,
    }
    resposta = api.post("/api/chamados", json=corpo)
    assert resposta.status_code == 201, resposta.text
    return resposta


def linha_relatorio(api, prioridade):
    resposta = api.get("/api/relatorio", params={"data_inicial": DIA, "data_final": DIA})
    linha = next(item for item in resposta.json()["prioridades"] if item["prioridade"] == prioridade)
    texto = (f"HTTP {resposta.status_code}, {prioridade}: resolvidos={linha['resolvidos']}, "
             f"dentro_do_prazo={linha['dentro_do_prazo']}, percentual={linha['percentual_dentro_do_prazo']}")
    return resposta, linha, texto


def main() -> int:
    v = Verificacao()
    banco = RAIZ / "dados" / "verificacao.db"
    banco.unlink(missing_ok=True)

    with servidor(AGORA, banco) as api:
        r = api.get("/")
        v.registrar("TELA", "Abrir a tela web", "HTTP 200 com HTML", resumo(r),
                    r.status_code == 200 and "<html" in r.text.lower() and "Chamados de suporte" in r.text)

        # CA-01
        r = novo_chamado(api, "ALTA", "CA-01 chamado ALTA")
        c = r.json()
        horas = (datetime.fromisoformat(c["prazo_em"]) - datetime.fromisoformat(c["aberto_em"])).total_seconds() / 3600
        v.registrar("CA-01", "Abrir chamado ALTA", "HTTP 201, situacao=ABERTO, prazo 8h após a abertura",
                    resumo(r, "situacao", "aberto_em", "prazo_em") + f", horas={horas:g}",
                    r.status_code == 201 and c["situacao"] == "ABERTO" and horas == 8)

        # CA-02
        id2 = novo_chamado(api, "MEDIA", "CA-02 assumir sem responsável").json()["id"]
        r = api.post(f"/api/chamados/{id2}/assumir", json={})
        situacao = api.get(f"/api/chamados/{id2}").json()["situacao"]
        v.registrar("CA-02", "Assumir chamado sem informar responsável",
                    "Recusa: HTTP 422 RESPONSAVEL_OBRIGATORIO, continua ABERTO",
                    resumo(r, "erro", "mensagem") + f", situacao={situacao}",
                    r.status_code == 422 and r.json()["erro"] == "RESPONSAVEL_OBRIGATORIO" and situacao == "ABERTO")

        # CA-03
        id3 = novo_chamado(api, "MEDIA", "CA-03 resolver aberto").json()["id"]
        r = api.post(f"/api/chamados/{id3}/resolver", json={"solucao": "Tentativa direta."})
        situacao = api.get(f"/api/chamados/{id3}").json()["situacao"]
        v.registrar("CA-03", "Resolver chamado ABERTO direto", "Recusa: HTTP 409 TRANSICAO_INVALIDA, continua ABERTO",
                    resumo(r, "erro", "mensagem") + f", situacao={situacao}",
                    r.status_code == 409 and r.json()["erro"] == "TRANSICAO_INVALIDA" and situacao == "ABERTO")

        # CA-04
        id4 = novo_chamado(api, "MEDIA", "CA-04 resolver sem solução").json()["id"]
        api.post(f"/api/chamados/{id4}/assumir", json={"responsavel": "Carla Mendes"})
        r = api.post(f"/api/chamados/{id4}/resolver", json={})
        situacao = api.get(f"/api/chamados/{id4}").json()["situacao"]
        v.registrar("CA-04", "Resolver chamado sem informar solução",
                    "Recusa: HTTP 422 SOLUCAO_OBRIGATORIA, continua EM_ATENDIMENTO",
                    resumo(r, "erro", "mensagem") + f", situacao={situacao}",
                    r.status_code == 422 and r.json()["erro"] == "SOLUCAO_OBRIGATORIA" and situacao == "EM_ATENDIMENTO")

        # CA-10
        id10 = novo_chamado(api, "BAIXA", "CA-10 fechar aberto").json()["id"]
        r = api.post(f"/api/chamados/{id10}/fechar")
        situacao = api.get(f"/api/chamados/{id10}").json()["situacao"]
        v.registrar("CA-10", "Fechar chamado ABERTO", "Recusa: HTTP 409 TRANSICAO_INVALIDA, continua ABERTO",
                    resumo(r, "erro", "mensagem") + f", situacao={situacao}",
                    r.status_code == 409 and r.json()["erro"] == "TRANSICAO_INVALIDA" and situacao == "ABERTO")

        # Preparação de CA-05..CA-09: abertos às 09:00.
        id5 = novo_chamado(api, "MEDIA", "CA-05 resolver no prazo").json()["id"]
        id6 = novo_chamado(api, "CRITICA", "CA-06 resolver 4h01 depois").json()["id"]
        id7 = novo_chamado(api, "CRITICA", "CA-07 fila com prazo vencido").json()["id"]
        id8 = novo_chamado(api, "ALTA", "CA-08 reabrir após 6 dias").json()["id"]
        id9 = novo_chamado(api, "ALTA", "CA-09 reabrir após 8 dias").json()["id"]
        for id_ in (id5, id6, id8, id9):
            api.post(f"/api/chamados/{id_}/assumir", json={"responsavel": "Bruno Lima"})
        for id_ in (id8, id9):  # resolvidos às 09:00 do dia 07
            api.post(f"/api/chamados/{id_}/resolver", json={"solucao": "Configuração corrigida."})

    # CA-05: 2 horas depois da abertura (prazo MEDIA = 24h).
    with servidor(DUAS_HORAS_DEPOIS, banco) as api:
        r = api.post(f"/api/chamados/{id5}/resolver", json={"solucao": "Reinstalado."})
        _, linha, texto = linha_relatorio(api, "MEDIA")
        v.registrar("CA-05", "Resolver chamado MEDIA 2h após a abertura (dentro do prazo) e consultar relatório",
                    "Conta como dentro do prazo: MEDIA resolvidos=1, dentro_do_prazo=1, percentual=100.0",
                    resumo(r, "situacao", "resolvido_em") + " | " + texto,
                    r.status_code == 200 and linha["resolvidos"] == 1 and linha["dentro_do_prazo"] == 1
                    and linha["percentual_dentro_do_prazo"] == 100.0)

    # CA-06 e CA-07: 4 horas e 1 minuto depois da abertura.
    with servidor(QUATRO_H_UM_MIN_DEPOIS, banco) as api:
        r = api.post(f"/api/chamados/{id6}/resolver", json={"solucao": "Serviço reiniciado."})
        _, linha, texto = linha_relatorio(api, "CRITICA")
        v.registrar("CA-06", "Resolver chamado CRITICA 4h01 após a abertura e consultar relatório",
                    "Conta como fora do prazo: CRITICA resolvidos=1, dentro_do_prazo=0",
                    resumo(r, "situacao", "resolvido_em") + " | " + texto,
                    r.status_code == 200 and linha["resolvidos"] == 1 and linha["dentro_do_prazo"] == 0)

        r = api.get("/api/fila")
        item = next(i for i in r.json() if i["id"] == id7)
        v.registrar("CA-07", "Consultar a fila com chamado CRITICA de prazo vencido (aberto 4h01 antes)",
                    "Chamado aparece como ATRASADO",
                    f"HTTP {r.status_code}, id={id7}, prazo_em={item['prazo_em']}, indicacao={item['indicacao']}",
                    r.status_code == 200 and item["indicacao"] == "ATRASADO")

    # CA-08: 6 dias depois da resolução.
    with servidor(SEIS_DIAS_DEPOIS, banco) as api:
        r = api.post(f"/api/chamados/{id8}/reabrir")
        v.registrar("CA-08", "Reabrir chamado resolvido há 6 dias", "HTTP 200, situacao=EM_ATENDIMENTO",
                    resumo(r, "situacao", "prazo_em"),
                    r.status_code == 200 and r.json()["situacao"] == "EM_ATENDIMENTO")

    # CA-09: 8 dias depois da resolução.
    with servidor(OITO_DIAS_DEPOIS, banco) as api:
        r = api.post(f"/api/chamados/{id9}/reabrir")
        situacao = api.get(f"/api/chamados/{id9}").json()["situacao"]
        v.registrar("CA-09", "Reabrir chamado resolvido há 8 dias",
                    "Recusa: HTTP 409 PRAZO_REABERTURA_ENCERRADO, continua RESOLVIDO",
                    resumo(r, "erro", "mensagem") + f", situacao={situacao}",
                    r.status_code == 409 and r.json()["erro"] == "PRAZO_REABERTURA_ENCERRADO" and situacao == "RESOLVIDO")

    passou = v.salvar()
    return 0 if passou else 1


if __name__ == "__main__":
    raise SystemExit(main())
