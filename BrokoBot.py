import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get

import asyncio

# Battles
import io
import uuid
import aiohttp

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

#for requirements.txt
#import Flask
#from threading import Thread

from keep_alive import keep_alive

import variables

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

GUILD_ID = 721200830253891594  # Replace with your server's ID

@bot.event
async def on_ready():
    global autothread
    autothread = True
    global message_sender
    message_sender = None
    await bot.tree.sync()

    # Registers the view persistent state so the button survives bot restarts
    bot.add_view(PrivateThreadSubmissionView())

    print("Bot is ready!")

# Battles
submissions = {}
allowed_extensions = (".mp3", ".wav", ".flac")

async def upload_large_file(file_bytes: bytes, filename: str) -> str:
    # Uploads large audio files to Catbox and returns the direct URL
    url = "https://catbox.moe/user/api.php"
    data = aiohttp.FormData()
    data.add_field("reqtype", "fileupload")
    data.add_field("fileToUpload", file_bytes, filename=filename)

    # Disable SSL verification for Catbox upload
    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, data=data) as response:
            if response.status == 200:
                return await response.text()
            else:
                return None

class PrivateThreadSubmissionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Submit Track",
        style=discord.ButtonStyle.success,
        custom_id="start_submission_thread"
    )
    async def create_private_thread(self,  interaction: discord.Interaction, button: discord.ui.Button):
        if not variables.battle_active:
            await interaction.response.send_message(
                "There is no active battle at the moment. Please wait for the next battle to start.",
                ephemeral=True
            )
            return

        channel = interaction.channel

        # Create a private thread for the user
        thread = await channel.create_thread(
            name=f"submission-{interaction.user.name}",
            type=discord.ChannelType.private_thread,
            auto_archive_duration=60,  # Auto-archive after 1 hour of inactivity
        )

        # Add the user to the private thread
        await thread.add_user(interaction.user)

        # Ping user inside the thread with instructions
        await thread.send(
            f"{interaction.user.mention} upload your submission here."
        )

        # Send hidden confirmation message to the user
        await interaction.response.send_message(
            f"Created a private thread for your submission: {thread.mention}",
            ephemeral=True
        )

@bot.event
async def on_message(msg: discord.Message):
    if msg.author == bot.user:
        return
    
    #1526833802083569694    
    if autothread:
        if msg.author.id != bot.user.id and msg.channel.id ==  1526833802083569694: #Channel ID for #wips
            await msg.create_thread(name=msg.attachments[0].filename if msg.attachments else msg.content[:50])
            await msg.thread.send(f"Discuss ya bull here:")
            print(f"Thread created for: {msg.author}")

    if msg.content == "what":
        await msg.reply("What?")
    
    # Battles
    if isinstance(msg.channel, discord.Thread) and msg.channel.name.startswith("submission-"):
        if not msg.attachments:
            return

        attachment = msg.attachments[0]
        ext = attachment.filename.lower()
        if not ext.endswith(allowed_extensions):
            await msg.channel.send("Invalid file type. Please upload either (.mp3, .wav, .flac).")
            return

        # Check if the user already has an existing submission stored
        existing_submission_id = None
        for sub_id, data in submissions.items():
            if data["thread_id"] == msg.channel.id:
                existing_submission_id = sub_id
                break

        if existing_submission_id:
            # Update existing submission with the new attachment file
            old_data = submissions[existing_submission_id]

            # Overwrite attachment reference and comfirmation message ID
            submissions[existing_submission_id]["attachment"] = attachment
            submissions[existing_submission_id]["message_id"] = msg.id

            await msg.channel.send(f"🔄 **Submission updated!** Your new track replaced the old one under ID **#{existing_submission_id}**")

        else:
            # First-time submission setup
            submission_id = str(uuid.uuid4())[:6].upper()  # Generate a unique ID for the submission

            submissions[submission_id] = {
                "author_id": msg.author.id,
                "attachment": attachment,
                "thread_id": msg.channel.id,
                "message_id": msg.id
            }

            await msg.channel.send(f"✅ **Submission received!** Your track is now stored under ID **#{submission_id}**. It will be posted anonymously in the submissions channel.")

    await bot.process_commands(msg)

@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    guild_id = payload.guild_id
    guild = bot.get_guild(guild_id)

    if payload.member == bot.user:
        return

    if payload.channel_id != variables.role_select_channel_id:
        return

    emoji = str(payload.emoji)

    reaction_role_map = {
        "🎵": "PROD",
        "⌨️": "GAMER",
        "💅": "CHATTER",
        "🟩": "MC",
        "🟥": "18+"
    }

    if emoji in reaction_role_map:
        role_name = reaction_role_map[emoji]
        role = get(payload.member.guild.roles, name=role_name)

        if role and payload.member:
            await payload.member.add_roles(role)
            print(f"Assigned {role_name} role to {payload.member}.")

    else:
        await message.remove_reaction(payload.emoji, payload.member)
        print("Reaction removed: User tried to react with an invalid emoji.")

@bot.event
async def on_raw_reaction_remove(payload):
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    guild_id = payload.guild_id
    guild = bot.get_guild(payload.guild_id)

    payload.member = guild.get_member(payload.user_id)

    if payload.member == bot.user:
        return

    if payload.channel_id != variables.role_select_channel_id:
        return

    emoji = str(payload.emoji)

    reaction_role_map = {
        "🎵": "PROD",
        "⌨️": "GAMER",
        "💅": "CHATTER",
        "🟩": "MC",
        "🟥": "18+"
    }

    if emoji in reaction_role_map:
        role_name = reaction_role_map[emoji]
        role = get(guild.roles, name=role_name)

        if role and payload.member:
            await payload.member.remove_roles(role)
            print(f"Removed {role_name} role from {payload.member}.")

