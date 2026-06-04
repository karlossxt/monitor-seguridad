import feedparser
import requests
import os
import re
from datetime import datetime
from groq import Groq

# --- INICIALIZAR IA ---
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CONFIGURACION = {
    "MTY": {"rss": os.getenv('RSS_MTY'), "webhook": os.getenv('WEBHOOK_MTY'), "color": 15158332},
    "CDMX": {"rss": os.getenv('RSS_CDMX'), "webhook": os.getenv('WEBHOOK_CDMX'), "color": 3447003},
    "GDL": {"rss": os.getenv('RSS_GDL'), "webhook": os.getenv('WEBHOOK_GDL'), "color": 15844367}
}

def analizar_con_ia(titulo, resumen):
    prompt = f"¿Esta noticia es una ALERTA de seguridad, accidente o riesgo? Responde SOLO SI o NO. Noticia: {titulo} {resumen}"
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2, temperature=0
        )
        return "SI" in completion.choices[0].message.content.strip().upper()
    except: return True

def extraer_imagen(noticia):
    if 'media_content' in noticia: return noticia.media_content[0]['url']
    img_match = re.search(r'src="([^"]+)"', noticia.get('summary', ''))
    return img_match.group(1) if img_match else None

def enviar_a_discord(noticia, ciudad, config):
    # .strip() elimina espacios accidentales que causan el error 401
    webhook_url = config['webhook'].strip() if config['webhook'] else None
    if not webhook_url: return

    img = extraer_imagen(noticia)
    desc = re.sub(r'<[^>]+>', '', noticia.get('summary', ''))[:400]
    
    payload = {
        "username": f"ALERTA {ciudad}",
        "embeds": [{
            "title": f"🚨 {noticia.title[:250]}",
            "url": noticia.link,
            "description": desc,
            "color": config['color'],
            "image": {"url": img} if img else {},
            "footer": {"text": f"Vigilancia IA {ciudad} | {datetime.now().strftime('%I:%M %p')}"}
        }]
    }
    
    r = requests.post(webhook_url, json=payload)
    print(f"📡 Resultado {ciudad}: {r.status_code}")

def ejecutar():
    for ciudad, info in CONFIGURACION.items():
        print(f"\n--- 📡 PROCESANDO {ciudad} ---")
        if not info['rss'] or not info['webhook']: continue

        feed = feedparser.parse(info['rss'].strip())
        for noticia in feed.entries[:8]:
            if analizar_con_ia(noticia.title, noticia.summary):
                enviar_a_discord(noticia, ciudad, info)

if __name__ == "__main__":
    ejecutar()
