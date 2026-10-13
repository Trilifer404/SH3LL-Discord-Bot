from ddgs import DDGS

def executar(consulta: str, max_resultados: int = 5) -> str:
    try:
        limite = min(max(max_resultados, 1), 10)
        resultados = DDGS().text(consulta, region="br-pt", max_results=limite)

        if not resultados:
            return f"Nenhum resultado encontrado para '{consulta}'"

        partes = [f"Resultados para '{consulta}'"]
        for i, r  in enumerate(resultados, start=1):
            titulo = r.get("title", "Sem Título")
            link = r.get("href", "Sem Link")
            trecho = r.get("body", "")
            partes.append(f"{i}. {titulo}\n URL: {link}\n     {trecho}")

        return "\n\n".join(partes)

    except Exception as e:
        return f"Erro ao buscar na web: {e}"


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