import os
import wikipedia  # Importe a biblioteca wikipedia
from langchain_community.document_loaders import WikipediaLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# --- CORREÇÃO: Definir um User-Agent personalizado para a Wikipédia ---
USER_AGENT = "SH3LL_Discord_Bot/1.0 (https://github.com/seu-usuario/sh3ll)"
wikipedia.set_user_agent(USER_AGENT)
# -------------------------------------------------------------------

# Configurações
PASTA_CHROMA = "./chroma_db"
NOME_COLECAO = "wikipedia_subset"
MODELO_EMBEDDING = "nomic-embed-text"

# Lista de temas para indexar
TEMAS = [
    "Inconfidência Mineira",
    "Tiradentes",
    "Brasil Colônia",
    "Império do Brasil",
    "Era Vargas",
    "Ditadura Militar Brasileira",
    "Idade Média",
    "Renascimento",
    "Revolução Industrial",
    "Primeira Guerra Mundial",
    "Segunda Guerra Mundial",
    "Revolução Francesa",
    "Império Romano",
    "Filosofia estoica",
    "Sêneca",
    "Marco Aurélio",
    "Epicteto",
    "Karl Marx",
    "Física Quântica",
    "Química Orgânica",
    "Inteligência artificial",
]


def indexar():
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)

    vectorstore = Chroma(
        collection_name=NOME_COLECAO,
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
            # O User-Agent já foi definido globalmente acima
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