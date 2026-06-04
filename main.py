import feedparser
import requests
import os
from datetime import datetime

# --- CONFIGURACIÓN DE PAQUETES (CIUDAD: [RSS_URL, WEBHOOK_URL, COLOR]) ---
CONFIGURACION = {
    "MTY": {
        "rss": os.getenv('RSS_MTY'),
        "webhook": os.getenv('WEBHOOK_MTY'),
        "color": 15158332 # Rojo
    },
    "CDMX": {
        "rss": os.getenv('RSS_CDMX'),
        "webhook": os.getenv('WEBHOOK_CDMX'),
        "color": 3447003 # Azul
    },
    "GDL": {
        "rss": os.getenv('RSS_GDL'),
        "webhook": os.getenv('WEBHOOK_GDL'),
        "color": 15844367 # Dorado
    }
}

# --- EL FILTRO TOTAL DE SEGURIDAD Y EMERGENCIAS ---
INCIDENTES = [
    "balacera", "disparos", "detonaciones", "enfrentamiento", "ejecutado", "homicidio", "muerto", "herido", 
    "arma", "sicarios", "comando", "robo", "asalto", "atracan", "cristalazo", "carjacking", "secuestro",
    "levantón", "levanton", "hallazgo", "embolsado", "encobijado", "cuerpo", "restos", "fosa",
    "bloqueo", "narcobloqueo", "disturbio", "motín", "protesta", "ponchallantas", "persecución", 
    "sismo", "temblor", "alerta sísmica", "lluvia", "tormenta", "inundación", "encharcamiento",
    "accidente", "choque", "volcadura", "incendio", "explosión", "cierre", "vial", "precaución", "riesgo"
     "accidente", "choque", "volcadura", "incendio", "explosión", "cierre", 
    "vial", "precaución", "riesgo", "fuga"

]

def extraer_imagen(noticia):
    if 'media_content' in noticia: return noticia.media_content[0]['url']
    if 'links' in noticia:
        for link in noticia.links:
            if 'image' in link.get('type', ''): return link.get('href')
    return None

def enviar_a_discord(noticia, ciudad, config):
    imagen_url = extraer_imagen(noticia)
    payload = {
        "username": f"VIGILANCIA {ciudad}",
        "embeds": [{
            "title": f"🚨 {noticia.title}",
            "url": noticia.link,
            "description": noticia.summary.split('<')[0][:500],
            "color": config['color'],
            "image": {"url": imagen_url} if imagen_url else {},
            "footer": {
                "text": f"Central {ciudad} | {datetime.now().strftime('%I:%M %p')}",
                "icon_url": "https://abs.twimg.com/favicons/twitter.2.ico"
            }
        }]
    }
    requests.post(config['webhook'], json=payload)

def ejecutar():
    for ciudad, info in CONFIGURACION.items():
        if not info['rss'] or not info['webhook']:
            print(f"⚠️ Saltando {ciudad}: Configuración incompleta.")
            continue

        print(f"📡 Procesando {ciudad}...")
        feed = feedparser.parse(info['rss'])
        
        for noticia in feed.entries[:10]:
            texto = (noticia.title + " " + noticia.summary).lower()
            
            # Ahora solo filtramos por INCIDENTE, porque el RSS ya es de la ciudad correcta
            if any(inc in texto for inc in INCIDENTES):
                enviar_a_discord(noticia, ciudad, info)
                print(f"✅ Alerta {ciudad} enviada: {noticia.title}")

if __name__ == "__main__":
    ejecutar()
