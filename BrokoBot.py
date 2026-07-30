import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    autothread = False

#@bot.event
#async def on_message(msg):
    #if msg.author.id != bot.user.id:
        #channel = bot.get_channel(msg.channel.id)
        ##await msg.create_thread(name=msg.author.display_name)


#@bot.event
#async def on_message(msg):
    #if msg.author.id != bot.user.id:
        #await msg.channel.send(f"Sup {msg.author.mention}, I am Broko af my ni- woah I can't say that")

@bot.tree.command(name="hello", description="Says hello to the user")
async def hello(interaction: discord.Interaction):
    username = interaction.user.mention
    await interaction.response.send_message(f"Sup {username}, I am Broko af my ni- woah I can't say that")

@bot.tree.command(name="autothread", description="Creates a thread in the current channel for each message sent by a user")
async def autothread(interaction: discord.Interaction):
    channel = bot.get_channel(interaction.channel_id)
    global autothread
    autothread = not autothread
    await interaction.response.send_message(f"Autothread is now {'enabled' if autothread == True else 'disabled'} in {channel.mention}")
    import time
    time.sleep(1)
    await interaction.delete_original_response()
    @bot.event
    async def on_message(msg):
        if msg.author.id != bot.user.id:
            if autothread and msg.channel.id == channel.id:
                await msg.create_thread(name=msg.attachments[0].filename if msg.attachments else msg.content[:50])
                await msg.thread.send(f"Discuss ya bull here:")

bot.run(TOKEN)