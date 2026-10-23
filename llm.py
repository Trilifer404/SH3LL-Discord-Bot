from datetime import datetime
from pathlib import Path
import importlib
import json
import logging
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import modules
import storage

storage.start_db()

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_TIMEOUT = (3.0, 180.0)
OLLAMA_MAX_RETRIES = 3
OLLAMA_BACKOFF_FACTOR = 0.5

MAX_HISTORICO = 10
MAX_ITER_TOOL = 4
historico_usuarios = {}

logger = logging.getLogger("sh3ll.llm")

_session = requests.Session()
_retry = Retry(
    total=OLLAMA_MAX_RETRIES,
    connect=OLLAMA_MAX_RETRIES,
    read=OLLAMA_MAX_RETRIES,
    backoff_factor=OLLAMA_BACKOFF_FACTOR,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset({"POST"}),
    raise_on_status=False,
)
_adapter = HTTPAdapter(max_retries=_retry)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)


def load_prompt() -> str:
    caminho = Path(__file__).parent / "prompt.txt"
    return caminho.read_text(encoding="utf-8")


def check_datetime() -> str:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    return "/no_think\n" + load_prompt() + f"\n\nData aproximada no início desta sessão: {agora}. Para a hora exata, use a ferramenta obter_hora."


def get_history(user_id: int, channel_id: int | None = None) -> list:
    hist = storage.load_history(user_id, channel_id)
    if not hist:
        hist = [{"role": "system", "content": check_datetime()}]
    return hist


def limitar_historico(hist: list) -> list:
    if len(hist) > 1 + MAX_HISTORICO * 2:
        return [hist[0]] + hist[-(MAX_HISTORICO * 2):]
    return hist


def reset_historico(user_id: int, channel_id: int | None = None) -> None:
    storage.clean_history(user_id, channel_id)

def reload_modules() -> str:
    try:
        for nome_modulo in list(modules.FERRAMENTAS.keys()):
            modulo = modules.FERRAMENTAS[nome_modulo]
            importlib.reload(modulo)

        importlib.reload(modules)

        return f"Módulos recarregados: {', '.join(list(modules.FERRAMENTAS.keys()))}."
    except Exception as e:
        return f"Erro ao recarregar módulos: {e}"


def request_ollama(payload: dict, *, timeout: tuple[float, float] = OLLAMA_TIMEOUT) -> dict:
    last_error: Exception | None = None

    for tentativa in range(OLLAMA_MAX_RETRIES + 1):
        try:
            resposta = _session.post(OLLAMA_URL, json=payload, timeout=timeout)
            if resposta.status_code == 200:
                dados = resposta.json()
                if not isinstance(dados, dict):
                    raise ValueError("Resposta do Ollama não era um objeto JSON válido.")
                logger.debug(
                    "OLLAMA | eval_count=%s | eval_duration=%s | tokens/s=%.1f",
                    dados.get("eval_count"),
                    dados.get("eval_duration"),
                    dados.get("eval_count", 0) / (dados.get("eval_duration", 1) / 1e9),
                )
                return dados

            last_error = requests.HTTPError(
                f"Ollama respondeu com status HTTP {resposta.status_code}: {resposta.text[:200]}"
            )

            if resposta.status_code not in (429, 500, 502, 503, 504):
                resposta.raise_for_status()

        except (requests.RequestException, ValueError) as exc:
            last_error = exc

        if tentativa < OLLAMA_MAX_RETRIES:
            atraso = OLLAMA_BACKOFF_FACTOR * (2 ** tentativa)
            logger.warning(
                "Tentativa de rede com Ollama falhou (%s/%s). Repetindo em %.1fs.",
                tentativa + 1,
                OLLAMA_MAX_RETRIES + 1,
                atraso,
            )
            time.sleep(atraso)
            continue

        raise last_error if last_error is not None else RuntimeError("Falha desconhecida ao acessar o Ollama.")

    raise RuntimeError("Falha desconhecida ao acessar o Ollama.")


def granite_knock(mensagens: list, first = False) -> dict:
    mensagens_envio = list(mensagens)
    if first:
        mensagens_envio[0] = {
            "role": "system",
            "content": (
                    "[INSTRUÇÃO PRIORITÁRIA]\n"
                    "Esta é a primeira mensagem deste usuário. "
                    "Comece a resposta com a frase exata: 'Olá, eu sou SH3LL.' "
                    "Em seguida, execute o fluxo normal (ferramentas quando necessário).\n\n"
                    + mensagens_envio[0]["content"]
            ),
        }

    payload = {
        "model": OLLAMA_MODEL,
        "messages": mensagens_envio,
        "tools": modules.schemas(),
        "stream": False,
        "keep_alive": "10m",
        "think": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 900,
            "num_ctx": 16384,
            "top_p": 0.9,
            "repeat_penalty": 1.05,
            "num_gpu": 15,
        },
    }

    return request_ollama(payload)


def get_response(user_id: int, channel_id: int | None, prompt: str) -> str:
    hist = get_history(user_id, channel_id)
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
        storage.save_history(user_id, limitar_historico(hist), channel_id)
