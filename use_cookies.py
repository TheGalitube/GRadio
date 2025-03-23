import yt_dlp
import os
import ssl

# SSL-Zertifikatprobleme beheben
ssl._create_default_https_context = ssl._create_unverified_context

# Cookies-Datei erstellen
cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

with open(cookies_path, "w") as f:
    f.write("""# HTTP Cookie File
#HttpOnly_.youtube.com	TRUE	/	TRUE	1718918465	CONSENT	YES+cb
.youtube.com	TRUE	/	TRUE	1718918465	VISITOR_INFO1_LIVE	random_alphanumeric
.youtube.com	TRUE	/	TRUE	1718918465	YSC	random_alphanumeric
""")

print(f"Cookies-Datei erstellt unter: {cookies_path}")
print("Diese Datei wird vom Bot automatisch verwendet.")
print("Starte den Bot nun mit 'python bot.py'") 