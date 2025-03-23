import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from collections import deque
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import aiohttp
import json

# Lade Umgebungsvariablen
load_dotenv()

# YouTube API Konfiguration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Bot Konfiguration
class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(command_prefix="!", intents=intents)
        
    async def setup_hook(self):
        # Lade die Music Cog
        await self.add_cog(Music(self))
        
        # Commands synchronisieren
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Error syncing commands: {e}")

bot = MusicBot()

@bot.event
async def on_ready():
    print(f'Bot ist online als {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print(f'Bot ist in {len(bot.guilds)} Servern')
    
    # Commands beim Start synchronisieren
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_song = None
        self.queues = {}  # Queue pro Server
        self.volume = 1.0  # Standardlautstärke

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]

    async def search_youtube(self, query):
        try:
            # Suche nach dem Video
            search_response = youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=1,
                type='video'
            ).execute()

            if not search_response['items']:
                return None

            video_id = search_response['items'][0]['id']['videoId']
            title = search_response['items'][0]['snippet']['title']
            
            # Hole Video-Details für die Audio-URL
            video_response = youtube.videos().list(
                part='contentDetails',
                id=video_id
            ).execute()

            if not video_response['items']:
                return None

            # Extrahiere die Audio-URL
            audio_url = f'https://www.youtube.com/watch?v={video_id}'
            
            return {
                'url': audio_url,
                'title': title,
                'audio_url': audio_url
            }
        except HttpError as e:
            print(f'An HTTP error {e.resp.status} occurred: {e.content}')
            return None

    @app_commands.command(name="play", description="Spielt Musik von YouTube")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message("Du musst in einem Voice Channel sein!", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        
        # Prüfe ob der Bot bereits in einem Voice Channel ist
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.channel != channel:
                await interaction.guild.voice_client.move_to(channel)
        else:
            vc = await channel.connect()

        await interaction.response.send_message("Suche nach dem Song...")

        try:
            # Suche nach dem Song
            song = await self.search_youtube(query)
            if not song:
                await interaction.followup.send("Keine Songs gefunden!", ephemeral=True)
                return

            # Füge Song zur Queue hinzu
            self.get_queue(interaction.guild_id).append(song)

            # Wenn kein Song läuft, starte die Wiedergabe
            if not interaction.guild.voice_client.is_playing():
                await self.play_next(interaction)

            await interaction.followup.send(f"Song zur Queue hinzugefügt: {song['title']}")
            
        except Exception as e:
            await interaction.followup.send(f"Fehler beim Abspielen: {str(e)}", ephemeral=True)

    async def play_next(self, interaction):
        queue = self.get_queue(interaction.guild_id)
        if not queue:
            return

        song = queue.popleft()
        vc = interaction.guild.voice_client

        # Spiele den Song
        vc.play(discord.FFmpegPCMAudio(song['audio_url']), after=lambda e: asyncio.run_coroutine_threadsafe(
            self.play_next(interaction), self.bot.loop
        ))
        
        await interaction.channel.send(f"Spiele jetzt: {song['title']}")

    @app_commands.command(name="queue", description="Zeigt die aktuelle Warteschlange")
    async def queue(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild_id)
        if not queue:
            await interaction.response.send_message("Die Warteschlange ist leer!", ephemeral=True)
            return

        queue_list = "\n".join(f"{i+1}. {song['title']}" for i, song in enumerate(queue))
        await interaction.response.send_message(f"**Aktuelle Warteschlange:**\n{queue_list}")

    @app_commands.command(name="skip", description="Überspringt den aktuellen Song")
    async def skip(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            await interaction.response.send_message("Es wird aktuell keine Musik abgespielt!", ephemeral=True)
            return

        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Song übersprungen!")
        await self.play_next(interaction)

    @app_commands.command(name="volume", description="Ändert die Lautstärke (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        if not interaction.guild.voice_client:
            await interaction.response.send_message("Ich bin in keinem Voice Channel!", ephemeral=True)
            return

        if volume < 0 or volume > 100:
            await interaction.response.send_message("Die Lautstärke muss zwischen 0 und 100 liegen!", ephemeral=True)
            return

        self.volume = volume / 100
        interaction.guild.voice_client.source.volume = self.volume
        await interaction.response.send_message(f"Lautstärke auf {volume}% gesetzt!")

    @app_commands.command(name="pause", description="Pausiert die Wiedergabe")
    async def pause(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            await interaction.response.send_message("Es wird aktuell keine Musik abgespielt!", ephemeral=True)
            return

        interaction.guild.voice_client.pause()
        await interaction.response.send_message("Wiedergabe pausiert!")

    @app_commands.command(name="resume", description="Setzt die Wiedergabe fort")
    async def resume(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            await interaction.response.send_message("Es wird aktuell keine Musik abgespielt!", ephemeral=True)
            return

        interaction.guild.voice_client.resume()
        await interaction.response.send_message("Wiedergabe fortgesetzt!")

    @app_commands.command(name="stop", description="Stoppt die Musik und leert die Warteschlange")
    async def stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            self.get_queue(interaction.guild_id).clear()
            await interaction.response.send_message("Musik gestoppt und Warteschlange geleert!")
        else:
            await interaction.response.send_message("Ich spiele keine Musik!", ephemeral=True)

    @app_commands.command(name="leave", description="Verlässt den Voice Channel")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            self.get_queue(interaction.guild_id).clear()
            await interaction.response.send_message("Voice Channel verlassen!")
        else:
            await interaction.response.send_message("Ich bin in keinem Voice Channel!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))

# Bot Token laden und starten
bot.run(os.getenv('DISCORD_TOKEN'))