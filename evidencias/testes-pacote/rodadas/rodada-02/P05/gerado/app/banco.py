"""Conexão SQLite, criação das tabelas e carga inicial."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Request

# Um CREATE TABLE IF NOT EXISTS por item, na ordem das chaves estrangeiras.
ESQUEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS chamados (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 1 AND 200),
  descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 2000),
  solicitante_nome TEXT NOT NULL CHECK (length(solicitante_nome) BETWEEN 1 AND 200),
  solicitante_email TEXT NOT NULL CHECK (length(solicitante_email) BETWEEN 3 AND 254),
  categoria TEXT NOT NULL CHECK (categoria IN ('ACESSO', 'HARDWARE', 'SOFTWARE')),
  prioridade TEXT NOT NULL CHECK (prioridade IN ('BAIXA', 'MEDIA', 'ALTA', 'CRITICA')),
  situacao TEXT NOT NULL CHECK (situacao IN ('ABERTO', 'EM_ATENDIMENTO', 'RESOLVIDO', 'FECHADO')),
  aberto_em TEXT NOT NULL,
  prazo_em TEXT NOT NULL,
  responsavel TEXT CHECK (responsavel IS NULL OR length(responsavel) BETWEEN 1 AND 200),
  solucao TEXT CHECK (solucao IS NULL OR length(solucao) BETWEEN 1 AND 2000),
  resolvido_em TEXT
)""",
    "CREATE INDEX IF NOT EXISTS ix_chamados_situacao_prazo ON chamados (situacao, prazo_em)",
    "CREATE INDEX IF NOT EXISTS ix_chamados_resolvido_em ON chamados (resolvido_em)",
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


def carga_inicial(conn: sqlite3.Connection, agora: datetime) -> None:
    """Dados iniciais fictícios. Idempotente: só insere quando a tabela está vazia.

    Datas relativas ("futura", "atrasado", "há 3 dias") são calculadas a partir de `agora`,
    que é o relógio de teste nos testes e APP_AGORA ou a hora real no servidor.
    """
    # Import local: o repositório não depende deste módulo, mas evita ciclo na carga do app.
    from app.dominio.chamados import calcular_prazo
    from app.repositorio import chamados as repo

    if repo.contar(conn) > 0:
        return
    # RF-12, PR-10: 6 chamados fictícios, todas as situações e prioridades, dois atrasados na fila.
    exemplos = [
        ("Sem acesso à pasta compartilhada do financeiro", "Ao abrir a pasta aparece acesso negado.",
         "Ana Souza", "ana.souza@empresa.example", "ACESSO", "CRITICA", "ABERTO", 6, None, None, None),
        ("Notebook não liga após atualização", "A tela fica preta depois da atualização de ontem.",
         "Diego Ramos", "diego.ramos@empresa.example", "HARDWARE", "ALTA", "EM_ATENDIMENTO", 2,
         "Carla Mendes", None, None),
        ("Instalar editor de planilhas", "Preciso do editor de planilhas para o fechamento do mês.",
         "Elisa Prado", "elisa.prado@empresa.example", "SOFTWARE", "BAIXA", "ABERTO", 1, None, None, None),
        ("Impressora do segundo andar travando papel", "A impressora trava o papel em toda impressão frente e verso.",
         "Fabio Nunes", "fabio.nunes@empresa.example", "HARDWARE", "MEDIA", "EM_ATENDIMENTO", 30,
         "Bruno Lima", None, None),
        ("Liberar acesso ao sistema de compras", "Novo integrante da equipe de compras sem acesso.",
         "Gabriela Reis", "gabriela.reis@empresa.example", "ACESSO", "ALTA", "RESOLVIDO", 26,
         "Carla Mendes", "Perfil de compras concedido.", 20),
        ("Erro ao abrir o sistema de ponto", "O sistema de ponto fecha sozinho ao abrir.",
         "Hugo Alves", "hugo.alves@empresa.example", "SOFTWARE", "MEDIA", "FECHADO", 72,
         "Bruno Lima", "Reinstalado o cliente do sistema de ponto.", 46),
    ]
    for (titulo, descricao, nome, email, categoria, prioridade, situacao, horas_atras,
         responsavel, solucao, resolvido_horas_atras) in exemplos:
        aberto_em = agora - timedelta(hours=horas_atras)
        resolvido_em = agora - timedelta(hours=resolvido_horas_atras) if resolvido_horas_atras else None
        repo.inserir(conn, {
            "titulo": titulo, "descricao": descricao, "solicitante_nome": nome, "solicitante_email": email,
            "categoria": categoria, "prioridade": prioridade, "situacao": situacao,
            "aberto_em": aberto_em, "prazo_em": calcular_prazo(prioridade, aberto_em),
            "responsavel": responsavel, "solucao": solucao, "resolvido_em": resolvido_em,
        })


def iniciar(caminho: str, agora: datetime) -> None:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conn = conectar(caminho)
    try:
        with transacao(conn):
            for ddl in ESQUEMA:
                conn.execute(ddl)
            carga_inicial(conn, agora)
    finally:
        conn.close()


def obter_conexao(request: Request):
    """Dependência do FastAPI: uma conexão por requisição."""
    conn = conectar(request.app.state.caminho_db)
    try:
        yield conn
    finally:
        conn.close()
