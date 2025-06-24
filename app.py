# Importar las librerías necesarias
import nltk
from googleapiclient.discovery import build
import requests # Para la API del clima
import streamlit as st # <<<< ¡ESTA LÍNEA ES CRUCIAL!

# Descargar recursos de NLTK
# Estas descargas son necesarias para NLTK, se ejecutan cuando Streamlit inicia app.py
nltk.download('punkt')
nltk.download('wordnet')

# 1. Define las conversaciones predefinidas de tu chatbot
conversaciones = {
    "hola": "¡Hola! ¿Cómo estás?",
    "cuál es tu nombre": "Soy un chatbot creado en Colab.",
    "qué hora es": "No tengo forma de saber la hora exacta, pero puedo ayudarte con otras cosas.",
    "adiós": "¡Hasta luego! Que tengas un buen día."
}

# 2. Configura tus claves de API
# ¡IMPORTANTE! Reemplaza con tus claves reales
GOOGLE_API_KEY = "AIzaSyCKD9ZiNGPzRhsa7bSZBm_XYGNdWxXNEyM"
CUSTOM_SEARCH_ENGINE_ID = "622da2f1bf1d04cb9"
OPENWEATHER_API_KEY = "622da2f1bf1d04cb9" # Si la estás usando

# 3. Función para buscar en internet (si la usas)
def buscar_en_internet(pregunta):
    """Busca en internet utilizando la API de búsqueda de Google Custom Search."""
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        respuesta = service.cse().list(q=pregunta, cx=CUSTOM_SEARCH_ENGINE_ID).execute()
        if respuesta and "items" in respuesta:
            return respuesta["items"][0]["snippet"]
        else:
            return "Lo siento, no encontré información relevante en internet."
    except Exception as e:
        return f"Ocurrió un error al buscar en internet: {e}"

# 4. Función para obtener el clima (si la usas)
def obtener_clima(ciudad):
    """Obtiene información del clima para una ciudad específica usando OpenWeatherMap."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": ciudad,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "es"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("cod") == 200:
            temperatura = data["main"]["temp"]
            descripcion = data["weather"][0]["description"]
            nombre_ciudad = data["name"]
            return f"El clima en {nombre_ciudad} es {descripcion} con una temperatura de {temperatura}°C."
        else:
            return "Lo siento, no pude obtener el clima para esa ciudad. ¿Verificaste el nombre?"
    except requests.exceptions.RequestException as e:
        return f"Ocurrió un error al conectar con la API del clima: {e}"
    except Exception as e:
        return f"Ocurrió un error inesperado al procesar el clima: {e}"

# 5. Función principal de respuesta del chatbot
def responder(mensaje):
    """Responde a un mensaje, buscando en conversaciones, luego el clima, y finalmente en internet."""
    mensaje_lower = mensaje.lower()

    if mensaje_lower in conversaciones:
        return conversaciones[mensaje_lower]
    elif "clima en" in mensaje_lower:
        partes = mensaje_lower.split("clima en ")
        if len(partes) > 1:
            ciudad = partes[1].strip().replace("?", "").replace(".", "")
            if ciudad:
                return obtener_clima(ciudad)
        return "Para el clima, por favor especifica la ciudad (ej. 'clima en Londres')."
    else:
        return buscar_en_internet(mensaje) # O "Lo siento, no sé qué responder a eso." si no usas APIs externas

# === CÓDIGO DE STREAMLIT PARA LA INTERFAZ ===

st.title("Mi Chatbot de Python")

# Inicializar el historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Campo de entrada para el usuario
if prompt := st.chat_input("Escribe tu mensaje aquí:"):
    # Añadir mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Obtener la respuesta del chatbot
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."): # Muestra un spinner mientras el chatbot responde
            respuesta_chatbot = responder(prompt)
            st.markdown(respuesta_chatbot)
    # Añadir respuesta del chatbot al historial
    st.session_state.messages.append({"role": "assistant", "content": respuesta_chatbot})
