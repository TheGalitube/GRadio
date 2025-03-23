# Discord Musik Bot

Ein Discord Bot zum Abspielen von Musik von YouTube, Spotify und SoundCloud.

## Installation

1. Installiere die Abhängigkeiten:
```bash
pip install -r requirements.txt
```

2. Installiere Lavalink (Java 11 oder höher erforderlich):
- Lade Lavalink.jar von [GitHub](https://github.com/freyacodes/Lavalink/releases) herunter
- Erstelle eine `application.yml` Datei mit der Standardkonfiguration
- Starte Lavalink mit: `java -jar Lavalink.jar`

3. Konfiguriere die Umgebungsvariablen:
- Kopiere die `.env.example` zu `.env`
- Füge deine API-Tokens ein:
  - Discord Bot Token
  - Spotify Client ID und Secret
  - SoundCloud Client ID

4. Starte den Bot:
```bash
python bot.py
```

## Verfügbare Befehle

- `/play <name/link>` - Spielt einen Song ab
- `/stop` - Stoppt die Wiedergabe
- `/pause` - Pausiert die Wiedergabe
- `/resume` - Setzt die Wiedergabe fort
- `/disconnect` - Trennt den Bot vom Voice Channel
