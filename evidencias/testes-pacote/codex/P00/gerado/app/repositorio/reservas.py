from app.relogio import do_banco, para_banco

COLUNAS = "id,sala_id,responsavel_nome,responsavel_email,titulo,participantes,inicio,fim,status"
OBTER = f"SELECT {COLUNAS} FROM reservas WHERE id=?"
LISTAR = f"SELECT {COLUNAS} FROM reservas WHERE (? IS NULL OR sala_id=?) ORDER BY inicio,id"
CONFLITO = """SELECT 1 FROM reservas WHERE sala_id=? AND status='ATIVA'
AND inicio<? AND ?<fim LIMIT 1"""
INSERIR = """INSERT INTO reservas(sala_id,responsavel_nome,responsavel_email,titulo,
participantes,inicio,fim,status) VALUES (?,?,?,?,?,?,?,'ATIVA')"""
CANCELAR = "UPDATE reservas SET status='CANCELADA' WHERE id=?"
INTERVALOS = """SELECT inicio,fim FROM reservas WHERE sala_id=? AND status='ATIVA'
AND inicio<? AND ?<fim"""


def objeto(row):
    return {**dict(row), "inicio": do_banco(row["inicio"]).isoformat(),
            "fim": do_banco(row["fim"]).isoformat()}


def obter(conn, reserva_id):
    row = conn.execute(OBTER, (reserva_id,)).fetchone()
    return objeto(row) if row else None


def listar(conn, sala_id=None, dia=None):
    rows = [objeto(row) for row in conn.execute(LISTAR, (sala_id, sala_id))]
    if dia is not None:
        from datetime import datetime, time, timedelta
        from app.relogio import FUSO
        inicio = datetime.combine(dia, time.min, FUSO)
        fim = inicio + timedelta(days=1)
        rows = [row for row in rows if datetime.fromisoformat(row["inicio"]) < fim
                and datetime.fromisoformat(row["fim"]) > inicio]
    return rows


def tem_conflito(conn, sala_id, inicio, fim):
    return conn.execute(CONFLITO, (sala_id, para_banco(fim), para_banco(inicio))).fetchone() is not None


def inserir(conn, dados):
    cursor = conn.execute(INSERIR, (dados.sala_id, dados.responsavel_nome,
        dados.responsavel_email, dados.titulo, dados.participantes,
        para_banco(dados.inicio), para_banco(dados.fim)))
    return obter(conn, cursor.lastrowid)


def cancelar(conn, reserva_id):
    conn.execute(CANCELAR, (reserva_id,))
    return obter(conn, reserva_id)


def intervalos(conn, sala_id, inicio, fim):
    return [(do_banco(row[0]), do_banco(row[1])) for row in conn.execute(
        INTERVALOS, (sala_id, para_banco(fim), para_banco(inicio)))]
