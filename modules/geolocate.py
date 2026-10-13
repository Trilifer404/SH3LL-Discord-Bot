import requests

def executar(cidade: str) -> str:
    url = "https://nominatim.openstreetmap.org/search"
    params= {
        "q": cidade,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    headers = {
        "User-Agent": "SH3LL-Bot/0.4 (contato: trilifer404@gmail.com)"
    }
    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data:
        return f"Não encontrei coordenadas para {cidade}"
    local = data[0]
    end = local.get("address", {})
    return (
        f"Cidade: {end.get('city', cidade)}, "
        f"Estado: {end.get('state', 'desconhecido')}, " 
        f"País: {end.get('country', 'desconhecido')}, "
        f"Latitude: {local['lat']}, longitude: {local['lon']}"

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