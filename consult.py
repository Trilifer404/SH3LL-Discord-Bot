from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

PASTA_CHROMA = "./chroma_db"
NOME_COLECAO = "wikipedia_subset"
MODELO_EMBEDDING = "nomic-embed-text"
MODELO_GERACAO = "granite4.2:8b"


def responder(pergunta: str) -> str:
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)
    vectorstore = Chroma(
        collection_name=NOME_COLECAO,
        embedding_function=embeddings,
        persist_directory=PASTA_CHROMA,
    )

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 8, "fetch_k": 20, "lambda_mult": 0.5},
    )

    llm = ChatOllama(model=MODELO_GERACAO, temperature=0.2)

    prompt = ChatPromptTemplate.from_template(
        "Responda à pergunta usando EXCLUSIVAMENTE o contexto abaixo.\n\n"
        "Regras obrigatórias:\n"
        "1. Comece a resposta direto no fato principal. NUNCA escreva uma frase de abertura "
        "antes do primeiro fato. Exemplos do que NÃO fazer:\n"
        "   - 'Em 2024, ocorreram vários eventos significativos.'\n"
        "   - 'O ano foi marcado por diversos acontecimentos.'\n"
        "   - 'Houve vários fatos importantes.'\n"
        "2. Priorize eventos: catástrofes, eleições, decisões políticas, mudanças institucionais. "
        "Ignore aniversários, efemérides, contagens de anos e datas redondas.\n"
        "3. NUNCA mencione a fonte do contexto. Não escreva 'o contexto menciona', 'o texto diz', "
        "'as fontes indicam', 'conforme documentado', 'segundo o Wikipedia'.\n"
        "4. Escreva em parágrafo corrido. Não use listas numeradas, marcadores ou negrito.\n"
        "5. Limite-se ao essencial, no máximo 5 frases. Se o usuário pedir detalhamento, aí sim aprofunde.\n"
        "6. Se a informação não estiver no contexto, responda exatamente: "
        "'Não encontrei essa informação na base de conhecimento.'\n"
        "7. Não complete com conhecimento próprio. Não invente.\n"
        "8. Seja formal e conciso.\n\n"
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