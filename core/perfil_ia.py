"""
Análisis de hojas de vida con IA para generar el perfil de búsqueda.

El LLM recibe el texto del CV y devuelve un JSON con el perfil que consume
el panel de scraping: términos de búsqueda, modalidades, palabras clave
con puntajes y palabras con bonus en el título.

Proveedores soportados:
- gemini: API de Google AI Studio (generativelanguage).
- openai: cualquier API compatible con OpenAI chat completions
  (OpenAI, OpenRouter, Groq, Ollama, etc.) según `url_base`.
"""

import json

import httpx

MAX_CARACTERES_CV = 12000
TIMEOUT_SEGUNDOS = 60

URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
URL_OPENAI_DEFECTO = "https://api.openai.com/v1"

PROMPT_PLANTILLA = """Eres un asistente que configura un buscador de empleo. Analiza la siguiente hoja de vida y genera el perfil de búsqueda ideal para esa persona.

Responde ÚNICAMENTE con un JSON válido (sin markdown, sin explicaciones) con esta estructura exacta:

{{
  "terminos": {{
    "elempleo": ["término 1", "término 2", "término 3", "término 4"],
    "infojobs": ["término 1", "término 2", "término 3", "término 4"]
  }},
  "modalidades": ["remoto"],
  "palabras_positivas": {{"palabra o frase": puntos}},
  "palabras_negativas": {{"palabra o frase": puntos}},
  "stack_titulo": ["palabra1", "palabra2"]
}}

Reglas:
- "terminos": 4-5 búsquedas realistas por portal, en español, orientadas al rol objetivo del CV. elempleo es un portal colombiano e infojobs español; adapta el vocabulario.
- "modalidades": subconjunto de ["remoto", "hibrido", "presencial"] según lo que indique o sugiera el CV; si no se menciona, usa ["remoto"].
- "palabras_positivas": 15-25 palabras o frases cortas que describan habilidades, roles y tecnologías del CV, con puntaje entero de 4 a 10 según importancia. En minúsculas.
- "palabras_negativas": 8-15 palabras con puntaje entero negativo (-2 a -10) para descartar lo que NO encaja: seniority superior al del candidato (ej. "senior", "lead" si es junior), idiomas que el CV no evidencia (ej. "inglés", "english", "bilingüe" si no menciona inglés), y tecnologías/roles ajenos al perfil.
- "stack_titulo": 5-8 palabras que identifiquen el rol ideal cuando aparecen en el título de la oferta.
- No inventes habilidades que no aparezcan en el CV.

HOJA DE VIDA:
{texto_cv}"""


class ErrorProveedorIA(Exception):
    """Error al comunicarse con el proveedor de IA o al interpretar su respuesta."""


def analizar_cv(texto_cv: str, cfg_ia: dict) -> dict:
    """Envía el texto del CV al LLM configurado y devuelve el perfil validado."""
    proveedor = (cfg_ia.get("proveedor") or "gemini").strip().lower()
    api_key = (cfg_ia.get("api_key") or "").strip()
    modelo = (cfg_ia.get("modelo") or "").strip()
    url_base = (cfg_ia.get("url_base") or "").strip().rstrip("/")

    if not modelo:
        raise ErrorProveedorIA("Falta el nombre del modelo.")
    es_local = url_base.startswith(("http://localhost", "http://127.0.0.1"))
    if not api_key and not es_local:
        raise ErrorProveedorIA("Falta la API key del proveedor de IA.")

    prompt = PROMPT_PLANTILLA.format(texto_cv=texto_cv[:MAX_CARACTERES_CV])

    if proveedor == "gemini":
        respuesta_texto = _llamar_gemini(prompt, api_key, modelo)
    elif proveedor == "openai":
        respuesta_texto = _llamar_openai(prompt, api_key, modelo, url_base)
    else:
        raise ErrorProveedorIA(f"Proveedor '{proveedor}' no soportado. Usa 'gemini' u 'openai'.")

    return _validar_perfil(_extraer_json(respuesta_texto))


def _llamar_gemini(prompt: str, api_key: str, modelo: str) -> str:
    url = URL_GEMINI.format(modelo=modelo)
    try:
        respuesta = httpx.post(
            url,
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.2,
                },
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except httpx.HTTPStatusError as e:
        raise ErrorProveedorIA(f"Error de Gemini ({e.response.status_code}): {e.response.text[:200]}")
    except (httpx.RequestError, KeyError, IndexError, ValueError) as e:
        raise ErrorProveedorIA(f"No se pudo interpretar la respuesta de Gemini: {e}")


def _llamar_openai(prompt: str, api_key: str, modelo: str, url_base: str) -> str:
    base = url_base or URL_OPENAI_DEFECTO
    try:
        respuesta = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": modelo,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
        return datos["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise ErrorProveedorIA(f"Error del proveedor ({e.response.status_code}): {e.response.text[:200]}")
    except (httpx.RequestError, KeyError, IndexError, ValueError) as e:
        raise ErrorProveedorIA(f"No se pudo interpretar la respuesta del proveedor: {e}")


def _extraer_json(texto: str) -> dict:
    """Extrae el primer objeto JSON de la respuesta del LLM, tolerando
    bloques markdown o texto alrededor."""
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio == -1 or fin == -1 or fin <= inicio:
        raise ErrorProveedorIA("La IA no devolvió un JSON válido.")
    try:
        datos = json.loads(texto[inicio:fin + 1])
    except json.JSONDecodeError as e:
        raise ErrorProveedorIA(f"La IA devolvió un JSON malformado: {e}")
    if not isinstance(datos, dict):
        raise ErrorProveedorIA("La IA no devolvió un objeto JSON.")
    return datos


def _validar_perfil(datos: dict) -> dict:
    """Normaliza el perfil devuelto por la IA al formato que consume el panel."""
    return {
        "terminos": _validar_terminos(datos.get("terminos")),
        "modalidades": _validar_modalidades(datos.get("modalidades")),
        "palabras_positivas": _validar_puntajes(datos.get("palabras_positivas"), permitir_negativos=False),
        "palabras_negativas": _validar_puntajes(datos.get("palabras_negativas"), permitir_negativos=True),
        "stack_titulo": _validar_lista_palabras(datos.get("stack_titulo")),
    }


def _validar_terminos(valor) -> dict:
    if not isinstance(valor, dict):
        return {}
    terminos = {}
    for portal, lista in valor.items():
        palabras = _validar_lista_palabras(lista)
        if palabras:
            terminos[str(portal).strip().lower()] = palabras
    return terminos


def _validar_modalidades(valor) -> list:
    validas = {"remoto", "hibrido", "presencial"}
    return [m for m in _validar_lista_palabras(valor) if m in validas]


def _validar_puntajes(valor, permitir_negativos: bool) -> dict:
    if not isinstance(valor, dict):
        return {}
    puntajes = {}
    for palabra, puntos in valor.items():
        palabra = str(palabra).strip().lower()
        try:
            puntos = int(puntos)
        except (TypeError, ValueError):
            continue
        if not palabra:
            continue
        if permitir_negativos and puntos > 0:
            puntos = -puntos
        if not permitir_negativos and puntos < 0:
            puntos = -puntos
        puntajes[palabra] = puntos
    return puntajes


def _validar_lista_palabras(valor) -> list:
    if not isinstance(valor, list):
        return []
    return [p.strip().lower() for p in valor if isinstance(p, str) and p.strip()]
