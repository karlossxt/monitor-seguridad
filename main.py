import feedparser
import requests
import os
from datetime import datetime

# Configuraciones
RSS_URL = "https://rss.app/feeds/_ML02gz2zhukdQcW6.xml"
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

KEYWORDS = ["querétaro", "qro", "bloqueo", "vial", "accidente", "precaución", "carretera", "seguridad"]

def extraer_imagen(noticia):
    """Intenta extraer una imagen del feed"""
    # 1. Buscar en media_content
    if 'media_content' in noticia:
        return noticia.media_content[0]['url']
    # 2. Buscar en enclosures
    if 'links' in noticia:
        for link in noticia.links:
            if 'image' in link.get('type', ''):
                return link.get('href')
    # 3. Buscar en el resumen (a veces viene ahí)
    if 'summary' in noticia and '<img' in noticia.summary:
        import re
        img_match = re.search(r'src="([^"]+)"', noticia.summary)
        if img_match:
            return img_match.group(1)
    return None

def enviar_a_discord(noticia):
    imagen_url = extraer_imagen(noticia)
    
    # Formatear la fecha actual para el footer
    fecha_hoy = datetime.now().strftime("%I:%M %p")

    payload = {
        "username": "NEWS-ALERTS-BOT",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/1243/1243911.png", # Icono naranja tipo RSS
        "embeds": [{
            "title": noticia.title,
            "url": noticia.link,
            "description": noticia.summary.split('<')[0], # Limpia etiquetas HTML si las hay
            "color": 23295, # Azul profesional (similar al de la imagen)
            "image": {
                "url": imagen_url
            } if imagen_url else {},
            "footer": {
                "text": f"GN_Carreteras | x.com • hoy a las {fecha_hoy}",
                "icon_url": "https://abs.twimg.com/favicons/twitter.2.ico"
            }
        }]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def ejecutar():
    feed = feedparser.parse(RSS_URL)
    # Revisamos las últimas 5 para procesar lo más reciente
    for noticia in feed.entries[:5]:
        texto = (noticia.title + " " + noticia.summary).lower()
        if any(key in texto for key in KEYWORDS):
            enviar_a_discord(noticia)
            print(f"Alerta enviada con imagen: {noticia.title}")

if __name__ == "__main__":
    ejecutar()
