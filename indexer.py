import os
from langchain_community.document_loaders import WikipediaLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# Configurações
PASTA_CHROMA = "./chroma_db"
PASTA_COLECAO = "wikipedia_subset"
MODELO_EMBEDDING = "nomic-embed-text"

# Temas dominados pelo SH3LL.
TEMAS = [
    "Inconfidência Mineira",
    "Tiradentes",
    "História do Brasil",
    "Filosofia",
    "Inteligência artificial",
    "Revolução Francesa",
]


def indexar():
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)

    # Cria ou recupera a coleção persistente
    vectorstore = Chroma(
        collection_name=PASTA_COLECAO,
        embedding_function=embeddings,
        persist_directory=PASTA_CHROMA,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    total = 0
    for tema in TEMAS:
        try:
            documentos = WikipediaLoader(
                query=tema,
                lang="pt",
                load_max_docs=1,
            ).load()
        except Exception as e:
            print(f"Erro ao carregar '{tema}': {e}")
            continue

        pedacos = splitter.split_documents(documentos)
        vectorstore.add_documents(pedacos)
        total += len(pedacos)
        print(f"Indexado: {tema} ({len(pedacos)} pedaços)")

    print(f"\nTotal de pedaços indexados: {total}")
    print(f"Base salva em: {os.path.abspath(PASTA_CHROMA)}")


if __name__ == "__main__":
    indexar()