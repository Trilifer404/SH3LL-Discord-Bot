from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from indexer import TEMAS as TEMAS_INDEXADOS

PASTA_CHROMA = "./chroma_db"
NOME_COLECAO = "wikipedia_subset"
MODELO_EMBEDDING = "nomic-embed-text"

_vectorstore = None


def _obter_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)
        _vectorstore = Chroma(
            collection_name=NOME_COLECAO,
            embedding_function=embeddings,
            persist_directory=PASTA_CHROMA,
        )
    return _vectorstore


def executar(pergunta: str) -> str:
    try:
        vectorstore = _obter_vectorstore()
        resultados = vectorstore.similarity_search(
            pergunta,
            k=5,
            fetch_k=20,
            lambda_mult=0.5,
        )
    except Exception as e:
        return f"Erro ao consultar base RAG: {e}"


    if not resultados:
        return "Nenhum trecho relevante encontrado na base de conhecimento."

    trechos = [f"[{i}] {doc.page_content}" for i, doc in enumerate(resultados, start=1)]
    return "\n\n".join(trechos)


SCHEMA = {
    "type": "function",
    "function": {
        "name": "consultar_conhecimento",
        "description": (
            "Consulta a base de conhecimento local do SH3LL. "
            "Contém artigos detalhados sobre os seguintes temas: "
            + ", ".join(TEMAS_INDEXADOS) + ". "
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