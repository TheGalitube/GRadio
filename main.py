import discord
from discord.ext import commands
from discord.commands import option
import asyncio
import yt_dlp

# Bot Konfiguration
TOKEN = "DEIN_BOT_TOKEN_HIER" # Ersetze dies mit deinem Discord Bot Token
PREFIX = "!"

# Radio Streams
RADIO_STATIONS = {
    "Energy": "https://frontend.streamonkey.net/energy-deutschrap",
    "KissFM": "https://stream.kissfm.de/kissfm/mp3-192/stream.mp3",
    "SunshineLive": "https://stream.sunshine-live.de/hq/mp3-128/stream.mp3",
    "104.6 RTL": "https://rtlberlin.streamabc.net/rtlb-1046rtlde-mp3-128-5118254",
    "SWR3": "https://liveradio.swr.de/sw282p3/swr3/play.mp3"
}

# YT-DLP Optionen
YTDLP_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

# FFMPEG Optionen
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# Bot Initialisierung
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

# Voice Client Manager
class VoiceClientManager:
    def __init__(self):
        self.voice_clients = {}
        
    async def join_channel(self, ctx):
        if ctx.author.voice is None:
            await ctx.respond("Du musst in einem Sprachkanal sein, um Radio zu hören!", ephemeral=True)
            return None
        
        voice_channel = ctx.author.voice.channel
        guild_id = ctx.guild.id
        
        if guild_id in self.voice_clients:
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]
        
        voice_client = await voice_channel.connect()
        self.voice_clients[guild_id] = voice_client
        return voice_client
    
    async def play_radio(self, ctx, station_name):
        guild_id = ctx.guild.id
        
        voice_client = None
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
        else:
            voice_client = await self.join_channel(ctx)
            
        if voice_client is None:
            return
        
        if voice_client.is_playing():
            voice_client.stop()
            
        url = RADIO_STATIONS[station_name]
        
        try:
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                url = info['url']
                
            audio_source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            voice_client.play(audio_source)
            await ctx.respond(f"📻 **{station_name}** wird jetzt gespielt!")
        except Exception as e:
            await ctx.respond(f"Fehler beim Abspielen von {station_name}: {str(e)}", ephemeral=True)
    
    async def stop_radio(self, ctx):
        guild_id = ctx.guild.id
        
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            del self.voice_clients[guild_id]
            await ctx.respond("📻 Radio gestoppt und Sprachkanal verlassen.")
        else:
            await ctx.respond("Ich spiele derzeit kein Radio ab.", ephemeral=True)

# Voice Client Manager initialisieren
voice_manager = VoiceClientManager()

# Events
@bot.event
async def on_ready():
    print(f'Bot ist eingeloggt als {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Radio"))

# Radio Befehle
@bot.slash_command(name="radio", description="Wähle einen Radiosender zum Abspielen")
@option(
    "sender",
    description="Wähle einen Radiosender",
    choices=list(RADIO_STATIONS.keys())
)
async def radio(ctx, sender: str):
    await voice_manager.play_radio(ctx, sender)

@bot.slash_command(name="stop", description="Stoppt das Radio und verlässt den Kanal")
async def stop(ctx):
    await voice_manager.stop_radio(ctx)

@bot.slash_command(name="list", description="Zeigt alle verfügbaren Radiosender")
async def list_stations(ctx):
    stations_list = "\n".join([f"• {station}" for station in RADIO_STATIONS.keys()])
    embed = discord.Embed(
        title="📻 Verfügbare Radiosender",
        description=stations_list,
        color=discord.Color.blue()
    )
    await ctx.respond(embed=embed)

# Bot starten
if __name__ == "__main__":
    bot.run(TOKEN) 