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
    import sqlite3
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