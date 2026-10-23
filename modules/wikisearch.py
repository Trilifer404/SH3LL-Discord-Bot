import re

import requests

from .common import ToolError


def executar(topico: str, idioma: str = "pt") -> str:
    if not isinstance(topico, str) or not topico.strip() or len(topico.strip()) > 300:
        raise ToolError("informe um tópico com até 300 caracteres.")
    if not isinstance(idioma, str) or not re.fullmatch(r"[a-z]{2,3}", idioma.lower()):
        raise ToolError("o idioma deve ser um código válido de 2 ou 3 letras.")
    topico = topico.strip()
    idioma = idioma.lower()

    url = f"https://{idioma}.wikipedia.org/w/api.php"
    headers = {
        "User-Agent": "SH3LL-Bot/1.0 (LLM Discord Bot; contato: trilifer404@gmail.com)"
    }

    # Etapa 1: buscar o título exato
    params_busca = {
        "action": "query",
        "list": "search",
        "srsearch": topico,
        "format": "json",
        "srlimit": 1,
    }
    try:
        r = requests.get(url, params=params_busca, headers=headers, timeout=10)
        r.raise_for_status()
        dados = r.json()
    except requests.exceptions.RequestException as exc:
        raise ToolError("Wikipédia está indisponível no momento.") from exc

    resultados = (
        dados.get("query", {}).get("search", [])
        if isinstance(dados, dict) and isinstance(dados.get("query"), dict)
        else []
    )
    if not resultados:
        return f"Não encontrei informações sobre '{topico}' na Wikipédia."

    titulo = resultados[0].get("title") if isinstance(resultados[0], dict) else None
    if not isinstance(titulo, str) or not titulo:
        raise ToolError("Wikipédia retornou um resultado inválido.")

    # Etapa 2: obter o resumo do artigo via Action API
    params_resumo = {
        "action": "query",
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "titles": titulo,
        "format": "json",
    }
    try:
        r = requests.get(url, params=params_resumo, headers=headers, timeout=10)
        r.raise_for_status()
        dados = r.json()
    except requests.exceptions.RequestException as exc:
        raise ToolError("não consegui obter o resumo da Wikipédia.") from exc

    paginas = (
        dados.get("query", {}).get("pages", {})
        if isinstance(dados, dict) and isinstance(dados.get("query"), dict)
        else {}
    )
    for page_id, pagina in paginas.items():
        if not isinstance(pagina, dict):
            continue
        extract_raw = pagina.get("extract", "")
        if not isinstance(extract_raw, str):
            continue
        extract = extract_raw.strip()[:1500]
        if extract:
            return f"{titulo}: {extract}"

    raise ToolError(f"encontrei '{titulo}', mas não consegui extrair o resumo.")


SCHEMA = {
    "type": "function",
    "function": {
        "name": "consultar_wikipedia",
        "description": (
            "Consulta a Wikipédia e retorna um resumo factual sobre um tópico. "
            "Use SEMPRE que o usuário perguntar sobre um lugar, pessoa, evento histórico, "
            "conceito, obra, organização ou qualquer assunto enciclopédico consolidado. "
            "É sua fonte primária para fatos estáveis e verificados. "
            "Para informações recentes, eventos em andamento ou dados atualizados, "
            "use buscar_web em vez desta ferramenta. "
            "As duas são complementares: use a Wikipédia para contexto histórico e "
            "a busca web para atualização. Encadeie-as quando o tema exigir profundidade."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topico": {
                    "type": "string",
                    "description": (
                        "O assunto a ser pesquisado, em português. "
                        "Ex.: 'São João del-Rei', 'Revolução Francesa', 'Alan Turing'. "
                        "Formule o tópico de forma direta, sem frases longas."
                    ),
                },
                "idioma": {
                    "type": "string",
                    "description": "Código do idioma da Wikipédia. Padrão: 'pt' (português).",
                },
            },
            "required": ["topico"],
        },
    },
}
