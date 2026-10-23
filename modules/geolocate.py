import requests

from .common import ToolError


def executar(cidade: str) -> str:
    if not isinstance(cidade, str) or not cidade.strip() or len(cidade.strip()) > 200:
        raise ToolError("informe uma localidade com até 200 caracteres.")
    cidade = cidade.strip()

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": cidade,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    headers = {
        "User-Agent": "SH3LL-Bot/0.4 (contato: trilifer404@gmail.com)"
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.RequestException as exc:
        raise ToolError("serviço de geolocalização indisponível no momento.") from exc

    if not isinstance(data, list):
        raise ToolError("serviço de geolocalização retornou uma resposta inválida.")
    if not data:
        return f"Não encontrei coordenadas para {cidade}."

    local = data[0]
    if not isinstance(local, dict):
        raise ToolError("serviço de geolocalização retornou um resultado inválido.")
    try:
        latitude = float(local["lat"])
        longitude = float(local["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ToolError("serviço de geolocalização retornou coordenadas inválidas.") from exc
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ToolError("serviço de geolocalização retornou coordenadas inválidas.")

    end = local.get("address", {})
    if not isinstance(end, dict):
        end = {}
    nome_cidade = (
            end.get("city")
            or end.get("town")
            or end.get("village")
            or end.get("municipality")
            or cidade
    )
    return (
        f"Cidade: {nome_cidade}, "
        f"Estado: {end.get('state', 'desconhecido')}, "
        f"País: {end.get('country', 'desconhecido')}, "
        f"Latitude: {latitude}, longitude: {longitude}"
    )


SCHEMA = {
    "type": "function",
    "function": {
        "name": "geolocate",
        "description": (
            "Converte o nome de uma cidade, estado ou país em coordenadas geográficas "
            "(latitude e longitude) e dados de localização (estado, país). "
            "Use SEMPRE que o usuário mencionar um lugar e você precisar das coordenadas "
            "para consultar clima, ou quando ele perguntar sobre localização geográfica. "
            "Chame esta ferramenta antes de obter_clima quando só tiver o nome da cidade."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cidade": {
                    "type": "string",
                    "description": (
                        "Nome da cidade, estado ou país. "
                        "Ex.: 'Rio de Janeiro', 'Minas Gerais', 'Portugal'. "
                        "Se o usuário mencionar um estado ou país específico, inclua."
                    ),
                },
            },
            "required": ["cidade"],
        },
    },
}
