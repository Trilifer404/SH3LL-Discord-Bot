from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from .common import ToolError

PASTA_CHROMA = "./chroma_db"
NOME_COLECAO = "wikipedia_subset"
MODELO_EMBEDDING = "nomic-embed-text"

_vectorstore = None


def obter_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING, keep_alive=1800)
        _vectorstore = Chroma(
            collection_name=NOME_COLECAO,
            embedding_function=embeddings,
            persist_directory=PASTA_CHROMA,
        )
    return _vectorstore


def executar(pergunta: str) -> str:
    if not isinstance(pergunta, str) or not pergunta.strip() or len(pergunta.strip()) > 2000:
        raise ToolError("informe uma pergunta com até 2000 caracteres.")

    vectorstore = obter_vectorstore()
    resultados = vectorstore.similarity_search_with_relevance_scores(
        pergunta.strip(), k=3
    )

    relevantes = [(doc, score) for doc, score in resultados if score >= 0.5]

    if not relevantes:
        return "Nenhum trecho relevante encontrado na base de conhecimento."

    trechos = [
        f"[{i}] {doc.page_content}"
        for i, (doc, _) in enumerate(relevantes, start=1)
    ]
    return "\n\n".join(trechos)


SCHEMA = {
    "type": "function",
    "function": {
        "name": "consultar_conhecimento",
        "description": (
            "Consulta a base de conhecimento local do SH3LL. "
            "Contém artigos detalhados sobre história do Brasil, história mundial, filosofia, "
            "química, medicina, substâncias, e a organização política e institucional do Brasil. "
            "OBRIGATÓRIO: use esta ferramenta SEMPRE que a pergunta mencionar "
            "qualquer um desses temas, qualquer pessoa, evento ou conceito histórico. "
            "NUNCA responda sobre esses temas de memória. "
            "Se a informação não estiver na base, a ferramenta avisa, e aí você pode "
            "recorrer a consultar_wikipedia ou buscar_web."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pergunta": {
                    "type": "string",
                    "description": "A pergunta ou tópico a ser consultado na base.",
                },
            },
            "required": ["pergunta"],
        },
    },
}
