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
    prompt = f"""Analiza si esta noticia es una alerta de SEGURIDAD, ACCIDENTE VIAL o DESASTRE NATURAL. 
    Responde SOLO 'SI' o 'NO'. 
    Noticia: {titulo} {resumen}"""
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
    resumen = noticia.get('summary', '')
    img_match = re.search(r'src="([^"]+)"', resumen)
    return img_match.group(1) if img_match else None

def enviar_a_discord(noticia, ciudad, config):
    if not config['webhook']:
        print(f"❌ Error: El Webhook de {ciudad} está vacío.")
        return

    img = extraer_imagen(noticia)
    desc = re.sub(r'<[^>]+>', '', noticia.get('summary', ''))[:400]
    
    # Payload ultra-limpio
    embed = {
        "title": f"🚨 {noticia.title[:250]}",
        "url": noticia.link,
        "description": desc,
        "color": config['color'],
        "footer": {"text": f"Vigilancia IA {ciudad} | {datetime.now().strftime('%I:%M %p')}"}
    }
    
    if img and img.startswith('http'):
        embed["image"] = {"url": img}

    payload = {
        "username": f"ALERTA {ciudad}",
        "embeds": [embed]
    }

    try:
        r = requests.post(config['webhook'], json=payload, timeout=10)
        if r.status_code in [200, 204]:
            print(f"🚀 MENSAJE ENTREGADO A DISCORD ({ciudad})")
        else:
            print(f"⚠️ Discord rechazó el mensaje ({ciudad}). Código: {r.status_code}, Respuesta: {r.text}")
    except Exception as e:
        print(f"💥 Error de conexión con Discord en {ciudad}: {e}")

def ejecutar():
    for ciudad, info in CONFIGURACION.items():
        print(f"\n--- 📡 PROCESANDO {ciudad} ---")
        if not info['rss'] or not info['webhook']:
            print(f"⚠️ Faltan datos para {ciudad}. Revisa los Secrets.")
            continue

        feed = feedparser.parse(info['rss'])
        for noticia in feed.entries[:8]:
            if analizar_con_ia(noticia.title, noticia.summary):
                print(f"✅ IA APROBÓ: {noticia.title[:50]}...")
                enviar_a_discord(noticia, ciudad, info)
            else:
                print(f"❌ IA RECHAZÓ: {noticia.title[:50]}...")

if __name__ == "__main__":
    ejecutar()
