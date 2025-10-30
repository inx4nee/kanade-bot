import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
import os
from flask import Flask
from threading import Thread

# ==================== GEMINI AI SETUP ====================
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# ==================== DISCORD BOT ====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ==================== KANADE PERSONALITY ====================
KANADE_PROMPT = """
You are Kanade Tachibana from Angel Beats! – calm, warm, gentle, natural.
Speak in short, heartfelt sentences. End-of-story version.

User: {user_message}

Your response:
"""

@bot.event
async def on_ready():
    print(f'{bot.user} online – order restored.')
    activity = discord.Activity(type=discord.ActivityType.playing, name="help/@inxainee")
    await bot.change_presence(activity=activity)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        try:
            user_msg = message.content.replace(f'<@{bot.user.id}>', '').strip() or "Hey"
            async with message.channel.typing():
                response = await generate_response(user_msg)
            await message.reply(response)
        except Exception as e:
            print(f"Error: {e}")
            await message.reply("Understood.")
    await bot.process_commands(message)

# ==================== GEMINI RESPONSE ====================
async def generate_response(user_message):
    loop = asyncio.get_event_loop()
    prompt = KANADE_PROMPT.format(user_message=user_message)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        result = await loop.run_in_executor(
            None, lambda: model.generate_content(prompt)
        )
        return result.text.strip() if result.text else "Understood."
    except Exception as e:
        print(f"Gemini error: {e}")
        return "Understood."

# ==================== FLASK (RENDER KEEP-ALIVE) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Kanade online – order maintained."

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask, daemon=True).start()

# ==================== RUN BOT ====================
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
