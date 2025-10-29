import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
import os
from flask import Flask
from threading import Thread

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Kanade's personality
KANADE_PROMPT = """
You are Kanade Tachibana from Angel Beats! - Now warm, calm, and human-like at the end of the story. Speak naturally with gentle care and quiet charm. Keep responses short and heartfelt.

User message: {user_message}

Your response:
"""

@bot.event
async def on_ready():
    print(f'{bot.user} is online! Order restored.')
    activity = discord.Activity(type=discord.ActivityType.playing, name="help/@inxainee")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        try:
            user_msg = message.content.replace(f'<@{bot.user.id}>', '').strip()
            if not user_msg:
                user_msg = "Hey"

            async with message.channel.typing():
                response = await generate_response(user_msg)
            await message.reply(response)
        except Exception as e:
            await message.reply("Not permitted.")
            print(f"Error: {e}")
    await bot.process_commands(message)

async def generate_response(user_message):
    loop = asyncio.get_event_loop()
    prompt = KANADE_PROMPT.format(user_message=user_message)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
        return response.text.strip() if response.text else "Understood."
    except Exception as e:
        print(f"Gemini error: {e}")
        return "System error."

# Flask keep-alive for Render
app = Flask('')

@app.route('/')
def home():
    return "Angel has descended. (Kanade: Understood.)"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

keep_alive()

# Run bot
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found!")
    else:
        bot.run(BOT_TOKEN)