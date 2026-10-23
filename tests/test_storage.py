import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
import storage


@pytest.fixture
def db_temporario(tmp_path, monkeypatch):
    """Cria um banco isolado para cada teste."""
    caminho = tmp_path / "teste.db"
    monkeypatch.setattr(storage, "CAMINHO_DB", caminho)
    storage.start_db()
    return caminho


def test_iniciar_db_cria_tabela(db_temporario):
    con = sqlite3.connect(db_temporario)
    cursor = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='historico'"
    )
    assert cursor.fetchone() is not None


def test_salvar_e_carregar_roundtrip(db_temporario):
    mensagens = [
        {"role": "system", "content": "Você é SH3LL."},
        {"role": "user", "content": "olá"},
        {"role": "assistant", "content": "Olá. Tudo em ordem."},
    ]
    storage.save_history(1, mensagens)
    carregado = storage.load_history(1)
    assert carregado == mensagens


def test_salvar_substitui_historico(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "primeira"}])
    storage.save_history(1, [{"role": "user", "content": "segunda"}])
    carregado = storage.load_history(1)
    assert len(carregado) == 1
    assert carregado[0]["content"] == "segunda"


def test_historico_vazio_para_usuario_novo(db_temporario):
    assert storage.load_history(999) == []


def test_usuarios_isolados(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "user 1"}])
    storage.save_history(2, [{"role": "user", "content": "user 2"}])
    assert storage.load_history(1)[0]["content"] == "user 1"
    assert storage.load_history(2)[0]["content"] == "user 2"


def test_limpar_historico_de_um_usuario(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "user 1"}])
    storage.save_history(2, [{"role": "user", "content": "user 2"}])
    storage.clean_history(1)
    assert storage.load_history(1) == []
    assert storage.load_history(2) != []


def test_limpar_todos_historicos(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "user 1"}])
    storage.save_history(2, [{"role": "user", "content": "user 2"}])
    total = storage.purge_hist_db()
    assert total == 2
    assert storage.load_history(1) == []
    assert storage.load_history(2) == []


def test_preserva_tool_calls(db_temporario):
    mensagens = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"function": {"name": "obter_hora", "arguments": {}}}
            ],
        },
        {
            "role": "tool",
            "content": "14:30",
            "tool_name": "obter_hora",
        },
    ]
    storage.save_history(1, mensagens)
    carregado = storage.load_history(1)
    assert carregado[0]["tool_calls"][0]["function"]["name"] == "obter_hora"
    assert carregado[1]["tool_name"] == "obter_hora"


def test_content_vazio_vira_string_vazia(db_temporario):
    storage.save_history(1, [{"role": "assistant", "content": ""}])
    carregado = storage.load_history(1)
    assert carregado[0]["content"] == ""


def test_historicos_de_usuarios_no_mesmo_canal_sao_isolados(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "usuário 1"}], channel_id=50)
    storage.save_history(2, [{"role": "user", "content": "usuário 2"}], channel_id=50)

    assert storage.load_history(1, 50)[0]["content"] == "usuário 1"
    assert storage.load_history(2, 50)[0]["content"] == "usuário 2"


def test_salvar_historico_nao_substitui_outro_usuario_no_canal(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "manter"}], channel_id=50)
    storage.save_history(2, [{"role": "user", "content": "substituir"}], channel_id=50)
    storage.save_history(2, [{"role": "user", "content": "novo"}], channel_id=50)

    assert storage.load_history(1, 50)[0]["content"] == "manter"
    assert storage.load_history(2, 50)[0]["content"] == "novo"


def test_limpar_historico_no_canal_afeta_somente_o_usuario(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "manter"}], channel_id=50)
    storage.save_history(2, [{"role": "user", "content": "limpar"}], channel_id=50)

    storage.clean_history(2, 50)

    assert storage.load_history(1, 50)[0]["content"] == "manter"
    assert storage.load_history(2, 50) == []


def test_timestamp_e_salvo_em_utc_iso8601(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "olá"}])
    with sqlite3.connect(db_temporario) as con:
        timestamp = con.execute("SELECT timestamp FROM historico").fetchone()[0]

    parsed = datetime.fromisoformat(timestamp)
    assert parsed.utcoffset() == timedelta(0)


def test_purge_old_history_remove_apenas_registros_antigos(db_temporario):
    recente = datetime.now(timezone.utc).isoformat(timespec="seconds")
    antiga = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(timespec="seconds")
    with sqlite3.connect(db_temporario) as con:
        con.executemany(
            """
            INSERT INTO historico (user_id, role, content, timestamp)
            VALUES (?, 'user', ?, ?)
            """,
            [(1, "antiga", antiga), (1, "recente", recente)],
        )

    assert storage.purge_old_history(days=90) == 1
    historico = storage.load_history(1)
    assert [mensagem["content"] for mensagem in historico] == ["recente"]


def test_purge_old_history_rejeita_prazo_invalido(db_temporario):
    with pytest.raises(ValueError, match="inteiro maior ou igual a 1"):
        storage.purge_old_history(days=0)


def test_start_db_migra_timestamp_legado_para_utc(db_temporario):
    with sqlite3.connect(db_temporario) as con:
        con.execute(
            """
            INSERT INTO historico (user_id, role, content, timestamp)
            VALUES (1, 'user', 'legado', '01/01/2020 12:30:45')
            """
        )

    storage.start_db()

    with sqlite3.connect(db_temporario) as con:
        timestamp = con.execute("SELECT timestamp FROM historico").fetchone()[0]
    assert datetime.fromisoformat(timestamp).utcoffset() == timedelta(0)


def test_json_corrompido_e_reportado(db_temporario, caplog):
    with sqlite3.connect(db_temporario) as con:
        con.execute(
            """
            INSERT INTO historico (user_id, role, content, extra)
            VALUES (1, 'assistant', 'resposta', '{inválido')
            """
        )

    with pytest.raises(ValueError, match="Metadados inválidos"):
        storage.load_history(1)

    assert "Metadados JSON inválidos" in caplog.text