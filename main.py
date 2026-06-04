import feedparser
import requests
import os
import re
from datetime import datetime

# --- CONFIGURACIÓN DE CIUDADES ---
CONFIGURACION = {
    "MTY": {"rss": os.getenv('RSS_MTY'), "webhook": os.getenv('WEBHOOK_MTY'), "color": 15158332},
    "CDMX": {"rss": os.getenv('RSS_CDMX'), "webhook": os.getenv('WEBHOOK_CDMX'), "color": 3447003},
    "GDL": {"rss": os.getenv('RSS_GDL'), "webhook": os.getenv('WEBHOOK_GDL'), "color": 15844367}
}

# --- FILTROS AMPLIADOS ---
INCIDENTES = [
    "balacera", "disparos", "detonaciones", "enfrentamiento", "ejecutado", "homicidio", "muerto", "herido", 
    "arma", "sicarios", "comando", "robo", "asalto", "atracan", "cristalazo", "carjacking", "secuestro",
    "levantón", "levanton", "hallazgo", "embolsado", "encobijado", "cuerpo", "restos", "fosa",
    "bloqueo", "narcobloqueo", "disturbio", "motín", "protesta", "ponchallantas", "persecución", 
    "sismo", "temblor", "alerta sísmica", "lluvia", "tormenta", "inundación", "encharcamiento",
    "accidente", "choque", "volcadura", "incendio", "explosión", "cierre", "vial", "precaución", "riesgo"
]

def extraer_imagen(noticia):
    # 1. Intentar en media_content
    if 'media_content' in noticia and noticia.media_content:
        return noticia.media_content[0]['url']
    # 2. Intentar en enclosures
    if 'enclosures' in noticia and noticia.enclosures:
        return noticia.enclosures[0]['href']
    # 3. Buscar en el texto (summary o description)
    for campo in ['summary', 'description']:
        if campo in noticia:
            img_match = re.search(r'src="([^"]+)"', noticia[campo])
            if img_match:
                return img_match.group(1)
    return None

def enviar_a_discord(noticia, ciudad, config):
    imagen_url = extraer_imagen(noticia)
    # Limpiar el texto de etiquetas HTML
    resumen_limpio = re.sub(r'<[^>]+>', '', noticia.summary)[:400]
    
    payload = {
        "username": f"VIGILANCIA {ciudad}",
        "embeds": [{
            "title": f"🚨 {noticia.title}",
            "url": noticia.link,
            "description": resumen_limpio,
            "color": config['color'],
            "image": {"url": imagen_url} if imagen_url else {},
            "footer": {
                "text": f"Central {ciudad} | {datetime.now().strftime('%I:%M %p')}",
                "icon_url": "https://abs.twimg.com/favicons/twitter.2.ico"
            }
        }]
    }
    r = requests.post(config['webhook'], json=payload)
    return r.status_code

def ejecutar():
    for ciudad, info in CONFIGURACION.items():
        print(f"\n--- 📡 ANALIZANDO: {ciudad} ---")
        
        if not info['rss'] or not info['webhook']:
            print(f"❌ ERROR: Faltan las variables (Secrets) para {ciudad}")
            continue

        try:
            feed = feedparser.parse(info['rss'])
            if not feed.entries:
                print(f"⚠️ El feed de {ciudad} no devolvió noticias. Verifica el link XML.")
                continue

            alertas_enviadas = 0
            for noticia in feed.entries[:10]:
                texto = (noticia.title + " " + (noticia.get('summary', '') or noticia.get('description', ''))).lower()
                
                # REVISIÓN DE INCIDENTES
                if any(inc in texto for inc in INCIDENTES):
                    status = enviar_a_discord(noticia, ciudad, info)
                    print(f"✅ [{status}] Alerta enviada: {noticia.title[:60]}...")
                    alertas_enviadas += 1
            
            if alertas_enviadas == 0:
                print(f"☕ Sin incidentes nuevos para {ciudad}.")
        
        except Exception as e:
            print(f"💥 Error crítico en {ciudad}: {e}")

if __name__ == "__main__":
    ejecutar()
