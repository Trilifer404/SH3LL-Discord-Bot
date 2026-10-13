from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

PASTA_CHROMA = "./chroma_db"
PASTA_COLECAO = "wikipedia_subset"
MODELO_EMBEDDING = "nomic-embed-text"

_vectorstore = None


def _obter_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)
        _vectorstore = Chroma(
            collection_name=PASTA_COLECAO,
            embedding_function=embeddings,
            persist_directory=PASTA_CHROMA,
        )
    return _vectorstore


def executar(pergunta: str) -> str:
    vectorstore = _obter_vectorstore()
    resultados = vectorstore.similarity_search(pergunta, k=4)

    if not resultados:
        return "Nenhum trecho relevante encontrado na base de conhecimento."

    trechos = []
    for i, doc in enumerate(resultados, start=1):
        trechos.append(f"[{i}] {doc.page_content}")

    return "\n\n".join(trechos)


SCHEMA = {
    "type": "function",
    "function": {
        "name": "consultar_conhecimento",
        "description": (
            "Consulta a base de conhecimento local do SH3LL, que contém artigos "
            "sobre história, filosofia, ciência e cultura. Use SEMPRE que o usuário "
            "perguntar sobre um tema que possa estar nessa base, antes de recorrer à "
            "busca na web. Retorna os trechos mais relevantes para a pergunta."
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