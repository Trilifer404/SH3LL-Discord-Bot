from datetime import datetime

def executar() -> str:
    """Retorna a data e hora atual no fuso local."""
    return datetime.now().strftime("%d/%m/%Y %H:%M")

SCHEMA = {
    "type": "function",
    "function": {
        "name": "obter_hora",
        "description": (
            "Retorna a data e a hora exatas do sistema neste momento. "
            "Use SEMPRE que o usuário perguntar que horas são, que dia é hoje, "
            "a data atual, ou qualquer variação sobre hora e data presentes. "
            "Não requer parâmetros."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}