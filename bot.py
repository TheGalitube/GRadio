import os
import discord
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
import yt_dlp
import re
import ssl
import tempfile

# SSL-Zertifikatprobleme beheben
ssl._create_default_https_context = ssl._create_unverified_context

# Lade Umgebungsvariablen
load_dotenv()

# Discord-Bot-Token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Spotify-Client initialisieren
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# Temp-Ordner für Downloads
temp_dir = os.path.join(tempfile.gettempdir(), "spotify_discord_bot")
os.makedirs(temp_dir, exist_ok=True)

# Cookies-Datei-Pfad
cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")
if not os.path.exists(cookies_path):
    # Erstelle leere Cookies-Datei, falls sie nicht existiert
    with open(cookies_path, "w") as f:
        f.write("# HTTP Cookie File\n")
    print(f"Leere Cookies-Datei erstellt: {cookies_path}")

# Bot-Konfiguration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Youtube-DL Optionen
ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'skip_download': True,
    'no_check_certificate': True,
    'prefer_insecure': True,
    'cookiefile': cookies_path,
    'extract_flat': True
}

# Hilfsfunktion für alternative YouTube-Suche (ohne SSL-Probleme)
async def search_youtube_alternative(query):
    try:
        # Alternative Methode zum Abrufen von YouTube-URLs
        process = await asyncio.create_subprocess_exec(
            'yt-dlp', '--dump-json', '--flat-playlist', f'ytsearch1:{query}',
            '--no-check-certificate', '--no-cache-dir',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"yt-dlp Fehler: {stderr.decode()}")
            return None
            
        import json
        data = json.loads(stdout.decode())
        
        # Für einzelne Ergebnisse
        if not isinstance(data, list):
            data = [data]
            
        if not data:
            return None
            
        return {
            'url': data[0].get('url'),
            'title': data[0].get('title'),
            'duration': data[0].get('duration', 0)
        }
    except Exception as e:
        print(f"Fehler bei alternativer YouTube-Suche: {str(e)}")
        return None

# Musik-Player Klasse
class MusicPlayer:
    def __init__(self, interaction):
        self.interaction = interaction
        self.bot = interaction.client
        self.guild = interaction.guild
        self.channel = interaction.channel
        self.queue = []
        self.current = None
        self.voice_client = None
        self.next = asyncio.Event()
        
        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            self.next.clear()
            
            if not self.queue:
                try:
                    await asyncio.sleep(300)  # 5 Minuten Timeout
                    if not self.queue:
                        if self.voice_client and self.voice_client.is_connected():
                            await self.voice_client.disconnect()
                        break
                except asyncio.CancelledError:
                    break
                continue
            
            self.current = self.queue.pop(0)
            self.voice_client.play(discord.FFmpegPCMAudio(self.current['url'], 
                                    options="-vn -b:a 128k"),
                                    after=lambda e: self.bot.loop.call_soon_threadsafe(self.next.set))
            
            await self.channel.send(f"🎵 Spiele jetzt: **{self.current['title']}**")
            
            await self.next.wait()
            self.current = None

# Dictionary für aktive Musik-Player
players = {}

@bot.event
async def on_ready():
    print(f'{bot.user} ist online!')
    print(f'Server: {len(bot.guilds)}')
    
    # Slash-Commands synchronisieren
    try:
        synced = await bot.tree.sync()
        print(f"Slash-Commands synchronisiert: {len(synced)}")
    except Exception as e:
        print(f"Fehler beim Synchronisieren der Slash-Commands: {e}")

@bot.tree.command(name='join', description='Bot tritt dem Sprachkanal bei')
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message('Du bist in keinem Sprachkanal!', ephemeral=True)
    
    channel = interaction.user.voice.channel
    
    # Falls Bot bereits in einem Voice-Channel ist
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()
    
    await interaction.response.send_message(f'Bot ist dem Kanal **{channel}** beigetreten!')

