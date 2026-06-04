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
    """Pregunta a Groq si la noticia es una alerta de seguridad real."""
    prompt = f"""
    Eres un analista de seguridad experto. Analiza esta noticia y responde SOLO con la palabra 'SI' si se trata de:
    - Violencia (balaceras, robos, asaltos, ejecuciones).
    - Riesgos viales graves (bloqueos, choques mayores, cierres de carreteras).
    - Desastres naturales (sismos, inundaciones, tormentas).
    - Operativos policiales o persecuciones.

    Responde 'NO' si es política, deportes, eventos programados, clima normal o noticias generales sin riesgo inminente.

    NOTICIA: {titulo}
    RESUMEN: {resumen}

    Respuesta (SI/NO):"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2,
            temperature=0
        )
        respuesta = completion.choices[0].message.content.strip().upper()
        return "SI" in respuesta
    except Exception as e:
        print(f"⚠️ Error en IA: {e}")
        return True # Por seguridad, si la IA falla, dejamos pasar la nota

def extraer_imagen(noticia):
    if 'media_content' in noticia: return noticia.media_content[0]['url']
    if 'enclosures' in noticia and noticia.enclosures: return noticia.enclosures[0]['href']
    resumen = noticia.get('summary', '')
    img_match = re.search(r'src="([^"]+)"', resumen)
    return img_match.group(1) if img_match else None

def enviar_a_discord(noticia, ciudad, config):
    img = extraer_imagen(noticia)
    desc = re.sub(r'<[^>]+>', '', noticia.get('summary', ''))[:400]
    
    payload = {
        "username": f"VIGILANCIA IA {ciudad}",
        "embeds": [{
            "title": f"🚨 {noticia.title}",
            "url": noticia.link,
            "description": desc,
            "color": config['color'],
            "image": {"url": img} if img else {},
            "footer": {"text": f"Análisis por IA Groq | {datetime.now().strftime('%I:%M %p')}"}
        }]
    }
    requests.post(config['webhook'], json=payload)

def ejecutar():
    for ciudad, info in CONFIGURACION.items():
        print(f"\n--- 🧠 ANALIZANDO {ciudad} CON IA ---")
        if not info['rss'] or not info['webhook']: continue

        feed = feedparser.parse(info['rss'])
        
        for noticia in feed.entries[:8]: # Revisamos las 8 más recientes
            # Primero un filtro rápido de texto para no gastar tokens de IA en cosas obvias
            print(f"Evaluando: {noticia.title[:50]}...")
            
            # Mandamos a la IA a decidir
            if analizar_con_ia(noticia.title, noticia.summary):
                enviar_a_discord(noticia, ciudad, info)
                print(f"✅ IA APROBÓ: Enviando alerta.")
            else:
                print(f"❌ IA RECHAZÓ: Ruido detectado.")

if __name__ == "__main__":
    ejecutar()
