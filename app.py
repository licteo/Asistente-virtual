# Importar las librerías necesarias
import nltk
from googleapiclient.discovery import build
import requests
import streamlit as st

# Descargar recursos de NLTK
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
# ¡IMPORTANTE! PARA COLAB, PON TUS CLAVES DIRECTAMENTE AQUÍ.
# CUANDO DESPLIEGUES EN STREAMLIT CLOUD, USA st.secrets
HUGGINGFACE_API_TOKEN = "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" # TU TOKEN REAL
GOOGLE_API_KEY = "AIzaSyCKD9ZiNGPzRhsa7bSZBm_XYGNdWxXNEyM" # TU CLAVE REAL DE GOOGLE
CUSTOM_SEARCH_ENGINE_ID = "622da2f1bf1d04cb9" # TU ID REAL DE MOTOR DE BUSQUEDA
OPENWEATHER_API_KEY = "TU_CLAVE_REAL_DE_OPENWEATHERMAP_AQUI" # TU CLAVE REAL DE OPENWEATHERMAP


# 3. Función para buscar en internet
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
        return f"Ocurrió un error al buscar en internet: {e}. Asegúrate de que tus claves de Google sean correctas y diferentes."

# 4. Función para obtener el clima
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

# === Nueva Función para el modelo Mixtral ===
def ask_mixtral(prompt):
    """
    Envía un prompt a mistralai/Mixtral-8x7B-Instruct-v0.1 via API de Inferencia.
    """
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    formatted_prompt = f"<s>[INST] {prompt} [/INST]"

    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.7,
            "do_sample": True,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and result and "generated_text" in result[0]:
            return result[0]["generated_text"].strip()
        else:
            return f"Mixtral no pudo generar una respuesta. Detalles: {result}. Posibles causas: límites de API, modelo no accesible, o error interno."

    except requests.exceptions.RequestException as e:
        return f"Error de conexión con Mixtral: {e}. Puede que requiera suscripción o acceso especial."
    except Exception as e:
        return f"Error inesperado con Mixtral: {e}"

# === Nueva Función para el modelo Llama 3.1 ===
def ask_llama(prompt):
    """
    Envía un prompt a meta-llama/Llama-3.1-8B-Instruct via API de Inferencia.
    """
    API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    # Formato para Llama 3.1 Instruct
    formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.7,
            "do_sample": True,
            "return_full_text": False # Solo devuelve el texto generado
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and result and "generated_text" in result[0]:
            return result[0]["generated_text"].strip()
        else:
            return f"Llama no pudo generar una respuesta. Detalles: {result}. Posibles causas: límites de API, modelo no accesible, o error interno."

    except requests.exceptions.RequestException as e:
        return f"Error de conexión con Llama 3.1: {e}. Puede que requiera suscripción o acceso especial."
    except Exception as e:
        return f"Error inesperado con Llama 3.1: {e}"


# 5. Función principal de respuesta del chatbot
def responder(mensaje):
    """Responde a un mensaje, buscando en conversaciones, luego el clima, la IA (Mixtral/Llama), y finalmente en internet."""
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
    elif mensaje_lower.startswith("ia mixtral:"): # Nuevo prefijo para Mixtral
        pregunta_ia = mensaje[len("ia mixtral:"):].strip()
        return ask_mixtral(pregunta_ia)
    elif mensaje_lower.startswith("ia llama:"): # Nuevo prefijo para Llama
        pregunta_ia = mensaje[len("ia llama:"):].strip()
        return ask_llama(pregunta_ia)
    else:
        return buscar_en_internet(mensaje)

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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            respuesta_chatbot = responder(prompt)
            st.markdown(respuesta_chatbot)
    st.session_state.messages.append({"role": "assistant", "content": respuesta_chatbot})
