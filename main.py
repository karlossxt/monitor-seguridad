import feedparser
import requests
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
RSS_URL = "https://rss.app/feeds/_ML02gz2zhukdQcW6.xml"
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

# 1. Filtro Geográfico (ZMM y alrededores críticos)
ZONAS = [
    "monterrey", "mty", "nuevo león", "nuevo leon", "nl",
    "san pedro", "spgg", "guadalupe", "san nicolás", "san nicolas", 
    "apodaca", "escobedo", "santa catarina", "garcía", "garcia", 
    "juárez", "juarez", "cadereyta", "santiago", "salinas victoria", 
    "zuazua", "cumbres", "carretera nacional", "saltillo", "laredo", 
    "reynosa", "colosio", "gonzalitos", "morones prieto", "constitución"
]

# 2. Filtro de Incidentes (Seguridad y Riesgo)
INCIDENTES = [
    # Violencia y Crimen
    "balacera", "disparos", "detonaciones", "enfrentamiento", "ejecutado", 
    "homicidio", "muerto", "herido", "arma", "sicarios", "comando",
    "robo", "asalto", "atracan", "cristalazo", "carjacking", "secuestro",
    
    # Disturbios y Bloqueos
    "bloqueo", "narcobloqueo", "disturbio", "motín", "motin", "manifestación", 
    "protesta", "ponchallantas", "quemado", "persecución", "operativo", "cateo",
    
    # Vialidad y Emergencias
    "accidente", "choque", "volcadura", "incendio", "explosión", "cierre", 
    "vial", "precaución", "riesgo", "fuga"
]

def extraer_imagen(noticia):
    if 'media_content' in noticia: return noticia.media_content[0]['url']
    if 'links' in noticia:
        for link in noticia.links:
            if 'image' in link.get('type', ''): return link.get('href')
    return "https://cdn-icons-png.flaticon.com/512/1243/1243911.png" # Icono por defecto

def enviar_a_discord(noticia):
    fecha_hoy = datetime.now().strftime("%I:%M %p")
    payload = {
        "username": "ALERTA SEGURIDAD MTY",
        "embeds": [{
            "title": f"⚠️ {noticia.title}",
            "url": noticia.link,
            "description": noticia.summary.split('<')[0][:500],
            "color": 15158332, # Rojo para mayor visibilidad
            "image": {"url": extraer_imagen(noticia)},
            "footer": {
                "text": f"Monitor ZMM | {fecha_hoy}",
                "icon_url": "https://abs.twimg.com/favicons/twitter.2.ico"
            }
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def ejecutar():
    feed = feedparser.parse(RSS_URL)
    for noticia in feed.entries[:15]: # Revisamos un rango más amplio
        texto = (noticia.title + " " + noticia.summary).lower()
        
        # LÓGICA DE FILTRADO:
        # Debe mencionar una ZONA Y un INCIDENTE para evitar ruido de otros estados
        menciona_zona = any(zona in texto for zona in ZONAS)
        menciona_incidente = any(inc in texto for inc in INCIDENTES)
        
        if menciona_zona and menciona_incidente:
            # Aquí GitHub Actions no guarda estado por defecto, 
            # pero el RSS suele actualizarse. 
            enviar_a_discord(noticia)
            print(f"🚨 Alerta enviada: {noticia.title}")

if __name__ == "__main__":
    ejecutar()
