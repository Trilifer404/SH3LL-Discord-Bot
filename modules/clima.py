import math

import requests

from .common import ToolError


def executar(latitude: float, longitude: float) -> str:
    if isinstance(latitude, bool) or isinstance(longitude, bool):
        raise ToolError("latitude e longitude devem ser números.")
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError) as exc:
        raise ToolError("latitude e longitude devem ser números.") from exc

    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ToolError("latitude deve estar entre -90 e 90.")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ToolError("longitude deve estar entre -180 e 180.")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "precipitation", "wind_speed_10m"],
        "timezone": "auto",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        dados = r.json()
    except requests.exceptions.RequestException as exc:
        raise ToolError("serviço de clima indisponível no momento.") from exc
    except ValueError as exc:
        raise ToolError("serviço de clima retornou uma resposta inválida.") from exc

    c = dados.get("current") if isinstance(dados, dict) else None
    if not isinstance(c, dict) or any(
            c.get(campo) is None
            for campo in ("temperature_2m", "precipitation", "wind_speed_10m")
    ):
        raise ToolError("serviço de clima não retornou dados completos.")

    return (
        f"Temperatura: {c['temperature_2m']}°C, "
        f"Precipitação: {c['precipitation']}mm, "
        f"Vento: {c['wind_speed_10m']} km/h"
    )


SCHEMA = {
    "type": "function",
    "function": {
        "name": "obter_clima",
        "description": (
            "Retorna as condições climáticas atuais de uma localização geográfica. "
            "Inclui temperatura, precipitação e velocidade do vento. "
            "Use SEMPRE que o usuário perguntar sobre clima, temperatura, chuva, vento "
            "ou qualquer condição meteorológica de uma cidade ou região. "
            "Requer latitude e longitude. Se você só tem o nome da cidade, "
            "chame primeiro a ferramenta geolocate para obter as coordenadas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Latitude em graus decimais. Ex.: -22.91 para Rio de Janeiro.",
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude em graus decimais. Ex.: -43.20 para Rio de Janeiro.",
                },
            },
            "required": ["latitude", "longitude"],
        },
    },
}
