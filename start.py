import os
import subprocess
import sys
import ssl

# SSL-Zertifikatsprobleme beheben
ssl._create_default_https_context = ssl._create_unverified_context

def start_bot():
    """Startet den Bot im Hintergrund und gibt die PID zurück"""
    
    # Prüfe, ob wir den alternativen Player verwenden sollen
    use_alternative = len(sys.argv) > 1 and sys.argv[1].lower() == 'alternative'
    
    # Entscheide, welche Bot-Datei zu starten ist
    bot_script = "alternative_player.py" if use_alternative else "bot.py"
    
    # Starte den Bot-Prozess
    print(f"Starte {bot_script}...")
    
    # Im Container/Server-Umgebung
    if os.path.exists('/home/container'):
        cmd = [sys.executable, os.path.join('/home/container', bot_script)]
    else:
        # Lokale Entwicklungsumgebung
        cmd = [sys.executable, bot_script]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    print(f"Bot gestartet mit PID: {process.pid}")
    print("Logs:")
    
    # Zeige die ersten paar Log-Zeilen
    for i in range(10):
        line = process.stdout.readline()
        if not line:
            break
        print(line.strip())
    
    print("\nBot läuft im Hintergrund. Benutze 'python stop.py' zum Beenden.")
    return process.pid

if __name__ == "__main__":
    start_bot() 