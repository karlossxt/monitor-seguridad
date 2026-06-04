import feedparser
import requests
import os

# Configuraciones desde GitHub Secrets y variables
RSS_URL = "https://rss.app/feeds/_ML02gz2zhukdQcW6.xml"
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

KEYWORDS = ["querétaro", "qro", "bloqueo", "vial", "accidente", "precaución", "carretera", "seguridad"]

def enviar_a_discord(noticia):
    payload = {
        "embeds": [{
            "title": "🚨 ALERTA DE SEGURIDAD",
            "description": f"**{noticia.title}**\n\n{noticia.link}",
            "color": 15158332
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def ejecutar():
    feed = feedparser.parse(RSS_URL)
    # Solo revisamos las últimas 5 noticias para no saturar
    for noticia in feed.entries[:5]:
        texto = (noticia.title + " " + noticia.summary).lower()
        if any(key in texto for key in KEYWORDS):
            enviar_a_discord(noticia)
            print(f"Alerta enviada: {noticia.title}")

if __name__ == "__main__":
    ejecutar()
