import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)

from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from llm import get_response, reset_historico, reload_modules
import modules
import os
import discord

logger = logging.getLogger("sh3ll.bot")

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER = 795763724970754119

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

GATILHOS_QUESTIONARIOS = (
    "quem foi", "quem é", "quem eram", "quem são",
    "o que foi", "o que é", "o que eram", "o que são",
    "o que aconteceu", "o que ocorreu",
    "me fala sobre", "me fale sobre", "me explica", "me explique",
    "história de", "história do", "história da",
    "quando foi", "quando aconteceu", "quando ocorreu",
    "onde fica", "onde foi", "onde ocorreu",
    "por que", "porque",
)


def rag_consult(prompt: str) -> bool:
    # Checa se a mensagem é uma pergunta, ou parece.
    p = prompt.lower().strip()
    return any(g in p for g in GATILHOS_QUESTIONARIOS)

def rag_injection(prompt: str) -> str:
    # Consulta o RAG e injeta o contexto no prompt, caso tenha um resultado na consulta RAG.
    try:
        trechos = modules.executar("consultar_conhecimento", {"pergunta": prompt})
    except Exception as e:
        logger.warning("Erro ao consultar base %s", e)
        return prompt

    if not trechos or "Nenhum trecho relevante" in trechos:
        return prompt

    logger.info("Contexto injetado da base | tamanho=%d chars", len(trechos))
    return (
        "Contexto factual para basear sua resposta (não mencione a fonte):\n\n"
        f"{trechos}\n\n"
        f"Pergunta: {prompt}"
    )



def dividir_mensagem(texto: str, limite: int = 2000) -> list[str]:
    if len(texto) <= limite:
        return [texto]

    partes = []
    while len(texto) > limite:
        # Tenta quebrar no último parágrafo antes do limite
        corte = texto.rfind("\n\n", 0, limite)
        if corte == -1:
            # Tenta quebrar na última linha antes do limite
            corte = texto.rfind("\n", 0, limite)
        if corte == -1:
            # Tenta quebrar no último espaço antes do limite
            corte = texto.rfind(" ", 0, limite)
        if corte == -1:
            # Sem espaço ou quebra, corta no limite mesmo
            corte = limite

        partes.append(texto[:corte].rstrip())
        texto = texto[corte:].lstrip()

    if texto:
        partes.append(texto)

    return partes

@client.event
async def on_ready():
    await client.change_presence(
        activity=discord.Streaming(
            name="Modular e preciso.",
            url="https://www.twitch.tv/trilifer"))

    print(r"""
   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
   █  S H 3 L L   ::   ONLINE  █
   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    """)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"   {client.user}  |  {len(client.guilds)} servidor(es)  |  {agora}")
    print()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.guild is None:
        prompt = message.content.strip()
    elif client.user.mentioned_in(message):
        prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
    else:
        return

    if not prompt:
        return


    comando = prompt.lower().strip().split()


    if comando and comando[0] in ("$reset", "reset"):
        if message.author.id != OWNER:
            await message.channel.send("Comando restrito ao proprietário.")
            return
        reset_historico(message.author.id)
        logger.info("Histórico resetado | usuário=%s (%s)", message.author, message.author.id)
        await message.channel.send("Histórico reiniciado.")
        return

    if comando and comando[0] in ("$reload", "reload"):
        if message.author.id != OWNER:
            await message.channel.send("Comando restrito ao proprietário.")
            return
        result = reload_modules()
        await message.channel.send(result)
        return


    if rag_consult(prompt):
        prompt = rag_injection(prompt)


    async with message.channel.typing():
        resposta = get_response(message.author.id, prompt)
        if not resposta or not resposta.strip():
            resposta = "Não consegui gerar uma resposta. Tente novamente."
        for parte in dividir_mensagem(resposta):
            try:
                await message.channel.send(parte)
            except discord.HTTPException as e:
                logger.error("Falha ao enviar parte da resposta: %s", e)
                break



if __name__ == "__main__":
    client.run(TOKEN)