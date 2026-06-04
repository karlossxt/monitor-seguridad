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
    """Prompt optimizado para ser más receptivo a noticias de vialidad y seguridad urbana"""
    prompt = f"""
    Eres un monitor de seguridad y vialidad urbana. Tu objetivo es detectar cualquier suceso que afecte la tranquilidad o movilidad.
    
    CRITERIOS DE APROBACIÓN (SI):
    - Accidentes viales, choques, volcaduras, atropellados.
    - Problemas de infraestructura (socavones, baches grandes, semáforos fallando).
    - Reportes policiacos (detenciones, persecuciones, operativos, crímenes).
    - Bloqueos, manifestaciones o tráfico inusual por eventos.
    - Desastres naturales o clima fuerte (lluvia, sismo).

    CRITERIOS DE RECHAZO (NO):
    - Publicidad, venta de productos, consejos de salud.
    - Noticias políticas de opinión o propaganda.
    - Deportes o espectáculos.

    Devuelve ÚNICAMENTE un objeto JSON:
    {{
        "es_alerta": "SI" o "NO",
        "ciudad": "MTY", "CDMX", "GDL", "EDOMEX" o "OTRO",
        "tipo": "SEGURIDAD", "VIAL", "INFRAESTRUCTURA" o "CLIMA",
        "prioridad": "ALTA" (crimen/choque grave), "MEDIA" (vialidad/obras), "BAJA" (info general),
        "resumen_corto": "máximo 15 palabras"
    }}
    
    NOTICIA: {titulo} {resumen}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5 # Subimos un poco la temperatura para que no sea tan "rígida"
        )
        return json.loads(completion.choices[0].message.content)
    except:
        # Si falla, por si acaso dejamos pasar la noticia
        return {"es_alerta": "SI", "ciudad": "DESCONOCIDA", "tipo": "REVISAR", "prioridad": "MEDIA", "resumen_corto": "Error en IA, revisar manualmente"}

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
