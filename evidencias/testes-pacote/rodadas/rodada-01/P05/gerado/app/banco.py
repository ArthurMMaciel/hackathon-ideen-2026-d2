"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import Request

from app import relogio

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS chamados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
  descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 2000),
  solicitante_nome TEXT NOT NULL CHECK (length(solicitante_nome) BETWEEN 1 AND 100),
  solicitante_email TEXT NOT NULL CHECK (length(solicitante_email) BETWEEN 3 AND 200),
  categoria TEXT NOT NULL CHECK (categoria IN ('ACESSO','HARDWARE','SOFTWARE')),
  prioridade TEXT NOT NULL CHECK (prioridade IN ('BAIXA','MEDIA','ALTA','CRITICA')),
  situacao TEXT NOT NULL CHECK (situacao IN ('ABERTO','EM_ATENDIMENTO','RESOLVIDO','FECHADO')),
  aberto_em TEXT NOT NULL,
  prazo TEXT NOT NULL,
  responsavel TEXT,
  solucao TEXT,
  resolvido_em TEXT
)""",
    "CREATE INDEX IF NOT EXISTS ix_chamados_situacao_prazo ON chamados (situacao, prazo)",
]

# RF-12: 6 chamados de exemplo, fictícios. Horas relativas ao momento da carga (PR-09):
# (titulo, descricao, nome, email, categoria, prioridade, situacao, horas_desde_abertura,
#  responsavel, solucao, horas_ate_resolver)
EXEMPLOS = [
    ("Sem acesso à pasta compartilhada do financeiro", "Pasta retorna acesso negado desde ontem.",
     "Ana Exemplo", "ana.exemplo@example.com", "ACESSO", "ALTA", "ABERTO", 2, None, None, None),
    ("Impressora do 2º andar não imprime", "Fila de impressão travada.",
     "Bruno Ficticio", "bruno.ficticio@example.com", "HARDWARE", "BAIXA", "ABERTO", 80, None, None, None),
    ("Erro ao abrir o sistema de folha", "Mensagem de erro ao entrar no sistema.",
     "Diego Modelo", "diego.modelo@example.com", "SOFTWARE", "CRITICA", "EM_ATENDIMENTO", 1,
     "Carla Suporte", None, None),
    ("Instalar leitor de PDF", "Preciso abrir os relatórios em PDF.",
     "Elisa Teste", "elisa.teste@example.com", "SOFTWARE", "MEDIA", "RESOLVIDO", 72,
     "Carla Suporte", "Leitor instalado pela central de software.", 10),
    ("Senha do e-mail bloqueada", "Conta bloqueada após tentativas.",
     "Gabriel Amostra", "gabriel.amostra@example.com", "ACESSO", "CRITICA", "RESOLVIDO", 48,
     "Fabio Suporte", "Conta desbloqueada e senha redefinida pelo usuário.", 5),
    ("Trocar mouse com defeito", "Botão esquerdo falhando.",
     "Helena Demo", "helena.demo@example.com", "HARDWARE", "ALTA", "FECHADO", 120,
     "Fabio Suporte", "Mouse substituído.", 6),
]


def caminho_padrao() -> str:
    return os.environ.get("APP_DB", "dados/app.db")


def conectar(caminho: str) -> sqlite3.Connection:
    # isolation_level=None: sem transação implícita; escritas usam transacao().
    conn = sqlite3.connect(caminho, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transacao(conn: sqlite3.Connection):
    """BEGIN IMMEDIATE trava a escrita: verificar e gravar acontecem sem corrida."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def carga_inicial(conn: sqlite3.Connection) -> None:
    """Dados iniciais fictícios. Idempotente: só insere quando a tabela está vazia."""
    from app.dominio.chamados import calcular_prazo
    from app.repositorio import chamados as repo

    if repo.contar(conn) > 0:
        return
    agora = relogio.agora()
    for (titulo, descricao, nome, email, categoria, prioridade, situacao, horas,
         responsavel, solucao, horas_resolver) in EXEMPLOS:
        aberto_em = agora - timedelta(hours=horas)
        repo.inserir(conn, {
            "titulo": titulo, "descricao": descricao, "solicitante_nome": nome,
            "solicitante_email": email, "categoria": categoria, "prioridade": prioridade,
            "situacao": situacao, "aberto_em": aberto_em, "prazo": calcular_prazo(prioridade, aberto_em),
            "responsavel": responsavel, "solucao": solucao,
            "resolvido_em": aberto_em + timedelta(hours=horas_resolver) if horas_resolver else None,
        })


def iniciar(caminho: str) -> None:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conn = conectar(caminho)
    try:
        with transacao(conn):
            for ddl in ESQUEMA:
                conn.execute(ddl)
            carga_inicial(conn)
    finally:
        conn.close()


def obter_conexao(request: Request):
    """Dependência do FastAPI: uma conexão por requisição."""
    conn = conectar(request.app.state.caminho_db)
    try:
        yield conn
    finally:
        conn.close()
