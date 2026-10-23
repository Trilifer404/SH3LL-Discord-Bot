import json
import logging
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CAMINHO_DB = Path(__file__).parent / "sh3ll.db"
SQLITE_TIMEOUT_SECONDS = 15
logger = logging.getLogger("sh3ll.storage")


def conectar() -> sqlite3.Connection:
    con = sqlite3.connect(CAMINHO_DB, timeout=SQLITE_TIMEOUT_SECONDS)
    con.row_factory = sqlite3.Row
    con.execute(f"PRAGMA busy_timeout = {SQLITE_TIMEOUT_SECONDS * 1000}")
    return con


def _migrar_timestamps_legados(con: sqlite3.Connection) -> None:
    linhas = con.execute(
        """
        SELECT id, timestamp FROM historico
        WHERE timestamp IS NOT NULL AND timestamp NOT GLOB '????-??-??T*'
        """
    ).fetchall()
    for linha in linhas:
        valor = linha["timestamp"]
        try:
            datetime.fromisoformat(valor)
            continue
        except (TypeError, ValueError):
            pass

        try:
            local = datetime.strptime(valor, "%d/%m/%Y %H:%M:%S").astimezone()
            utc = local.astimezone(timezone.utc).isoformat(timespec="seconds")
        except (TypeError, ValueError):
            logger.warning(
                "Timestamp legado inválido mantido sem alteração | registro=%s | valor=%r",
                linha["id"],
                valor,
            )
            continue
        con.execute("UPDATE historico SET timestamp = ? WHERE id = ?", (utc, linha["id"]))


def start_db() -> None:
    with closing(conectar()) as con, con:
        con.execute("PRAGMA journal_mode = WAL")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER,
                role TEXT NOT NULL,
                content TEXT,
                extra TEXT,
                timestamp TEXT
            )
            """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_historico_user_channel_id "
            "ON historico(user_id, channel_id, id)"
        )
        _migrar_timestamps_legados(con)


def serialize(mensagem: dict[str, Any]) -> tuple[str, str, str | None]:
    role = mensagem["role"]
    content = mensagem.get("content", "") or ""
    extra: dict[str, Any] = {}

    if "tool_calls" in mensagem:
        extra["tool_calls"] = mensagem["tool_calls"]
    if "tool_name" in mensagem:
        extra["tool_name"] = mensagem["tool_name"]

    return role, content, json.dumps(extra, ensure_ascii=False) if extra else None


def deserial(linha: sqlite3.Row) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "role": linha["role"],
        "content": linha["content"] or "",
    }
    if linha["extra"]:
        try:
            extra = json.loads(linha["extra"])
            if not isinstance(extra, dict):
                raise ValueError("O campo extra deve conter um objeto JSON.")
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.exception("Metadados JSON inválidos no histórico | registro=%s", linha["id"])
            raise ValueError(
                f"Metadados inválidos no registro de histórico {linha['id']}."
            ) from exc
        msg.update(extra)
    return msg


def load_history(user_id: int, channel_id: int | None = None) -> list[dict[str, Any]]:
    if channel_id is None:
        query = (
            "SELECT id, role, content, extra FROM historico "
            "WHERE user_id = ? AND channel_id IS NULL ORDER BY id"
        )
        params = (user_id,)
    else:
        query = (
            "SELECT id, role, content, extra FROM historico "
            "WHERE user_id = ? AND channel_id = ? ORDER BY id"
        )
        params = (user_id, channel_id)

    with closing(conectar()) as con, con:
        return [deserial(linha) for linha in con.execute(query, params).fetchall()]


def save_history(
    user_id: int,
    mensagens: list[dict[str, Any]],
    channel_id: int | None = None,
) -> None:
    timestamp_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with closing(conectar()) as con, con:
        if channel_id is None:
            con.execute(
                "DELETE FROM historico WHERE user_id = ? AND channel_id IS NULL",
                (user_id,),
            )
        else:
            con.execute(
                "DELETE FROM historico WHERE user_id = ? AND channel_id = ?",
                (user_id, channel_id),
            )

        con.executemany(
            """
            INSERT INTO historico
                (user_id, channel_id, role, content, extra, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (user_id, channel_id, *serialize(mensagem), timestamp_utc)
                for mensagem in mensagens
            ],
        )


def clean_history(user_id: int, channel_id: int | None = None) -> None:
    with closing(conectar()) as con, con:
        if channel_id is None:
            con.execute(
                "DELETE FROM historico WHERE user_id = ? AND channel_id IS NULL",
                (user_id,),
            )
        else:
            con.execute(
                "DELETE FROM historico WHERE user_id = ? AND channel_id = ?",
                (user_id, channel_id),
            )


def purge_old_history(days: int = 90) -> int:
    if not isinstance(days, int) or isinstance(days, bool) or days < 1:
        raise ValueError("days deve ser um inteiro maior ou igual a 1.")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(
        timespec="seconds"
    )
    with closing(conectar()) as con, con:
        cursor = con.execute(
            "DELETE FROM historico WHERE timestamp IS NOT NULL AND timestamp < ?",
            (cutoff,),
        )
        return cursor.rowcount


def purge_hist_db() -> int:
    with closing(conectar()) as con, con:
        cursor = con.execute("DELETE FROM historico")
        return cursor.rowcount
