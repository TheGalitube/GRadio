import os
import signal
import psutil

# Suche nach laufenden Bot-Prozessen
def kill_bot():
    """Beendet alle laufenden Bot-Prozesse"""
    count = 0
    for proc in psutil.process_iter():
        try:
            # Überprüfe, ob es sich um einen Python-Prozess handelt, der bot.py oder alternative_player.py ausführt
            cmdline = proc.cmdline()
            if len(cmdline) >= 2 and 'python' in cmdline[0].lower() and any(x in cmdline[1].lower() for x in ['bot.py', 'alternative_player.py']):
                print(f"Beende Bot-Prozess mit PID {proc.pid}")
                os.kill(proc.pid, signal.SIGTERM)
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if count > 0:
        print(f"{count} Bot-Prozesse beendet.")
    else:
        print("Keine laufenden Bot-Prozesse gefunden.")

if __name__ == "__main__":
    kill_bot()
    print("Stop-Skript ausgeführt.") 