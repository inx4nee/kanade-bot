import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread
import random

print("1. Script started")  # ← ADD THIS

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

print("2. Bot object created")  # ← ADD THIS

@bot.event
async def on_ready():
    print("3. BOT IS ONLINE – ORDER RESTORED!")  # ← CHANGE THIS
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
                resp = await generate_response(user_msg)
            await message.reply(resp)
        except Exception as e:
            print(f"Message error: {e}")
            await message.reply("Understood.")
    await bot.process_commands(message)

async def generate_response(user_message):
    print(f"Generating response for: {user_message}")  # ← DEBUG
    kanade_lines = [
        "Hey... I'm here.",
        "Understood.",
        "What is it?",
        "Order restored.",
        "I'm listening...",
        "Yes?"
    ]
    return random.choice(kanade_lines)

# Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "Kanade online."

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    print(f"4. Flask starting on port {port}")  # ← DEBUG
    app.run(host='0.0.0.0', port=port)

print("5. Starting Flask thread")  # ← DEBUG
Thread(target=run_flask, daemon=True).start()

print("6. Starting Discord bot...")  # ← DEBUG
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not BOT_TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN missing!")
else:
    print("7. Token found, running bot...")
    bot.run(BOT_TOKEN)
