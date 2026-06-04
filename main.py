import feedparser
import requests
import time

# === CONFIGURACIÓN ===
# Pega aquí tu link de RSS.app
RSS_URL = "https://rss.app/feeds/_ML02gz2zhukdQcW6.xml" 

# Pega aquí la URL que copiaste de Discord
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1511866876051980329/uXPEKZk3P6-KM3oPrJT5aLqfcW8kCjXHSOfjf_OUd6AZVmSRMZlMnTVvjAPVJ2zLADoc"

# Palabras clave que te interesan (puedes agregar las que quieras)
KEYWORDS = ["querétaro", "qro", "bloqueo", "vial", "accidente", "precaución", "carretera", "seguridad"]

# Lista para recordar qué noticias ya enviamos y no repetir
enviados = []

def enviar_a_discord(titulo, link, descripcion):
    # Formato visual elegante (Embed)
    payload = {
        "embeds": [
            {
                "title": f"🚨 ALERTA DETECTADA",
                "description": f"**{titulo}**\n\n{descripcion[:250]}...",
                "url": link,
                "color": 15158332, # Color rojo intenso
                "footer": {"text": "Sistema de Vigilancia en Tiempo Real"}
            }
        ]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def monitorear():
    print("🚀 Monitor iniciado... buscando alertas en el feed.")
    
    while True:
        try:
            # 1. Leer el feed de noticias
            feed = feedparser.parse(RSS_URL)
            
            # 2. Revisar cada noticia en el feed
            for noticia in feed.entries:
                # Si el link ya lo enviamos antes, lo ignoramos
                if noticia.link in enviados:
                    continue
                
                # Unimos titulo y resumen para buscar palabras clave
                texto_analizar = (noticia.title + " " + noticia.summary).lower()
                
                # 3. ¿Alguna palabra clave coincide?
                if any(key in texto_analizar for key in KEYWORDS):
                    print(f"✨ ¡Coincidencia encontrada!: {noticia.title}")
                    enviar_a_discord(noticia.title, noticia.link, noticia.summary)
                    
                    # 4. Guardar en la lista de enviados
                    enviados.append(noticia.link)
                    
                    # Limpiar la lista si se hace muy grande (mantener los últimos 50)
                    if len(enviados) > 50:
                        enviados.pop(0)

            # Esperar 2 minutos para la siguiente revisión
            # (Si tu RSS.app es gratuito, puedes subir esto a 10 o 20 minutos)
            time.sleep(120) 

        except Exception as e:
            print(f"Hubo un error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitorear()
