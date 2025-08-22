import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord import app_commands
import sqlite3
from pathlib import Path
import tempfile
from datetime import datetime

import openai

# === Cargar variables de entorno ===
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERSONA = os.getenv("BOT_PERSONA", "Chonchón")  # Personalidad por defecto

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dave_lore.sqlite3"

openai.api_key = OPENAI_API_KEY

# ====== OpenAI wrapper ======
def generar_respuesta(pregunta: str) -> str:
    """Pide a OpenAI una respuesta con la personalidad del Chonchón (misteriosa + sarcástica)."""
    try:
        system_prompt = (
            f"Eres {PERSONA}, criatura del folklore chileno. "
            "Eres un oráculo oscuro, misterioso y con un leve toque de sarcasmo. "
            "Hablas en español, respondiendo dudas de Dungeons & Dragons con precisión, "
            "y relatas los sucesos como un cronista oculto que susurra verdades entre sombras." 
        )
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": pregunta},
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("Error en generar_respuesta:", e)
        return "El Chonchón guarda silencio entre las sombras... (error al generar respuesta)"

# ====== Bot de Discord ======
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

INVITE_URL = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=277083450689&scope=bot%20applications.commands"

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    print(f"Invita al bot a tu servidor con: {INVITE_URL}")
    try:
        await bot.tree.sync()
        print("Slash commands sincronizados")
    except Exception as e:
        print(f"Error al sincronizar slash commands: {e}")

# ====== Persistencia (SQLite) + LORE KEEPER ======

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                title TEXT,
                start_ts TEXT NOT NULL,
                end_ts TEXT,
                summary_md TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                ts TEXT NOT NULL,
                author_id INTEGER,
                author_name TEXT,
                content TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        con.commit()

# ... (todo el bloque SQLite, funciones y comandos de lore que ya tienes)

# ====== Slash Commands ======

@bot.tree.command(name="pregunta", description="Pregunta de reglas al Chonchón")
@app_commands.describe(pregunta="Tu duda de D&D")
async def slash_pregunta(interaction: discord.Interaction, pregunta: str):
    await interaction.response.defer(thinking=True)
    texto = generar_respuesta(pregunta)
    await interaction.followup.send(f"**El Chonchón responde:** {texto}")

# ... (slash commands de lore_iniciar, lore_nota, lore_listar, lore_cerrar)

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("Falta DISCORD_BOT_TOKEN en el .env")
    if not OPENAI_API_KEY:
        raise RuntimeError("Falta OPENAI_API_KEY en el .env")
    bot.run(TOKEN)
