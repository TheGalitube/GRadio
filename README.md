# GRadio - Discord Radio Bot

Ein Discord-Bot, der verschiedene deutsche Radiosender in deinem Sprachkanal abspielen kann.

## Features

- Spielt verschiedene deutsche Radiosender über Discord-Sprachkanäle ab
- Einfache Bedienung über Discord Slash-Commands
- Aktuell verfügbare Sender: Energy, KissFM, SunshineLive, 104.6 RTL, SWR3

## Voraussetzungen

- Python 3.8 oder höher
- FFmpeg (muss im System-Pfad verfügbar sein)
- Discord Bot Token
- Die Pakete aus der `requirements.txt`

## Installation

1. Repository klonen oder herunterladen
2. FFmpeg installieren:
   - Windows: [FFmpeg Download](https://ffmpeg.org/download.html)
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`
3. Python-Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```
4. Bot-Token in `main.py` eintragen:
   ```python
   TOKEN = "DEIN_BOT_TOKEN_HIER"  # Ersetze mit deinem Discord Bot Token
   ```

## Bot-Einrichtung

1. Gehe zum [Discord Developer Portal](https://discord.com/developers/applications)
2. Erstelle eine neue Application und einen Bot
3. Aktiviere die folgenden Intents:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
4. Kopiere den Bot-Token und füge ihn in `main.py` ein
5. Lade den Bot zu deinem Server ein mit den folgenden Berechtigungen:
   - Bot
   - applications.commands
   - Connect (Sprachkanäle)
   - Speak (Sprachkanäle)

## Bot starten

```
python main.py
```

## Befehle

- `/radio [sender]` - Spielt den ausgewählten Radiosender ab
- `/stop` - Stoppt das Radio und trennt den Bot vom Sprachkanal
- `/list` - Zeigt alle verfügbaren Radiosender an

## Neue Sender hinzufügen

Um neue Sender hinzuzufügen, bearbeite das `RADIO_STATIONS`-Dictionary in `main.py`:

```python
RADIO_STATIONS = {
    "Sendername": "Stream-URL",
    # Weitere Sender...
}
```
