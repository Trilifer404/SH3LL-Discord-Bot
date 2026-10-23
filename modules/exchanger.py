import math
import re
from datetime import date

import requests

from .common import ToolError


def executar(moeda_origem: str, moeda_destino: str, valor: float = 1.0, data: str | None = None) -> str:
    if not isinstance(moeda_origem, str) or not isinstance(moeda_destino, str):
        raise ToolError("informe códigos de moeda válidos.")
    base = moeda_origem.upper().strip()
    quote = moeda_destino.upper().strip()
    if not re.fullmatch(r"[A-Z]{3}", base) or not re.fullmatch(r"[A-Z]{3}", quote):
        raise ToolError("os códigos de moeda devem ter três letras ISO 4217.")

    if isinstance(valor, bool):
        raise ToolError("o valor a converter deve ser numérico.")
    try:
        valor = float(valor)
    except (TypeError, ValueError) as exc:
        raise ToolError("o valor a converter deve ser numérico.") from exc
    if not math.isfinite(valor) or valor < 0:
        raise ToolError("o valor a converter deve ser um número finito não negativo.")

    if data is not None:
        if not isinstance(data, str):
            raise ToolError("a data deve usar o formato YYYY-MM-DD.")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
            raise ToolError("a data deve usar o formato YYYY-MM-DD.")
        try:
            date.fromisoformat(data)
        except ValueError as exc:
            raise ToolError("a data deve usar o formato YYYY-MM-DD.") from exc

    url = f"https://api.frankfurter.dev/v2/rate/{base}/{quote}"
    params = {}
    if data:
        params["date"] = data

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        dados = r.json()
    except requests.exceptions.RequestException as exc:
        raise ToolError("serviço de câmbio indisponível no momento.") from exc

    if not isinstance(dados, dict):
        raise ToolError("serviço de câmbio retornou uma resposta inválida.")
    cotacao_raw = dados.get("rate")
    if cotacao_raw is None:
        return f"Não encontrei cotação para {base} → {quote}."
    if isinstance(cotacao_raw, bool) or not isinstance(cotacao_raw, (int, float)):
        raise ToolError("serviço de câmbio retornou uma cotação inválida.")
    cotacao: float = float(cotacao_raw)
    if not math.isfinite(cotacao) or cotacao <= 0:
        raise ToolError("serviço de câmbio retornou uma cotação inválida.")

    data_ref_raw = dados.get("date", "")
    if data_ref_raw:
        try:
            ano, mes, dia = data_ref_raw.split("-")
            data_ref = f"{dia}/{mes}/{ano}"
        except ValueError:
            data_ref = data_ref_raw
    else:
        data_ref = "data desconhecida"

    convertido = valor * cotacao

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
