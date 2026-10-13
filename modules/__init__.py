import logging

from . import clima, hora, geolocate, exchanger, wikisearch, websearch

FERRAMENTAS = {
    "obter_clima": clima,
    "obter_hora": hora,
    "geolocate": geolocate,
    "obter_cambio": exchanger,
    "consultar_wikipedia": wikisearch,
    "buscar_web": websearch,
}

logger = logging.getLogger("sh3ll.tools")

MAX_LOG_RESULTADO = 200


def schemas() -> list:
    return [mod.SCHEMA for mod in FERRAMENTAS.values()]


def executar(nome: str, argumentos: dict) -> str:
    logger.debug("Chamando ferramenta '%s' | args=%s", nome, argumentos)

    if nome not in FERRAMENTAS:
        logger.warning(
            "Ferramenta '%s' não registrada. Disponíveis: %s",
            nome, list(FERRAMENTAS.keys()),
        )
        return f"Ferramenta '{nome}' não encontrada."

    try:
        resultado = FERRAMENTAS[nome].executar(**argumentos)
    except TypeError as e:
        logger.error("Erro de argumento em '%s' | args=%s | erro=%s", nome, argumentos, e)
        return f"Argumentos inválidos para '{nome}': {e}"
    except Exception as e:
        logger.exception("Erro inesperado em '%s' | args=%s", nome, argumentos)
        return f"Erro ao executar {nome}: {e}"

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