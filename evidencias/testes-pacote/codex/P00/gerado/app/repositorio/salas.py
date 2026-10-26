import json

LISTAR = "SELECT id,nome,local,capacidade,recursos FROM salas ORDER BY local,nome,id"
OBTER = "SELECT id,nome,local,capacidade,recursos FROM salas WHERE id=?"
INSERIR = "INSERT INTO salas(nome,local,capacidade,recursos) VALUES (?,?,?,?)"
LIVRES = """SELECT s.id,s.nome,s.local,s.capacidade,s.recursos FROM salas s
WHERE (? IS NULL OR s.local=?) AND s.capacidade>=?
AND NOT EXISTS (SELECT 1 FROM reservas r WHERE r.sala_id=s.id AND r.status='ATIVA'
AND r.inicio<? AND ?<r.fim)
ORDER BY s.local,s.nome,s.id"""


def objeto(row):
    return {**dict(row), "recursos": json.loads(row["recursos"])}


def listar(conn):
    return [objeto(row) for row in conn.execute(LISTAR)]


def obter(conn, sala_id):
    row = conn.execute(OBTER, (sala_id,)).fetchone()
    return objeto(row) if row else None


def inserir(conn, dados):
    cursor = conn.execute(INSERIR, (dados.nome, dados.local, dados.capacidade,
                                   json.dumps(dados.recursos)))
    return obter(conn, cursor.lastrowid)


def livres(conn, inicio, fim, local, capacidade_minima):
    from app.relogio import para_banco
    return [objeto(row) for row in conn.execute(
        LIVRES, (local, local, capacidade_minima, para_banco(fim), para_banco(inicio)))]
