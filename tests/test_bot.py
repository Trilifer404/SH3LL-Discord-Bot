import pytest
from main import dividir_mensagem


def test_texto_curto():
    assert dividir_mensagem("olá") == ["olá"]


def test_string_vazia():
    assert dividir_mensagem("") == [""]


def test_texto_no_limite_exato():
    texto = "a" * 2000
    assert dividir_mensagem(texto) == [texto]


def test_texto_um_char_a_mais():
    texto = "a" * 2001
    partes = dividir_mensagem(texto)
    assert len(partes) == 2
    assert partes[0] == "a" * 2000
    assert partes[1] == "a"


def test_quebra_no_paragrafo():
    texto = "abc\n\ndef\n\nghi"
    partes = dividir_mensagem(texto, limite=5)
    assert partes == ["abc", "def", "ghi"]


def test_quebra_na_linha():
    texto = "abcdef\nghij"
    partes = dividir_mensagem(texto, limite=6)
    assert partes == ["abcdef", "ghij"]


def test_quebra_no_espaco():
    texto = "abc def ghi"
    partes = dividir_mensagem(texto, limite=6)
    assert partes == ["abc", "def", "ghi"]


def test_sem_quebra_corte_duro():
    texto = "abcdefghijkl"
    partes = dividir_mensagem(texto, limite=5)
    assert partes == ["abcde", "fghij", "kl"]


def test_cada_parte_respeita_limite():
    texto = "palavra " * 500
    limite = 100
    partes = dividir_mensagem(texto, limite=limite)
    for parte in partes:
        assert len(parte) <= limite


def test_nenhum_conteudo_perdido():
    texto = "abcdefghij\nklmnopqrst\nuvwxyz"
    partes = dividir_mensagem(texto, limite=12)
    reunido = "".join(partes).replace("\n", "")
    original = texto.replace("\n", "")
    assert reunido == original


def test_multiplas_partes():
    texto = "x" * 10_000
    partes = dividir_mensagem(texto)
    assert len(partes) == 5
    assert sum(len(p) for p in partes) == 10_000