import feedparser
import requests
import os
import re
import json
from datetime import datetime
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
WEBHOOK_URL = os.getenv('WEBHOOK_UNIFICADO')
RSS_URL = os.getenv('RSS_BUNDLE')

def analizar_con_ia(titulo, resumen):
    """La IA clasifica la noticia y devuelve un formato estructurado"""
    prompt = f"""
    Analiza esta noticia y clasifícala. 
    Devuelve ÚNICAMENTE un objeto JSON con este formato:
    {{
        "es_alerta": "SI" o "NO",
        "ciudad": "MTY", "CDMX", "GDL" o "OTRO",
        "tipo": "CRIMEN", "VIAL", "NATURAL" o "INFO",
        "prioridad": "ALTA", "MEDIA" o "BAJA",
        "resumen_corto": "máximo 15 palabras"
    }}
    
    NOTICIA: {titulo} {resumen}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={{"type": "json_object"}}, # Forzamos respuesta JSON
            temperature=0
        )
        return json.loads(completion.choices[0].message.content)
    except:
        return {"es_alerta": "NO"}

def enviar_a_discord(noticia, analisis):
    # Definir colores según prioridad
    colores = {
        "ALTA": 15158332,   # Rojo
        "MEDIA": 15105570,  # Naranja
        "BAJA": 3447003     # Azul
    }
    
    prioridad_emoji = "🔴" if analisis['prioridad'] == "ALTA" else "🟠" if analisis['prioridad'] == "MEDIA" else "🔵"
    
    payload = {
        "username": f"CENTRAL IA - {analisis['ciudad']}",
        "embeds": [{
            "title": f"{prioridad_emoji} [{analisis['prioridad']}] - {analisis['ciudad']}",
            "url": noticia.link,
            "description": f"**{noticia.title}**\n\n{analisis['resumen_corto']}",
            "color": colores.get(analisis['prioridad'], 0),
            "fields": [
                {"name": "📍 Ubicación", "value": analisis['ciudad'], "inline": True},
                {"name": "📝 Tipo", "value": analisis['tipo'], "inline": True}
            ],
            "footer": {"text": f"Detección Inteligente | {datetime.now().strftime('%I:%M %p')}"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

def ejecutar():
    print(f"--- 📡 MONITOR UNIFICADO INICIADO ---")
    feed = feedparser.parse(RSS_URL)
    
    # Procesamos las 10 más recientes del paquete
    for noticia in feed.entries[:10]:
        print(f"🧐 Evaluando: {noticia.title[:50]}...")
        
        analisis = analizar_con_ia(noticia.title, noticia.summary)
        
        if analisis.get("es_alerta") == "SI":
            enviar_a_discord(noticia, analisis)
            print(f"✅ ALERTA ENVIADA: {analisis['prioridad']} - {analisis['ciudad']}")
        else:
            print("❌ IA descartó por falta de relevancia.")

if __name__ == "__main__":
    ejecutar()
