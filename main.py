import feedparser
import requests
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
CONFIGURACION = {
    "MTY": {"rss": os.getenv('RSS_MTY'), "webhook": os.getenv('WEBHOOK_MTY'), "color": 15158332},
    "CDMX": {"rss": os.getenv('RSS_CDMX'), "webhook": os.getenv('WEBHOOK_CDMX'), "color": 3447003},
    "GDL": {"rss": os.getenv('RSS_GDL'), "webhook": os.getenv('WEBHOOK_GDL'), "color": 15844367}
}

INCIDENTES = [
    "balacera", "disparos", "detonaciones", "enfrentamiento", "ejecutado", "homicidio", "muerto", "herido", 
    "arma", "sicarios", "comando", "robo", "asalto", "atracan", "cristalazo", "carjacking", "secuestro",
    "levantón", "levanton", "hallazgo", "embolsado", "encobijado", "cuerpo", "restos", "fosa",
    "bloqueo", "narcobloqueo", "disturbio", "motín", "protesta", "ponchallantas", "persecución", 
    "sismo", "temblor", "alerta sísmica", "lluvia", "tormenta", "inundación", "encharcamiento",
    "accidente", "choque", "volcadura", "incendio", "explosión", "cierre", "vial", "precaución", "riesgo"
]

def enviar_a_discord(noticia, ciudad, config):
    payload = {
        "username": f"VIGILANCIA {ciudad}",
        "embeds": [{
            "title": f"🚨 {noticia.title}",
            "url": noticia.link,
            "description": noticia.summary.split('<')[0][:500],
            "color": config['color'],
            "footer": {"text": f"Central {ciudad} | {datetime.now().strftime('%I:%M %p')}"}
        }]
    }
    r = requests.post(config['webhook'], json=payload)
    return r.status_code

def ejecutar():
    for ciudad, info in CONFIGURACION.items():
        print(f"\n--- 📡 PROCESANDO {ciudad} ---")
        
        if not info['rss'] or not info['webhook']:
            print(f"❌ ERROR: Faltan Secrets para {ciudad}. Revisa GitHub Settings.")
            continue

        try:
            feed = feedparser.parse(info['rss'])
            if not feed.entries:
                print(f"⚠️ El feed de {ciudad} está vacío o el link es incorrecto.")
                continue

            encontrados = 0
            for noticia in feed.entries[:10]:
                texto = (noticia.title + " " + noticia.summary).lower()
                if any(inc in texto for inc in INCIDENTES):
                    status = enviar_a_discord(noticia, ciudad, info)
                    print(f"✅ Alerta enviada ({status}): {noticia.title[:50]}...")
                    encontrados += 1
            
            if encontrados == 0:
                print(f"☕ No se encontraron incidentes recientes en {ciudad}.")
        
        except Exception as e:
            print(f"💥 Error procesando {ciudad}: {e}")

if __name__ == "__main__":
    ejecutar()
