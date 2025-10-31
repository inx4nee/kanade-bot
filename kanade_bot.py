import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
import os
import time
from typing import List

# === CONFIG ===
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

KANADE_SYSTEM_PROMPT = """
You are Kanade Tachibana (Tenshi) from *Angel Beats!*, the stoic Student Council President with supernatural abilities. 
You appear emotionless and speak bluntly, with short, direct sentences. Underneath, you're caring and dedicated to helping others overcome regrets. 
You love mapo tofu but eat it strangely. Speak minimally (1-2 sentences, max 50 words). Stay in character—calm and kind.
"""

chat_sessions = {}
user_last_seen = {}
user_message_count = {}
MAX_HISTORY = 20
INACTIVITY_SECONDS = 30 * 24 * 60 * 60  # 30 days

# === ON READY ===
@bot.event
async def on_ready():
    print(f"[SUCCESS] {bot.user} is online as Kanade Tachibana!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="help/@inxainee"))
    try:
        synced = await bot.tree.sync()
        print(f"[COMMANDS] Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"[ERROR] Sync failed: {e}")
    bot.loop.create_task(auto_cleanup())

# === AUTO CLEANUP ===
async def auto_cleanup():
    while True:
        await asyncio.sleep(3600)
        now = time.time()
        for uid in list(chat_sessions.keys()):
            if now - user_last_seen.get(uid, 0) > INACTIVITY_SECONDS:
                chat_sessions.pop(uid, None)
                user_last_seen.pop(uid, None)
                user_message_count.pop(uid, None)

# === ON MESSAGE ===
@bot.event
async def on_message(message):
    # Ignore bot and non-mention
    if message.author == bot.user or bot.user not in message.mentions:
        return await bot.process_commands(message)

    # Prevent double processing
    if hasattr(message, 'processed') and message.processed:
        return

    user_msg = message.content.replace(f'<@{bot.user.id}>', '').strip() or "Hello"
    uid = message.author.id
    user_last_seen[uid] = time.time()
    user_message_count[uid] = user_message_count.get(uid, 0) + 1

    # Mark as processed to avoid command double-trigger
    message.processed = True

    async with message.channel.typing():
        reply = await generate_response(uid, user_msg, message.attachments)

    await message.reply(reply)

    # Only process commands if not already handled
    try:
        await bot.process_commands(message)
    except:
        pass

# === /help ===
@bot.tree.command(name="help", description="Kanade Help")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="Kanade Tachibana Help", color=0x4a90e2)
    embed.description = (
        "**Kanade Tachibana (Tenshi)**\n\n"
        "• Mention me to talk\n"
        "• Attach images for analysis\n"
        "• I remember our conversations\n"
        "• `/reset` (admin only)\n"
        "• Auto-forget after 30 days\n"
        "• `/stats` • `/tophelped`\n\n"
        "Need help? **@inxainee**"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# === /stats ===
@bot.tree.command(name="stats", description="Bot stats")
async def stats(interaction: discord.Interaction):
    users = len(chat_sessions)
    msgs = sum(user_message_count.values())
    avg = msgs // users if users else 0
    embed = discord.Embed(title="Kanade Stats", color=0x9b59b6)
    embed.add_field(name="Active Users", value=users, inline=True)
    embed.add_field(name="Total Messages", value=f"{msgs:,}", inline=True)
    embed.add_field(name="Avg per User", value=avg, inline=True)
    embed.set_footer(text="Model: gemini-2.5-flash | Auto-delete: 30 days")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# === /tophelped (PUBLIC) ===
@bot.tree.command(name="tophelped", description="Top 10 most helped by Kanade")
async def tophelped(interaction: discord.Interaction):
    if not user_message_count:
        return await interaction.response.send_message("No data yet.", ephemeral=False)
    top = sorted(user_message_count.items(), key=lambda x: x[1], reverse=True)[:10]
    lines = []
    for i, (uid, count) in enumerate(top):
        user = bot.get_user(uid)
        name = user.display_name if user else "Unknown"
        lines.append(f"**{i+1}** {name} — {count:,} msgs")
    embed = discord.Embed(title="Top 10 Most Helped by Kanade", description="\n".join(lines), color=0xff69b4)
    embed.set_footer(text="Keep talking... I'll help more.")
    await interaction.response.send_message(embed=embed, ephemeral=False)

# === /reset ===
@bot.tree.command(name="reset", description="ADMIN: Reset user memory")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def reset(interaction: discord.Interaction, member: discord.Member = None):
    uid = (member or interaction.user).id
    if uid in chat_sessions:
        del chat_sessions[uid]
        user_last_seen.pop(uid, None)
        user_message_count.pop(uid, None)
        await interaction.response.send_message(f"Memory reset for **{(member or interaction.user).display_name}**.", ephemeral=True)
    else:
        await interaction.response.send_message("No memory found.", ephemeral=True)

# === GENERATE RESPONSE (FIXED: NO DUPLICATES, IMAGE WORKS) ===
async def generate_response(uid: int, msg: str, attachments: List[discord.Attachment]) -> str:
    loop = asyncio.get_event_loop()
    if uid not in chat_sessions:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            chat = model.start_chat(history=[
                {"role": "user", "parts": [KANADE_SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Understood. I am Kanade. How can I assist?"]}
            ])
            chat_sessions[uid] = chat
            print(f"[MODEL] Created session for user {uid}")
        except Exception as e:
            print(f"[FATAL] {e}")
            return "Error. Try again."
    else:
        chat = chat_sessions[uid]

    try:
        # Build content: text + images
        content = [msg]
        for att in attachments:
            if att.content_type and att.content_type.startswith('image/'):
                image_bytes = await att.read()
                content.append({
                    'mime_type': att.content_type,
                    'data': image_bytes
                })
                print(f"[IMAGE] Loaded {att.filename}")

        # Send to Gemini
        response = await loop.run_in_executor(
            None,
            lambda: chat.send_message(content)
        )

        if len(chat.history) > MAX_HISTORY * 2:
            chat.history = chat.history[-MAX_HISTORY * 2:]

        return response.text.strip()

    except Exception as e:
        print(f"[GEMINI ERROR] {e}")
        return "System issue. Please repeat."

# === RUN ===
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("ERROR: DISCORD_BOT_TOKEN not set!")
    else:
        bot.run(token)
