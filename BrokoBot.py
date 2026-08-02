import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio

#for requirements.txt
#import Flask
#from threading import Thread

from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)

GUILD_ID = 721200830253891594  # Replace with your server's ID

@bot.event
async def on_ready():
    await bot.tree.sync()
    global autothread
    autothread = True
    print("Bot is ready!")

@bot.event
async def on_message(msg):
    #1526833802083569694    
    if autothread:
        if msg.author.id != bot.user.id and msg.channel.id ==  1526833802083569694: #Channel ID for #wips
            await msg.create_thread(name=msg.attachments[0].filename if msg.attachments else msg.content[:50])
            await msg.thread.send(f"Discuss ya bull here:")
            print(f"Thread created for: {msg.author}")

    if msg.content == "what":
        await msg.reply("What?")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    guild = reaction.message.guild

    if not guild:
        return

    if hasattr("colour_role_message_id", "bot") and reaction.message.id != bot.colour_role_message_id:
        return

    emoji = str(reaction.emoji)

    reaction_role_map = {
        "🎵": "PROD",
        "⌨️": "GAMER",
        "💅": "CHATTER",
        "🟩": "MC"
    }

    if emoji in reaction_role_map:
        role_name = reaction_role_map[emoji]
        role = discord.utils.get(guild.roles, name=role_name)

        if role and user:
            await user.add_roles(role)
            print(f"Assigned {role_name} role to {user}.")

    else:
        await reaction.remove(user)

@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return

    guild = reaction.message.guild

    if not guild:
        return

    if hasattr("colour_role_message_id", "bot") and reaction.message.id != bot.colour_role_message_id:
        return

    emoji = str(reaction.emoji)

    reaction_role_map = {
        "🎵": "PROD",
        "⌨️": "GAMER",
        "💅": "CHATTER",
        "🟩": "MC"
    }

    if emoji in reaction_role_map:
        role_name = reaction_role_map[emoji]
        role = discord.utils.get(guild.roles, name=role_name)

        if role and user:
            await user.remove_roles(role)
            print(f"Removed {role_name} role from {user}.")

@bot.tree.command(name="main_roles", description="Lets user assign themselves a role automatically")
async def main_roles(interaction: discord.Interaction):
    # Check admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    description = (
        "React to this message with the corresponding emoji to assign yourself a role:\n\n"
        "🎵\n**PROD**\n*You are a music producer*\n\n"
        "⌨️\n**GAMER**\n*You wanna talk, see, play, and breathe games*\n\n"
        "💅\n**CHATTER**\n*Just here for the vibes*\n\n"
        "## We host our very own Minecraft Server!\n### If you're interested in joining, react with:\n"
        "🟩" # MC
    )
    
    embed = discord.Embed(title="Main Roles", description=description, color=discord.Color.blurple())
    message = await interaction.channel.send(embed=embed)

    emojis = ["🎵", "⌨️", "💅", "🟩"]

    for emoji in emojis:
        await message.add_reaction(emoji)

    bot.colour_role_message_id = message.id

    await interaction.followup.send("Role assignment message sent!", ephemeral=True)

bot.run(TOKEN)