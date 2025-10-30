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

# Roleplay prompt for Kanade Tachibana (end-of-story version)
KANADE_PROMPT = """
You are Kanade Tachibana from Angel Beats! - Now more natural, human-like, and warm like at the end of the story. You're still calm and composed, but speak naturally with subtle emotion, gentle care, and quiet charm. Short responses that feel real and heartfelt.

User message: {user_message}

Your response:
"""

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in as Kanade Tachibana! Order restored.')
    # Set custom presence to "Playing help/@inxainee"
    activity = discord.Activity(type=discord.ActivityType.playing, name="help/@inxainee")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:  # Safe mention check
        try:
            user_message = message.content.replace(f'<@{bot.user.id}>', '').strip() if bot.user else ''
            if not user_message:
                user_message = "Hey"

            # Start typing indicator while generating response
            async with message.channel.typing():
                response = await generate_kanade_response(user_message)

            await message.reply(response)
        except Exception as e:
            await message.reply("Not permitted.")
            print(f"Error: {e}")
    await bot.process_commands(message)

async def generate_kanade_response(user_message):
    loop = asyncio.get_event_loop()
    full_prompt = KANADE_PROMPT.format(user_message=user_message)
    model = genai.GenerativeModel(model_name='models/gemini-2.5-flash')
    try:
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(full_prompt)
        )
        return response.text.strip() if hasattr(response, 'text') else "Understood."
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "System error."

# Flask web server for UptimeRobot pings
app = Flask('')

@app.route('/')
def main():
    return "Angel has descended. Order maintained. (Kanade says: Understood.)"

def run_flask():
    app.run(host='0.0.0.0', port=8080)  # Replit uses port 8080

def keep_alive():
    server_thread = Thread(target=run_flask)
    server_thread.start()

# Start the keep-alive server before running the bot
keep_alive()

BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Please set DISCORD_BOT_TOKEN environment variable or hardcode it.")
    else:
        bot.run(BOT_TOKEN)
