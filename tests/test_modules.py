from types import SimpleNamespace

import pytest
import requests

import modules


def test_executor_padroniza_ferramenta_desconhecida():
    assert modules.executar("inexistente", {}) == "[ERRO] inexistente: ferramenta não encontrada."


def test_executor_padroniza_argumentos_que_nao_sao_objeto():
    assert modules.executar("obter_hora", []) == "[ERRO] obter_hora: argumentos devem ser um objeto."


def test_executor_nao_expoe_detalhes_de_falha_interna(monkeypatch):
    def falha():
        raise RuntimeError("detalhe interno")

    monkeypatch.setitem(
        modules.FERRAMENTAS,
        "obter_hora",
        SimpleNamespace(executar=falha),
    )

    resultado = modules.executar("obter_hora", {})

    assert resultado == "[ERRO] obter_hora: falha interna ao executar a ferramenta."
    assert "detalhe interno" not in resultado


@pytest.mark.parametrize(
    ("nome", "argumentos", "mensagem"),
    [
        (
            "consultar_wikipedia",
            {"topico": "Revolução Francesa", "idioma": "pt"},
            "Pesquisa na Wikipédia | tópico='Revolução Francesa'",
        ),
        (
            "buscar_web",
            {"consulta": "notícias recentes no Brasil"},
            "Pesquisa na web | consulta='notícias recentes no Brasil'",
        ),
        (
            "geolocate",
            {"cidade": "São Paulo"},
            "Pesquisa de localização | cidade/localidade='São Paulo'",
        ),
        (
            "consultar_conhecimento",
            {"pergunta": "Causas da Revolução Francesa"},
            "Consulta à base RAG | pergunta='Causas da Revolução Francesa'",
        ),
    ],
)
def test_executor_registra_consulta_especifica_e_resultado_da_ferramenta(
    nome,
    argumentos,
    mensagem,
    monkeypatch,
    caplog,
):
    retorno = "Resultado de teste da ferramenta"
    monkeypatch.setitem(
        vars(modules.FERRAMENTAS[nome]),
        "executar",
        lambda **kwargs: retorno,
    )

    with caplog.at_level("INFO", logger="sh3ll.tools"):
        assert modules.executar(nome, argumentos) == retorno

    assert mensagem in caplog.text
    assert "Resultado" in caplog.text
    assert retorno in caplog.text


def test_executor_trunca_resultados_extensos_nos_logs(monkeypatch, caplog):
    retorno = "R" * (modules.MAX_TAMANHO_RESULTADO_LOG + 100)
    monkeypatch.setitem(
        vars(modules.FERRAMENTAS["buscar_web"]),
        "executar",
        lambda **kwargs: retorno,
    )

    with caplog.at_level("INFO", logger="sh3ll.tools"):
        assert modules.executar("buscar_web", {"consulta": "consulta"}) == retorno

    assert "R" * modules.MAX_TAMANHO_RESULTADO_LOG + "..." in caplog.text
    assert retorno not in caplog.text


def test_executor_registra_conversao_de_moedas_exata(monkeypatch, caplog):
    resultado = "1 USD vale 5.1200 BRL. Portanto, 25.00 USD = 128.00 BRL."
    monkeypatch.setitem(
        vars(modules.FERRAMENTAS["obter_cambio"]),
        "executar",
        lambda **kwargs: resultado,
    )

    with caplog.at_level("INFO", logger="sh3ll.tools"):
        assert modules.executar(
            "obter_cambio",
            {
                "moeda_origem": "USD",
                "moeda_destino": "BRL",
                "valor": 25,
                "data": "2026-10-20",
            },
        ) == resultado

    assert (
        "Conversão de moedas solicitada | valor=25 | origem=USD | "
        "destino=BRL | data=2026-10-20"
    ) in caplog.text
    assert f"Resultado da conversão/cotação | {resultado}" in caplog.text


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [(91, 0), (0, -181), (float("nan"), 0), (True, 0)],
)
def test_clima_rejeita_coordenadas_invalidas(latitude, longitude, monkeypatch):
    monkeypatch.setitem(
        vars(requests),
        "get",
        lambda *args, **kwargs: pytest.fail("não deve fazer chamada externa"),
    )

    resultado = modules.executar(
        "obter_clima",
        {"latitude": latitude, "longitude": longitude},
    )

    assert resultado.startswith("[ERRO] obter_clima:")


def test_geolocate_rejeita_localidade_vazia(monkeypatch):
    monkeypatch.setitem(
        vars(requests),
        "get",
        lambda *args, **kwargs: pytest.fail("não deve fazer chamada externa"),
    )

    assert modules.executar("geolocate", {"cidade": " "}).startswith("[ERRO] geolocate:")


def test_geolocate_retorna_resultado_sem_coordenadas_como_nao_encontrado(monkeypatch):
    monkeypatch.setitem(
        vars(requests),
        "get",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: [],
        ),
    )

    assert modules.executar("geolocate", {"cidade": "Atlantis"}) == (
        "Não encontrei coordenadas para Atlantis."
    )


def test_wikipedia_rejeita_codigo_de_idioma_invalido(monkeypatch):
    monkeypatch.setitem(
        vars(requests),
        "get",
        lambda *args, **kwargs: pytest.fail("não deve fazer chamada externa"),
    )

    resultado = modules.executar(
        "consultar_wikipedia",
        {"topico": "história", "idioma": "pt.example"},
    )

    assert resultado.startswith("[ERRO] consultar_wikipedia:")


@pytest.mark.parametrize(
    "argumentos",
    [
        {"moeda_origem": "US$", "moeda_destino": "BRL"},
        {"moeda_origem": "USD", "moeda_destino": "BRL", "valor": float("inf")},
        {"moeda_origem": "USD", "moeda_destino": "BRL", "data": "20261022"},
        {"moeda_origem": "USD", "moeda_destino": "BRL", "data": "2026-02-30"},
    ],
)
def test_cambio_rejeita_entrada_invalida(argumentos, monkeypatch):
    monkeypatch.setitem(
        vars(requests),
        "get",
        lambda *args, **kwargs: pytest.fail("não deve fazer chamada externa"),
    )

    assert modules.executar("obter_cambio", argumentos).startswith("[ERRO] obter_cambio:")


@pytest.mark.parametrize(
    "argumentos",
    [
        {"consulta": " "},
        {"consulta": "notícias", "max_resultados": 11},
        {"consulta": "notícias", "max_resultados": True},
    ],
)
def test_busca_web_rejeita_entrada_invalida(argumentos):
    assert modules.executar("buscar_web", argumentos).startswith("[ERRO] buscar_web:")


def test_respostas_normais_de_nao_encontrado_nao_sao_erros(monkeypatch):
    monkeypatch.setitem(
        vars(requests),
        "get",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"search": []}},
        ),
    )

    resultado = modules.executar("consultar_wikipedia", {"topico": "sem resultado"})

    assert resultado == "Não encontrei informações sobre 'sem resultado' na Wikipédia."
    assert not resultado.startswith("[ERRO]")
