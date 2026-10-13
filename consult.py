from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

PASTA_CHROMA = "./chroma_db"
PASTA_COLECAO = "wikipedia_subset"
MODELO_EMBEDDING = "nomic-embed-text"
MODELO_GERACAO = "granite4.1:8b"


def responder(pergunta: str) -> str:
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)
    vectorstore = Chroma(
        collection_name=PASTA_COLECAO,
        embedding_function=embeddings,
        persist_directory=PASTA_CHROMA,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatOllama(model=MODELO_GERACAO, temperature=0.2)

    prompt = ChatPromptTemplate.from_template(
        "Responda à pergunta com base apenas no contexto abaixo. "
        "Se a resposta não estiver no contexto, diga que não encontrou. "
        "Seja formal e conciso.\n\n"
        "Contexto:\n{context}\n\n"
        "Pergunta: {question}"
    )

    cadeia = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return cadeia.invoke(pergunta)


if __name__ == "__main__":
    while True:
        pergunta = input("\nPergunta: ").strip()
        if not pergunta:
            break
        print(responder(pergunta))