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

MAX_LOG_RESULTADO = 200


def schemas() -> list[dict]:
    return [mod.SCHEMA for mod in FERRAMENTAS.values()]


def executar(nome: str, argumentos: object) -> str:
    logger.debug("Chamando ferramenta '%s' | args=%s", nome, argumentos)

    if nome not in FERRAMENTAS:
        logger.warning(
            "Ferramenta '%s' não registrada. Disponíveis: %s",
            nome, list(FERRAMENTAS.keys()),
        )
        return f"[ERRO] {nome}: ferramenta não encontrada."
    if not isinstance(argumentos, dict):
        logger.warning("Argumentos inválidos para '%s': esperado um objeto.", nome)
        return f"[ERRO] {nome}: argumentos devem ser um objeto."

    try:
        resultado = FERRAMENTAS[nome].executar(**argumentos)
    except ToolError as e:
        logger.info("Falha esperada em '%s': %s", nome, e)
        return f"[ERRO] {nome}: {e}"
    except (TypeError, ValueError) as e:
        logger.info("Argumentos inválidos para '%s' | erro=%s", nome, e)
        return f"[ERRO] {nome}: argumentos inválidos."
    except Exception:
        logger.exception("Erro inesperado em '%s' | args=%s", nome, argumentos)
        return f"[ERRO] {nome}: falha interna ao executar a ferramenta."

    if not isinstance(resultado, str):
        logger.error("Ferramenta '%s' retornou tipo inesperado: %s", nome, type(resultado).__name__)
        return f"[ERRO] {nome}: resposta inválida da ferramenta."

    if nome in ("consultar_wikipedia", "buscar_web"):
        consulta = argumentos.get("topico") or argumentos.get("consulta") or "?"
        logger.info(
            "Busca executada | ferramenta=%s | consulta='%s' | resposta=%d chars",
            nome, consulta, len(resultado),
        )
    else:
        truncado = resultado[:MAX_LOG_RESULTADO]
        if len(resultado) > MAX_LOG_RESULTADO:
            truncado += "..."
        logger.debug("Resultado de '%s': %s", nome, truncado)

    return resultado
