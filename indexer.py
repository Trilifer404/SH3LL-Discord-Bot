import os
import wikipedia  # Importe a biblioteca wikipedia
from langchain_community.document_loaders import WikipediaLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# --- CORREÇÃO: Definir um User-Agent personalizado para a Wikipédia ---
USER_AGENT = "SH3LL_Discord_Bot/1.0 (https://github.com/Trilifer404/sh3lldiscordbot/)"
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
    "2023 no Brasil",
    "2024 no Brasil",
    "2025 no Brasil",
    "2026 no Brasil"
]



def obter_vectorstore() -> Chroma:
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)
    return Chroma(
        collection_name=NOME_COLECAO,
        embedding_function=embeddings,
        persist_directory=PASTA_CHROMA,
    )

def alr_index(vectorstore: Chroma, tema: str) -> bool:
    """Verifica se já existe pelo menos um pedaço com esse tema nos metadados."""
    resultado = vectorstore.get(where={"tema": tema}, limit=1)
    return len(resultado["ids"]) > 0


def remover_tema(vectorstore: Chroma, tema: str) -> int:
    """Remove todos os pedaços de um tema. Retorna quantos foram removidos."""
    resultado = vectorstore.get(where={"tema": tema})
    ids = resultado["ids"]
    if ids:
        vectorstore.delete(ids=ids)
    return len(ids)

def indexar():
    vectorstore = obter_vectorstore()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    adicionados = 0
    pulados = 0

    for tema in TEMAS:
        if alr_index(vectorstore, tema):
            print(f"Pulado (já indexado): {tema}")
            pulados += 1
            continue

        try:
            documentos = WikipediaLoader(
                query=tema,
                lang="pt",
                load_max_docs=1,
            ).load()
        except Exception as e:
            print(f"Erro ao carregar '{tema}': {e}")
            continue

        if not documentos:
            print(f"Sem conteúdo retornado para '{tema}'. Pulando.")
            continue

        pedacos = splitter.split_documents(documentos)
        for pedaco in pedacos:
            pedaco.metadata["tema"] = tema

        vectorstore.add_documents(pedacos)
        adicionados += 1
        print(f"Indexado: {tema} ({len(pedacos)} pedaços)")

    print(f"\nResumo:")
    print(f"  Temas adicionados: {adicionados}")
    print(f"  Temas pulados:     {pulados}")
    print(f"  Total na base:     {vectorstore._collection.count()}")
    print(f"\nBase salva em: {os.path.abspath(PASTA_CHROMA)}")


if __name__ == "__main__":
    indexar()