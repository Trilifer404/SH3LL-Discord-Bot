import re
import pytest
import storage
import llm


@pytest.fixture
def db_temporario(tmp_path, monkeypatch):
    caminho = tmp_path / "teste.db"
    monkeypatch.setattr(storage, "CAMINHO_DB", caminho)
    storage.start_db()
    return caminho


def test_check_datetime_inclui_data_atual(db_temporario):
    prompt = llm.check_datetime()
    assert re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", prompt)


def test_get_history_cria_system_para_usuario_novo(db_temporario):
    hist = llm.get_history(1)
    assert len(hist) == 1
    assert hist[0]["role"] == "system"
    assert len(hist[0]["content"]) > 0


def test_get_history_carrega_do_banco(db_temporario):
    storage.save_history(1, [
        {"role": "system", "content": "SH3LL"},
        {"role": "user", "content": "olá"},
    ])
    hist = llm.get_history(1)
    assert len(hist) == 2
    assert hist[1]["content"] == "olá"


def test_reset_historico_apaga(db_temporario):
    storage.save_history(1, [{"role": "user", "content": "olá"}])
    llm.reset_historico(1)
    assert storage.load_history(1) == []


def test_limitar_historico_abaixo_do_limite(db_temporario):
    hist = [
        {"role": "system", "content": "SH3LL"},
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    resultado = llm.limitar_historico(hist)
    assert resultado == hist


def test_limitar_historico_acima_do_limite(db_temporario):
    hist = [{"role": "system", "content": "SH3LL"}]
    for i in range(15):
        hist.append({"role": "user", "content": f"u{i}"})
        hist.append({"role": "assistant", "content": f"a{i}"})
    resultado = llm.limitar_historico(hist)
    assert resultado[0]["role"] == "system"
    assert len(resultado) == 1 + llm.MAX_HISTORICO * 2


def test_limitar_historico_preserva_ultimas_trocas(db_temporario):
    hist = [{"role": "system", "content": "SH3LL"}]
    for i in range(15):
        hist.append({"role": "user", "content": f"u{i}"})
        hist.append({"role": "assistant", "content": f"a{i}"})
    resultado = llm.limitar_historico(hist)
    assert resultado[-1]["content"] == "a14"
