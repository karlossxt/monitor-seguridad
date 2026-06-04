import feedparser
import requests
import os
import re
import json
from datetime import datetime
from groq import Groq

# --- CONFIGURACIÓN ---
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
WEBHOOK_URL = os.getenv('WEBHOOK_UNIFICADO')
RSS_URL = os.getenv('RSS_BUNDLE')

CIUDADES_VALIDAS = ["MTY", "CDMX", "GDL", "EDOMEX"]

def analizar_con_ia(titulo, resumen):
    """Filtro de IA con restricciones geográficas y de seguridad"""
    prompt = f"""
    Eres un monitor de seguridad para MÉXICO. Clasifica noticias EXCLUSIVAMENTE para:
    MTY, CDMX, EDOMEX, GDL.
    
    REGLA: Si la noticia es de otro estado o no es riesgo/vialidad, responde 'es_alerta': 'NO'.
    
    Devuelve ÚNICAMENTE un objeto JSON:
    {{
        "es_alerta": "SI" o "NO",
        "ciudad": "MTY", "CDMX", "GDL" o "EDOMEX",
        "tipo": "SEGURIDAD", "VIAL", "INFRAESTRUCTURA" o "CLIMA",
        "prioridad": "ALTA", "MEDIA" o "BAJA",
        "resumen_corto": "máximo 12 palabras"
    }}
    
    NOTICIA: {titulo} {resumen}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(completion.choices[0].message.content)
    except:
        return {"es_alerta": "NO"}

def extraer_imagen(noticia):
    """Busca la imagen en media_content, enclosures o dentro del HTML del resumen"""
    # 1. Buscar en etiquetas de media
    if 'media_content' in noticia and noticia.media_content:
        return noticia.media_content[0]['url']
    if 'enclosures' in noticia and noticia.enclosures:
        return noticia.enclosures[0]['href']
    
    # 2. Buscar etiquetas <img> dentro del resumen (Muy común en RSS.app)
    resumen = noticia.get('summary', '')
    img_match = re.search(r'src="([^"]+)"', resumen)
    if img_match:
        return img_match.group(1)
    
    return None

def enviar_a_discord(noticia, analisis):
    # Colores visuales
    colores = {"ALTA": 15158332, "MEDIA": 15105570, "BAJA": 3447003}
    prioridad_emoji = "🔴" if analisis['prioridad'] == "ALTA" else "🟠" if analisis['prioridad'] == "MEDIA" else "🔵"
    
    # Extraer imagen
    url_foto = extraer_imagen(noticia)
    
    # Limpiar el texto de etiquetas HTML para que se vea limpio en Discord
    descripcion_limpia = re.sub(r'<[^>]+>', '', noticia.get('summary', ''))[:300]

    payload = {
        "username": f"VIGILANCIA - {analisis['ciudad']}",
        "embeds": [{
            "title": f"{prioridad_emoji} [{analisis['prioridad']}] {analisis['ciudad']}",
            "url": noticia.link,
            "description": f"**{noticia.title}**\n\n{analisis['resumen_corto']}\n\n{descripcion_limpia}...",
            "color": colores.get(analisis['prioridad'], 3447003),
            "image": {"url": url_foto} if url_foto else {},
            "fields": [
                {"name": "📍 Zona", "value": analisis['ciudad'], "inline": True},
                {"name": "📝 Categoría", "value": analisis['tipo'], "inline": True}
            ],
            "footer": {
                "text": f"Detección Inteligente | {datetime.now().strftime('%I:%M %p')}",
                "icon_url": "https://abs.twimg.com/favicons/twitter.2.ico"
            }
        }]
    }
    
    requests.post(WEBHOOK_URL, json=payload)

def ejecutar():
    print(f"--- 📡 MONITOR UNIFICADO CON IMAGEN ({datetime.now().strftime('%H:%M:%S')}) ---")
    feed = feedparser.parse(RSS_URL)
    
    # Revisamos las últimas 15 noticias
    for noticia in feed.entries[:15]:
        print(f"🧐 Evaluando: {noticia.title[:50]}...")
        
        analisis = analizar_con_ia(noticia.title, noticia.summary)
        
        # Filtro de Seguridad + Filtro Geográfico
        if analisis.get("es_alerta") == "SI" and analisis.get("ciudad") in CIUDADES_VALIDAS:
            enviar_a_discord(noticia, analisis)
            print(f"✅ ALERTA ENVIADA: {analisis['ciudad']} - {noticia.title[:30]}")
        else:
            print(f"❌ DESCARTADA (Zona o relevancia)")

if __name__ == "__main__":
    ejecutar()