@bot.tree.command(name='leave', description='Bot verlässt den Sprachkanal')
async def leave(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    
    if voice_client:
        await voice_client.disconnect()
        await interaction.response.send_message('Bot hat den Sprachkanal verlassen!')
    else:
        await interaction.response.send_message('Bot ist nicht in einem Sprachkanal!', ephemeral=True)

@bot.tree.command(name='play', description='Spielt ein Lied von Spotify')
@app_commands.describe(query="Songtitel, Spotify-Link oder Künstler zum Suchen")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    # Überprüfen ob der Bot in einem Sprachkanal ist
    voice_client = interaction.guild.voice_client
    if not voice_client:
        if interaction.user.voice:
            voice_client = await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("Du musst in einem Sprachkanal sein!", ephemeral=True)
            return
    
    # Erstelle einen Music-Player für die Guild, falls noch keiner existiert
    if interaction.guild.id not in players:
        players[interaction.guild.id] = MusicPlayer(interaction)
    
    player = players[interaction.guild.id]
    player.voice_client = voice_client
    player.channel = interaction.channel
    
    # Suche auf Spotify
    await interaction.followup.send(f"🔍 Suche nach: **{query}**")
    
    # Überprüfe ob es eine Spotify-URL ist
    spotify_url_pattern = r'https://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)'
    match = re.match(spotify_url_pattern, query)
    
    tracks_to_add = []
    
    if match:
        item_type = match.group(1)
        item_id = match.group(2)
        
        if item_type == 'track':
            track = spotify.track(item_id)
            tracks_to_add.append({
                'name': f"{track['name']} - {track['artists'][0]['name']}",
                'artist': track['artists'][0]['name']
            })
        elif item_type == 'album':
            album = spotify.album_tracks(item_id)
            for track in album['items']:
                tracks_to_add.append({
                    'name': f"{track['name']} - {track['artists'][0]['name']}",
                    'artist': track['artists'][0]['name']
                })
        elif item_type == 'playlist':
            playlist = spotify.playlist_tracks(item_id)
            for item in playlist['items']:
                track = item['track']
                tracks_to_add.append({
                    'name': f"{track['name']} - {track['artists'][0]['name']}",
                    'artist': track['artists'][0]['name']
                })
    else:
        # Normale Suche
        results = spotify.search(q=query, limit=1)
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            tracks_to_add.append({
                'name': f"{track['name']} - {track['artists'][0]['name']}",
                'artist': track['artists'][0]['name']
            })
        else:
            await interaction.followup.send("❌ Keine Ergebnisse gefunden!")
            return
    
    # Lieder zur Warteschlange hinzufügen
    for track in tracks_to_add:
        try:
            # Versuche zuerst die alternative Methode
            info = await search_youtube_alternative(track['name'])
            
            if info and info.get('url'):
                player.queue.append({
                    'title': track['name'],
                    'url': info['url'],
                    'duration': info.get('duration', 0)
                })
                await interaction.followup.send(f"✅ Zur Warteschlange hinzugefügt: **{track['name']}**")
            else:
                # Fallback zur ursprünglichen Methode
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch:{track['name']}", download=False)['entries'][0]
                    player.queue.append({
                        'title': track['name'],
                        'url': info['url'],
                        'duration': info['duration']
                    })
                    await interaction.followup.send(f"✅ Zur Warteschlange hinzugefügt: **{track['name']}**")
        except Exception as e:
            await interaction.followup.send(f"❌ Fehler beim Hinzufügen von **{track['name']}**: {str(e)}")
    
    # Starte den Player, falls er nicht läuft
    if not player.voice_client.is_playing() and not player.current:
        player.next.set()

@bot.tree.command(name='queue', description='Zeigt die aktuelle Warteschlange')
async def queue(interaction: discord.Interaction):
    if interaction.guild.id not in players or not players[interaction.guild.id].queue:
        await interaction.response.send_message("Die Warteschlange ist leer!", ephemeral=True)
        return
    
    player = players[interaction.guild.id]
    queue_list = ""
    
    for i, song in enumerate(player.queue, start=1):
        queue_list += f"{i}. **{song['title']}**\n"
    
    if player.current:
        current_song = f"🎵 **Aktuell:** {player.current['title']}\n\n"
    else:
        current_song = ""
    
    await interaction.response.send_message(f"{current_song}**Warteschlange:**\n{queue_list}")

@bot.tree.command(name='skip', description='Überspringt das aktuelle Lied')
async def skip(interaction: discord.Interaction):
    if interaction.guild.id not in players:
        await interaction.response.send_message("Es wird nichts abgespielt!", ephemeral=True)
        return
    
    player = players[interaction.guild.id]
    
    if not player.voice_client or not player.voice_client.is_playing():
        await interaction.response.send_message("Es wird nichts abgespielt!", ephemeral=True)
        return
    
    player.voice_client.stop()
    await interaction.response.send_message("⏭️ Lied übersprungen!")

@bot.tree.command(name='pause', description='Pausiert die aktuelle Wiedergabe')
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("⏸️ Wiedergabe pausiert!")
    else:
        await interaction.response.send_message("Es wird derzeit nichts abgespielt!", ephemeral=True)

@bot.tree.command(name='resume', description='Setzt die Wiedergabe fort')
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("▶️ Wiedergabe fortgesetzt!")
    else:
        await interaction.response.send_message("Die Wiedergabe wurde nicht pausiert!", ephemeral=True)

@bot.tree.command(name='stop', description='Stoppt die Wiedergabe und leert die Warteschlange')
async def stop(interaction: discord.Interaction):
    if interaction.guild.id in players:
        player = players[interaction.guild.id]
        player.queue = []
        
        if player.voice_client and player.voice_client.is_playing():
            player.voice_client.stop()
        
        await interaction.response.send_message("⏹️ Wiedergabe gestoppt und Warteschlange geleert!")
    else:
        await interaction.response.send_message("Es wird nichts abgespielt!", ephemeral=True)

# Behalte alte Präfix-Commands für Kompatibilität
@bot.command(name='join')
async def join_prefix(ctx):
    if not ctx.message.author.voice:
        await ctx.send('Du bist in keinem Sprachkanal!')
        return
    
    channel = ctx.message.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    
    await ctx.send(f'Bot ist dem Kanal **{channel}** beigetreten!')

@bot.command(name='leave')
async def leave_prefix(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send('Bot hat den Sprachkanal verlassen!')
    else:
        await ctx.send('Bot ist nicht in einem Sprachkanal!')

@bot.command(name='play')
async def play_prefix(ctx, *, query):
    # Überprüfen ob der Bot in einem Sprachkanal ist
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Du musst in einem Sprachkanal sein!")
            return
    
    # Erstelle einen Music-Player für die Guild, falls noch keiner existiert
    if ctx.guild.id not in players:
        players[ctx.guild.id] = MusicPlayer(ctx)
    
    player = players[ctx.guild.id]
    player.voice_client = ctx.voice_client
    
    # Suche auf Spotify
    await ctx.send(f"🔍 Suche nach: **{query}**")
    
    # Überprüfe ob es eine Spotify-URL ist
    spotify_url_pattern = r'https://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)'
    match = re.match(spotify_url_pattern, query)
    
    tracks_to_add = []
    
    if match:
        item_type = match.group(1)
        item_id = match.group(2)
        
        if item_type == 'track':
            track = spotify.track(item_id)
            tracks_to_add.append({
                'name': f"{track['name']} - {track['artists'][0]['name']}",
                'artist': track['artists'][0]['name']
            })
        elif item_type == 'album':
            album = spotify.album_tracks(item_id)
            for track in album['items']:
                tracks_to_add.append({
                    'name': f"{track['name']} - {track['artists'][0]['name']}",
                    'artist': track['artists'][0]['name']
                })
        elif item_type == 'playlist':
            playlist = spotify.playlist_tracks(item_id)
            for item in playlist['items']:
                track = item['track']
                tracks_to_add.append({
                    'name': f"{track['name']} - {track['artists'][0]['name']}",
                    'artist': track['artists'][0]['name']
                })
    else:
        # Normale Suche
        results = spotify.search(q=query, limit=1)
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            tracks_to_add.append({
                'name': f"{track['name']} - {track['artists'][0]['name']}",
                'artist': track['artists'][0]['name']
            })
        else:
            await ctx.send("❌ Keine Ergebnisse gefunden!")
            return
    
    # Lieder zur Warteschlange hinzufügen
    for track in tracks_to_add:
        try:
            # Versuche zuerst die alternative Methode
            info = await search_youtube_alternative(track['name'])
            
            if info and info.get('url'):
                player.queue.append({
                    'title': track['name'],
                    'url': info['url'],
                    'duration': info.get('duration', 0)
                })
                await ctx.send(f"✅ Zur Warteschlange hinzugefügt: **{track['name']}**")
            else:
                # Fallback zur ursprünglichen Methode
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch:{track['name']}", download=False)['entries'][0]
                    player.queue.append({
                        'title': track['name'],
                        'url': info['url'],
                        'duration': info['duration']
                    })
                    await ctx.send(f"✅ Zur Warteschlange hinzugefügt: **{track['name']}**")
        except Exception as e:
            await ctx.send(f"❌ Fehler beim Hinzufügen von **{track['name']}**: {str(e)}")
    
    player.voice_client = ctx.voice_client
    
    # Starte den Player, falls er nicht läuft
    if not player.voice_client.is_playing() and not player.current:
        player.next.set()

@bot.command(name='queue')
async def queue_prefix(ctx):
    if ctx.guild.id not in players or not players[ctx.guild.id].queue:
        await ctx.send("Die Warteschlange ist leer!")
        return
    
    player = players[ctx.guild.id]
    queue_list = ""
    
    for i, song in enumerate(player.queue, start=1):
        queue_list += f"{i}. **{song['title']}**\n"
    
    if player.current:
        current_song = f"🎵 **Aktuell:** {player.current['title']}\n\n"
    else:
        current_song = ""
    
    await ctx.send(f"{current_song}**Warteschlange:**\n{queue_list}")

@bot.command(name='skip')
async def skip_prefix(ctx):
    if ctx.guild.id not in players:
        await ctx.send("Es wird nichts abgespielt!")
        return
    
    player = players[ctx.guild.id]
    
    if not player.voice_client.is_playing():
        await ctx.send("Es wird nichts abgespielt!")
        return
    
    player.voice_client.stop()
    await ctx.send("⏭️ Lied übersprungen!")

@bot.command(name='pause')
async def pause_prefix(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Wiedergabe pausiert!")
    else:
        await ctx.send("Es wird derzeit nichts abgespielt!")

@bot.command(name='resume')
async def resume_prefix(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Wiedergabe fortgesetzt!")
    else:
        await ctx.send("Die Wiedergabe wurde nicht pausiert!")

@bot.command(name='stop')
async def stop_prefix(ctx):
    if ctx.guild.id in players:
        player = players[ctx.guild.id]
        player.queue = []
        
        if player.voice_client and player.voice_client.is_playing():
            player.voice_client.stop()
        
        await ctx.send("⏹️ Wiedergabe gestoppt und Warteschlange geleert!")
    else:
        await ctx.send("Es wird nichts abgespielt!")

# Bot starten
bot.run(DISCORD_TOKEN) 