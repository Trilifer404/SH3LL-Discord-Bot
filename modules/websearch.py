from ddgs import DDGS

from .common import ToolError


def executar(consulta: str, max_resultados: int = 5) -> str:
    if not isinstance(consulta, str) or not consulta.strip() or len(consulta.strip()) > 500:
        raise ToolError("informe uma consulta com até 500 caracteres.")
    if (
            not isinstance(max_resultados, int)
            or isinstance(max_resultados, bool)
            or not 1 <= max_resultados <= 10
    ):
        raise ToolError("o número de resultados deve ser um inteiro entre 1 e 10.")

    try:
        limite = max_resultados
        resultados = DDGS().text(consulta.strip(), region="br-pt", max_results=limite)

        if not resultados:
            return f"Nenhum resultado encontrado para '{consulta.strip()}'."

        partes = [f"Resultados para '{consulta}'"]
        for i, r in enumerate(resultados, start=1):
            titulo = r.get("title", "Sem Título")
            link = r.get("href", "Sem Link")
            trecho = r.get("body", "")
            partes.append(f"{i}. {titulo}\n URL: {link}\n     {trecho}")

    except Exception as e:
        if isinstance(e, ToolError):
            raise
        raise ToolError("serviço de busca indisponível no momento.") from e

    return "\n\n".join(partes)


SCHEMA = {
    "type": "function",
    "function": {
        "name": "buscar_web",
        "description": (
            "Realiza uma busca na web e retorna os principais resultados com título, URL e trecho. "
            "Use SEMPRE que o usuário perguntar sobre informações atualizadas, eventos recentes, "
            "notícias, produtos, empresas, personalidades contemporâneas, dados estatísticos atuais, "
            "ou qualquer tópico geopolítico volátil (guerras, conflitos, eleições, crises). "
            "OBRIGATÓRIO para perguntas sobre guerras, conflitos, eleições ou crises em andamento — "
            "seu conhecimento de memória pode estar desatualizado. "
            "Nunca afirme que 'não há uma guerra' ou 'não há um conflito' com base em memória. "
            "Para fatos históricos consolidados, use consultar_wikipedia em vez desta ferramenta. "
            "As duas são complementares e podem ser encadeadas."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": (
                        "O termo ou pergunta a ser pesquisada. "
                        "Formule de forma clara e específica, com termos objetivos. "
                        "Ex.: 'prefeito do Rio de Janeiro 2026', 'inflação Brasil 2026', "
                        "'conflito Israel Irã'. Prefira termos objetivos a frases conversacionais longas."
                    ),
                },
                "max_resultados": {
                    "type": "integer",
                    "description": (
                        "Número de resultados a retornar, entre 1 e 10. Padrão: 5. "
                        "Use 8 a 10 para perguntas amplas que exigem múltiplas fontes, "
                        "e 2 a 3 para confirmações pontuais."
                    ),
                },
            },
            "required": ["consulta"],
        },
    },
}
