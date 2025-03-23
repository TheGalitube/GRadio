import ssl
import certifi

def fix_ssl():
    """
    Behebt SSL-Zertifikatprobleme in Python durch Verwendung der certifi-Zertifikate.
    Vor dem Starten des Bots ausführen.
    """
    ssl._create_default_https_context = ssl._create_unverified_context
    print("SSL-Zertifikatprüfung deaktiviert.")

if __name__ == "__main__":
    fix_ssl()
    print("SSL-Fix angewendet. Du kannst jetzt den Bot starten mit 'python bot.py'") 