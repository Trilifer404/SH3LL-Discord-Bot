import logging
from .common import ToolError
from . import clima, hora, geolocate, exchanger, wikisearch, websearch, conhecimento

FERRAMENTAS = {
    "obter_clima": clima,
    "obter_hora": hora,
    "geolocate": geolocate,
    "obter_cambio": exchanger,
    "consultar_wikipedia": wikisearch,
    "buscar_web": websearch,
    "consultar_conhecimento": conhecimento,
}
logger = logging.getLogger("sh3ll.tools")

MAX_TAMANHO_RESULTADO_LOG = 500


def log_text(valor: object, limite: int = 160) -> str:
    texto = " ".join(str(valor).split())
    if len(texto) > limite:
        return texto[:limite] + "..."
    return texto


def register_call(nome: str, argumentos: dict) -> None:
    if nome == "consultar_wikipedia":
        logger.info(
            "Pesquisa na Wikipédia | tópico=%r | idioma=%s",
            log_text(argumentos.get("topico", "não informado")),
            argumentos.get("idioma", "pt"),
        )
    elif nome == "buscar_web":
        logger.info(
            "Pesquisa na web | consulta=%r | máximo_resultados=%s",
            log_text(argumentos.get("consulta", "não informada")),
            argumentos.get("max_resultados", 5),
        )
    elif nome == "consultar_conhecimento":
        logger.info(
            "Consulta à base RAG | pergunta=%r",
            log_text(argumentos.get("pergunta", "não informada")),
        )
    elif nome == "geolocate":
        logger.info(
            "Pesquisa de localização | cidade/localidade=%r",
            log_text(argumentos.get("cidade", "não informada")),
        )
    elif nome == "obter_clima":
        logger.info(
            "Consulta de clima | latitude=%s | longitude=%s",
            argumentos.get("latitude", "não informada"),
            argumentos.get("longitude", "não informada"),
        )
    elif nome == "obter_cambio":
        logger.info(
            "Conversão de moedas solicitada | valor=%s | origem=%s | destino=%s | data=%s",
            argumentos.get("valor", 1),
            argumentos.get("moeda_origem", "não informada"),
            argumentos.get("moeda_destino", "não informada"),
            argumentos.get("data", "cotação mais recente"),
        )
    elif nome == "obter_hora":
        logger.info("Consulta de data e hora atual")
    else:
        logger.info("Ferramenta chamada | nome=%s", nome)


def result_registry(nome: str, resultado: str) -> None:
    trecho = log_text(resultado, MAX_TAMANHO_RESULTADO_LOG)
    eventos = {
        "consultar_wikipedia": "Resultado da Wikipédia",
        "buscar_web": "Resultados da pesquisa web",
        "consultar_conhecimento": "Resultado da consulta RAG",
        "geolocate": "Resultado da pesquisa de localização",
        "obter_clima": "Resultado da consulta de clima",
        "obter_cambio": "Resultado da conversão/cotação",
        "obter_hora": "Data e hora retornadas",
    }
    logger.info("%s | %s", eventos.get(nome, f"Resultado da ferramenta {nome}"), trecho)


def schemas() -> list[dict]:
    return [mod.SCHEMA for mod in FERRAMENTAS.values()]


def executar(nome: str, argumentos: object) -> str:
    if nome not in FERRAMENTAS:
        logger.warning(
            "Ferramenta '%s' não registrada. Disponíveis: %s",
            nome, list(FERRAMENTAS.keys()),
        )
        return f"[ERRO] {nome}: ferramenta não encontrada."
    if not isinstance(argumentos, dict):
        logger.warning("Argumentos inválidos para '%s': esperado um objeto.", nome)
        return f"[ERRO] {nome}: argumentos devem ser um objeto."

    register_call(nome, argumentos)
    try:
        resultado = FERRAMENTAS[nome].executar(**argumentos)
    except ToolError as e:
        logger.info("Falha esperada em '%s': %s", nome, e)
        resultado = f"[ERRO] {nome}: {e}"
    except (TypeError, ValueError) as e:
        logger.info("Argumentos inválidos para '%s' | erro=%s", nome, e)
        resultado = f"[ERRO] {nome}: argumentos inválidos."
    except Exception:
        logger.exception("Erro inesperado em '%s'", nome)
        resultado = f"[ERRO] {nome}: falha interna ao executar a ferramenta."

    if not isinstance(resultado, str):
        logger.error("Ferramenta '%s' retornou tipo inesperado: %s", nome, type(resultado).__name__)
        resultado = f"[ERRO] {nome}: resposta inválida da ferramenta."

    result_registry(nome, resultado)

    return resultado