@bot.hybrid_command(name="tts", with_app_command=True, description="Makes the message Text-To-Speech")
#@app_commands.guilds(discord.Object(id = 721200830253891594))
async def tts(ctx: commands.Context, message):
    await ctx.reply(message, tts=True)

# Battles
@bot.tree.command(name="battle_start", description="Starts a new battle and allows users to submit their tracks anonymously")
async def battle_start(interaction: discord.Interaction, desc: str):
    embed = discord.Embed(
        title="Battle Started!",
        description=(
            desc
        ),
        color=discord.Color.green()
    )  
    embed.set_footer(text="Click below to submit your track")

    # Instantiate the class view and send it alongside the embed
    view = PrivateThreadSubmissionView()
    await interaction.response.send_message(embed=embed, view=view)
    variables.battle_active = True

@bot.tree.command(name="battle_pull", description="Pulls the submissions.")
@commands.has_permissions(administrator=True)
async def battle_pull(interaction: discord.Interaction):
    global submissions

    # Defer interaction response to give time for processing
    await interaction.response.defer(ephemeral=True)

    submissions_channel = bot.get_channel(variables.battle_submissions_channel_id)
    if not submissions_channel:
        await interaction.followup.send("Submissions channel not found.")
        return
    
    if not submissions:
        await interaction.followup.send("No submissions were received.")
        return

    uploaded_count = 0

    for submission_id, data in list(submissions.items()):
        try:
            author_id = data["author_id"]
            attachment = data["attachment"]

            # Download the most recently stored attachment
            audio_bytes = await attachment.read()
            file_extension = attachment.filename.split('.')[-1]
            clean_filename = f"submission_{submission_id}.{file_extension}"

            # Post anonymously in the submissions channel
            audio_file = discord.File(io.BytesIO(audio_bytes), filename=clean_filename)
            sent_message = await submissions_channel.send(
                content=f"**Submission #{submission_id}**",
                file=audio_file
            )

            # Store mapping to reveal authors later through battle_end command
            submissions[submission_id]["message_id"] = sent_message.id

            uploaded_count += 1

            # Close and archive the threads
            thread = bot.get_channel(data["thread_id"])
            if thread:
                await thread.delete()  # Delete the thread after the battle has ended
                await thread.send("This submission thread has been archived as the battle has ended.")

        except Exception as e:
            print(f"Failed to process submission #{submission_id}: {e}")
            continue  # Skip to the next submission
    
    await interaction.followup.send(f"Pulled {uploaded_count} submissions to the submissions channel.")

@bot.tree.command(name="battle_end", description="Ends the current ongoing battle and displays the user for each submission")
@commands.has_permissions(administrator=True)
async def battle_end(interaction: discord.Interaction):
    global submissions

    # Defer interaction response to give time for processing
    await interaction.response.defer(ephemeral=True)

    # Admin command to edit existing messages and ping authors
    channel = bot.get_channel(variables.battle_submissions_channel_id)
    if not channel:
        await interaction.followup.send("Submissions channel not found.")
        return

    revealed_count = 0

    for submission_id, data in submissions.items():
        try:
            message = await channel.fetch_message(data["message_id"])
            author_id = data["author_id"]

            # Edit the message to ping the author (keeps attached audio file)
            await message.edit(
                content=f"**Submission #{submission_id}** - Submitted by: <@{author_id}>"
            )
            revealed_count += 1

        except discord.NotFound:
            print(f"Message for submission #{submission_id} not found.")
            continue  # Message not found, skip to the next submission

    variables.battle_active = False
    submissions.clear()  # Clear submissions for the next battle
    await interaction.followup.send(f"Battle ended! Revealed {revealed_count} submissions.")

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

    variables.main_role_message_id = message.id

    await interaction.followup.send("Role assignment message sent!", ephemeral=True)

@bot.tree.command(name="age_role", description="Lets people select the 18+ role for themselves, probably going to be depreciated soon")
async def age_role(interaction: discord.Interaction):
    # Check admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    description = (
        "React to this message with the corresponding emoji to assign yourself a role:\n\n"
        "🟥\n**18+**\n*You're not a minor*"
    )

    embed = discord.Embed(title="Age role", description=description, color=discord.Color.red())
    message = await interaction.channel.send(embed=embed)

    emojis = ["🟥"]

    for emoji in emojis:
        await message.add_reaction(emoji)

    variables.age_role_message_id = message.id

    await interaction.followup.send("Role assignment message sent!", ephemeral=True)

@bot.tree.command(name="suspend", description="Suspends the ability to message in a channel, so that an update can be pushed correctly")
async def suspend(interaction: discord.Interaction):
    # Check admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    global overwrites
    overwrites = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrites.send_messages = False
    
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
    
    await interaction.response.send_message(f"Suspended the ability to message in {interaction.channel.mention}", ephemeral=True)
    await interaction.channel.send("## The ability to message in this channel has been ***suspended***.\n### Please wait for an update to be pushed before messaging again.")

@bot.tree.command(name="unsuspend", description="Unsuspends the ability to message in a channel")
async def unsuspend(interaction: discord.Interaction):
    # Check admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    global overwrites
    overwrites = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrites.send_messages = True
    
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
    
    await interaction.response.send_message(f"Unsuspended the ability to message in {interaction.channel.mention}", ephemeral=True)
    await interaction.channel.send("## The ability to message in this channel has been ***unsuspended***.\n### You can now message again.")

bot.run(TOKEN)