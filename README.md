# Spotify Discord Bot

Ein Discord-Bot, der Spotify-Suche und -Wiedergabe in Sprachkanälen ermöglicht.

## Voraussetzungen

- Python 3.8+
- FFmpeg (muss installiert und im PATH sein)
- Discord Bot Token
- Spotify Developer Credentials

## Installation

1. Klone dieses Repository:
```bash
git clone https://github.com/username/spotify-discord-bot.git
cd spotify-discord-bot
```

2. Installiere die Abhängigkeiten:
```bash
pip install -r requirements.txt
```

3. Konfiguriere deine .env Datei mit deinen Tokens:
```
DISCORD_TOKEN=dein_discord_token
SPOTIFY_CLIENT_ID=deine_spotify_client_id
SPOTIFY_CLIENT_SECRET=dein_spotify_client_secret
```

4. Installiere FFmpeg:
   - Windows: [Download](https://ffmpeg.org/download.html) und füge es zum PATH hinzu
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

## Discord-Bot Berechtigungen

Beim Hinzufügen des Bots zu deinem Discord-Server stelle sicher, dass die folgenden Berechtigungen aktiviert sind:
- applications.commands (für Slash-Commands)
- Nachrichtenverlauf ansehen
- Sprachkanälen beitreten
- In Sprachkanälen sprechen

## Starten des Bots

### Lokale Installation

```bash
python bot.py
```

### Server/Container Installation

Auf einem Server oder in einem Container:

```bash
# Bot starten
python start.py

# Alternativen Player verwenden
python start.py alternative

# Bot stoppen
python stop.py
```

## Befehle

Der Bot unterstützt sowohl Slash-Commands als auch Präfix-Befehle (mit `!`).

### Slash-Commands
- `/join` - Bot tritt dem Sprachkanal bei
- `/leave` - Bot verlässt den Sprachkanal
- `/play [query]` - Sucht und spielt ein Lied von Spotify
- `/queue` - Zeigt die aktuelle Warteschlange
- `/skip` - Überspringt das aktuelle Lied
- `/pause` - Pausiert die Wiedergabe
- `/resume` - Setzt die Wiedergabe fort
- `/stop` - Stoppt die Wiedergabe und leert die Warteschlange

### Präfix-Befehle (mit `!`)
- `!join` - Bot tritt dem Sprachkanal bei
- `!leave` - Bot verlässt den Sprachkanal
- `!play [query]` - Sucht und spielt ein Lied von Spotify
- `!queue` - Zeigt die aktuelle Warteschlange
- `!skip` - Überspringt das aktuelle Lied
- `!pause` - Pausiert die Wiedergabe
- `!resume` - Setzt die Wiedergabe fort
- `!stop` - Stoppt die Wiedergabe und leert die Warteschlange

## Tipps

- Du musst in einem Sprachkanal sein, um Musik abzuspielen
- Der Bot kann Spotify-Tracks, -Alben und -Playlists verarbeiten
- Die Musik wird über YouTube abgespielt, daher kann es zu geringen Qualitätsunterschieden kommen
- Beispiel für `/play`: `/play Adele Hello` oder `/play https://open.spotify.com/track/...`

## Fehlerbehebung

- Wenn der Bot keine Verbindung herstellen kann, überprüfe deine Discord- und Spotify-Tokens
- Bei Wiedergabeproblemen stelle sicher, dass FFmpeg korrekt installiert ist
- Falls der Bot keine Musik findet, könnte es an den YouTube-Beschränkungen oder fehlenden Übereinstimmungen liegen
- Falls Slash-Commands nicht funktionieren, stelle sicher, dass der Bot alle nötigen Berechtigungen hat
