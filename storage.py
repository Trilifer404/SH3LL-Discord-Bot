import json
import sqlite3
from pathlib import Path
from typing import Any

CAMINHO_DB = Path(__file__).parent /"sh3ll.db"



def conectar() -> sqlite3.Connection:
    con = sqlite3.connect(CAMINHO_DB)
    con.row_factory = sqlite3.Row
    return con

def start_db():
    # Função para criar a tabela caso ela não exista.
    with conectar() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                extra TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_id ON historico(user_id)"
        )


def serialize(mensagem: dict[str, Any]) -> tuple[str, str, str | None]:
    role = mensagem["role"]
    content = mensagem.get("content", "") or ""
    extra: dict[str, Any] = {}

    if "tool_calls" in mensagem:
        extra["tool_calls"] = mensagem["tool_calls"]
    if "tool_name" in mensagem:
        extra["tool_name"] = mensagem["tool_name"]

    return role, content, json.dumps(extra) if extra else None

def deserial(linha: sqlite3.Row) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "role": linha["role"],
        "content": linha["content"] or "",
    }
    if linha["extra"]:
        msg.update(json.loads(linha["extra"]))
    return msg

def load_history(user_id: int) -> list[dict[str, Any]]:
    with conectar() as con:
        cursor = con.execute(
            "SELECT role, content, extra FROM historico "
            "WHERE user_id = ? ORDER BY id",
            (user_id,),
        )
        return [deserial(linha) for linha in cursor.fetchall()]

def save_history(user_id: int, mensagens: list[dict[str, Any]]) -> None:
    with conectar() as con:
        con.execute("DELETE FROM historico WHERE user_id = ?", (user_id,))
        for msg in mensagens:
            role, content, extra = serialize(msg)
            con.execute(
                "INSERT INTO historico (user_id, role, content, extra) "
                "Values (?, ?, ?, ?)",
                (user_id, role, content, extra),
            )

def clean_history(user_id: int) -> None:
    with conectar() as con:
        con.execute("DELETE FROM historico WHERE user_id = ?", (user_id,))


def purge_hist_db():
    with conectar() as con:
        cursor = con.execute("DELETE FROM historico")
        return cursor.rowcount
