import requests

def executar(latitude: float, longitude: float) -> str:
    """Busca clima atual via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "precipitation", "wind_speed_10m"],
        "timezone": "America/Sao_Paulo",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    c = r.json().get("current", {})
    return (
        f"Temperatura: {c.get('temperature_2m')}°C, "
        f"Precipitação: {c.get('precipitation')}mm, "
        f"Vento: {c.get('wind_speed_10m')} km/h"
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