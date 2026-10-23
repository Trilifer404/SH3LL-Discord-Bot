import logging

from logging_config import Sh3llFormatter, configure_logging


def test_formatter_exibe_hora_nivel_componente_e_mensagem():
    record = logging.LogRecord(
        "sh3ll.llm",
        logging.INFO,
        "llm.py",
        10,
        "Resposta gerada",
        (),
        None,
    )

    linha = Sh3llFormatter().format(record)

    assert "INFO" in linha
    assert "LLM" in linha
    assert "Resposta gerada" in linha
    assert "\033[" not in linha


def test_configuracao_usa_info_por_padrao(monkeypatch):
    monkeypatch.delenv("SH3LL_LOG_LEVEL", raising=False)

    configure_logging()

    assert logging.getLogger().level == logging.INFO


def test_configuracao_avisa_se_nivel_for_invalido(monkeypatch, capsys):
    monkeypatch.setenv("SH3LL_LOG_LEVEL", "NOT_A_LEVEL")

    configure_logging()

    assert logging.getLogger().level == logging.INFO
    assert "NOT_A_LEVEL" in capsys.readouterr().err
