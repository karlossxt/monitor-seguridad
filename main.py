import feedparser
import requests
import os
import time
from datetime import datetime, timedelta
import calendar

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
def enviar_a_discord(noticia):
    # (Misma función de envío que ya tienes, pero con color rojo)
    payload = {
        "username": "MTY SEGURIDAD 24/7",
        "embeds": [{
            "title": f"🚨 {noticia.title}",
            "url": noticia.link,
            "description": noticia.summary.split('<')[0][:500],
            "color": 15158332,
            "footer": {"text": f"Alerta detectada a las {datetime.now().strftime('%I:%M %p')}"}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def revisar_feed():
    print(f"🔍 Revisando feed a las {datetime.now().strftime('%H:%M:%S')}")
    feed = feedparser.parse(RSS_URL)
    ahora_utc = calendar.timegm(time.gmtime())
    
    for noticia in feed.entries[:15]:
        texto = (noticia.title + " " + noticia.summary).lower()
        
        # Filtro 1: Geografía e Incidentes
        if any(z in texto for z in ZONAS) and any(i in texto for i in INCIDENTES):
            
            # Filtro 2: Tiempo (Solo noticias de los últimos 15 minutos)
            # Esto evita que te lleguen noticias viejas cada vez que corre el script
            try:
                publicado_time = calendar.timegm(noticia.published_parsed)
                diferencia_minutos = (ahora_utc - publicado_time) / 60
                
                if diferencia_minutos <= 15: # Solo si es muy reciente
                    enviar_a_discord(noticia)
                    print(f"✅ Noticia enviada: {noticia.title}")
            except:
                # Si el RSS no tiene fecha, enviamos por si las dudas
                enviar_a_discord(noticia)

def ejecutar():
    # CICLO 1
    revisar_feed()
    
    # ESPERA 3 MINUTOS (180 segundos)
    print("⏳ Esperando 3 minutos para la segunda revisión...")
    time.sleep(180)
    
    # CICLO 2
    revisar_feed()

if __name__ == "__main__":
    ejecutar()
