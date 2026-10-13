import requests


def executar(moeda_origem: str, moeda_destino: str, valor: float = 1.0, data: str | None = None) -> str:
    base = moeda_origem.upper().strip()
    quote = moeda_destino.upper().strip()

    url = f"https://api.frankfurter.dev/v2/rate/{base}/{quote}"
    params = {}
    if data:
        params["date"] = data

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        dados = r.json()
    except requests.exceptions.RequestException as e:
        return f"Erro ao consultar cotação: {e}"

    cotacao_raw = dados.get("rate")
    if cotacao_raw is None:
        return f"Não encontrei cotação para {base} → {quote}."

    try:
        cotacao = float(cotacao_raw)
    except (TypeError, ValueError):
        return f"Cotação inválida para {base} → {quote}."

    data_ref = dados.get("date", "data desconhecida")
    convertido = float(valor) * cotacao

    return (
        f"1 {base} vale {cotacao:.4f} {quote}. "
        f"Portanto, {valor:.2f} {base} = {convertido:.2f} {quote}. "
        f"Data de Referência: {data_ref}."
    )


SCHEMA = {
    "type": "function",
    "function": {
        "name": "obter_cambio",
        "description": (
            "Consulta a cotação entre duas moedas e, opcionalmente, converte um valor. "
            "Use SEMPRE que o usuário perguntar o valor de uma moeda, pedir conversão, "
            "ou mencionar câmbio. "
            "IMPORTANTE: quando o usuário perguntar 'quanto está o dólar', 'qual o valor do euro', "
            "'quanto vale o iene', assuma que ele quer saber quanto vale 1 unidade da moeda "
            "estrangeira em reais. Ou seja, moeda_origem='USD' (ou a estrangeira citada) e "
            "moeda_destino='BRL'. Só inverta se o usuário disser explicitamente "
            "'quantos dólares vale 1 real' ou 'converta reais para dólares'. "
            "Se o usuário não especificar a moeda de origem em uma conversão explícita, assuma 'BRL'. "
            "Se o usuário mencionar uma data específica, informe o campo 'data' em YYYY-MM-DD. "
            "Caso contrário, omita o campo para obter a cotação mais recente. "
            "Códigos de moeda no padrão ISO 4217 (USD, BRL, EUR, GBP, JPY, etc.). "
            "Se o usuário disser o nome por extenso (dólar, real, euro, iene), "
            "converta para o código ISO correspondente antes de chamar."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "moeda_origem": {
                    "type": "string",
                    "description": (
                        "Código ISO 4217 da moeda de origem. "
                        "Para perguntas sobre 'valor do dólar', use a moeda estrangeira (ex.: 'USD'). "
                        "Para conversões explícitas sem origem especificada, use 'BRL'."
                    ),
                },
                "moeda_destino": {
                    "type": "string",
                    "description": "Código ISO 4217 da moeda de destino. Ex.: 'BRL', 'EUR', 'JPY'.",
                },
                "valor": {
                    "type": "number",
                    "description": "Valor a converter. Se o usuário não informar, use 1.",
                },
                "data": {
                    "type": "string",
                    "description": (
                        "Data da cotação no formato YYYY-MM-DD (ex.: '2026-09-10'). "
                        "Só preencha se o usuário mencionar uma data específica. "
                        "Caso contrário, omita este campo."
                    ),
                },
            },
            "required": ["moeda_origem", "moeda_destino"],
        },
    },
}