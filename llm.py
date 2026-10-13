from datetime import datetime
from pathlib import Path
import importlib
import requests
import json
import logging
import modules

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "granite4.1:8b"

MAX_HISTORICO = 10
MAX_ITER_TOOL = 6
historico_usuarios = {}

logger = logging.getLogger("sh3ll.llm")


def load_prompt() -> str:
    caminho = Path(__file__).parent / "prompt.txt"
    return caminho.read_text(encoding="utf-8")


def check_datetime() -> str:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    return load_prompt() + f"\n\nData aproximada no início desta sessão: {agora}. Para a hora exata, use a ferramenta obter_hora."


def get_history(user_id: int) -> list:
    if user_id not in historico_usuarios:
        historico_usuarios[user_id] = [
            {"role": "system", "content": check_datetime()}
        ]
    return historico_usuarios[user_id]


def limitar_historico(hist: list) -> list:
    if len(hist) > 1 + MAX_HISTORICO * 2:
        return [hist[0]] + hist[-(MAX_HISTORICO * 2):]
    return hist


def reset_historico(user_id: int) -> None:
    historico_usuarios.pop(user_id, None)

def reload_modules() -> str:
    try:
        for nome_modulo in list(modules.FERRAMENTAS.keys()):
            modulo = modules.FERRAMENTAS[nome_modulo]
            importlib.reload(modulo)

        importlib.reload(modules)

        return f"Módulos recarregados: {', '.join(list(modules.FERRAMENTAS.keys()))}."
    except Exception as e:
        return f"Erro ao recarregar módulos: {e}"


def granite_knock(mensagens: list, first: bool = False) -> dict:
    mensagens_envio = list(mensagens)
    if first:
        mensagens_envio[0] = {
            "role": "system",
            "content": (
                    "[INSTRUÇÃO PRIORITÁRIA PARA ESTA RESPOSTA]\n"
                    "Esta é a primeira mensagem deste usuário. "
                    "Comece a resposta com a frase exata: 'Olá, eu sou SH3LL.' "
                    "Depois responda à pergunta em uma ou duas frases.\n\n"
                    + mensagens_envio[0]["content"]
            ),
        }

    payload = {
        "model": OLLAMA_MODEL,
        "messages": mensagens_envio,
        "tools": modules.schemas(),
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.2,
            "num_predict": 900,
            "num_ctx": 8192,
            "num_gpu": 22,
            "top_p": 0.9,
            "repeat_penalty": 1.05,
        },
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=300)
    r.raise_for_status()
    return r.json()


def get_response(user_id: int, prompt: str) -> str:
    hist = get_history(user_id)
    primeira = len(hist) == 1
    hist.append({"role": "user", "content": prompt})

    try:
        for i in range(MAX_ITER_TOOL):
            try:
                dados = granite_knock(hist, first=(primeira and i == 0))
            except requests.exceptions.Timeout:
                hist.append({"role": "assistant", "content": "Estou com atrasos de processamento interno..."})
                return "A resposta demorou demais. Tente novamente."
            except requests.exceptions.ConnectionError:
                hist.append({"role": "assistant", "content": "Não consegui me conectar ao servidor interno para processar sua solicitação."})
                return "Erro: não consegui conectar ao Ollama."
            except Exception as e:
                hist.append({"role": "assistant", "content": "Não consegui processar a solicitação."})
                return f"Erro inesperado: {e}"

            msg = dados.get("message", {})
            tool_calls = msg.get("tool_calls")

            # Caso 1: o modelo quer chamar uma ferramenta
            if tool_calls:

                hist.append({
                    "role": "assistant",
                    "content": msg.get("content", "") or "",
                    "tool_calls": tool_calls,
                })

                for call in tool_calls:
                    nome = call["function"]["name"]
                    args = call["function"]["arguments"]

                    logger.info("Modelo solicitou ferramenta | nome=%s | args=%s", nome, args)

                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {}

                    resultado = modules.executar(nome, args)
                    hist.append({
                        "role": "tool",
                        "content": str(resultado),
                        "tool_name": nome,
                    })
                continue

            # Caso 2: o modelo respondeu diretamente
            conteudo = (msg.get("content") or "").strip()
            logger.debug("Resposta final gerada (%d chars)", len(conteudo))
            if not conteudo:
                hist.append({"role": "assistant", "content": "Não consegui formular uma resposta."})
                return "Não consegui formular uma resposta. Tente reformular."
            hist.append({"role": "assistant", "content": conteudo})
            return conteudo

        hist.append({"role": "assistant", "content": "Tive de chamar a ferramenta muitas vezes, algo mais simples é necessário."})
        return "A operação exigiu muitas chamadas de ferramenta. Tente algo mais simples."
    finally:
        historico_usuarios[user_id] = limitar_historico(hist)
