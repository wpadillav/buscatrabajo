# API interna

El servidor web expone una API REST JSON para controlar el scraping y consultar resultados.

> Esta API está pensada para ser consumida por la propia interfaz web. No requiere autenticación en el MVP.

---

## Endpoints

### `GET /api/scrape/status`

Devuelve el estado actual del worker de scraping.

**Respuesta:**

```json
{
  "status": "running",
  "message": "Scrapeando infojobs...",
  "started_at": "2026-07-15T17:00:00",
  "finished_at": null,
  "total": 45,
  "nuevas": 0,
  "eliminadas": 0,
  "relevantes": 12
}
```

Estados posibles: `idle`, `running`, `completed`, `error`.

---

### `GET /api/scrape/results`

Devuelve las ofertas relevantes encontradas en la última ejecución.

**Respuesta:**

```json
{
  "status": "completed",
  "ofertas": [
    {
      "id_externo": "12345",
      "portal": "elempleo",
      "titulo": "Analista de soporte remoto",
      "empresa": "ACME",
      "ubicacion": "Bogotá",
      "url": "https://www.elempleo.com/co/ofertas-trabajo/...",
      "descripcion": "...",
      "fecha_publicacion": "2026-07-15T00:00:00",
      "salario": "Salario confidencial",
      "modalidad": "Remoto",
      "puntos_relevancia": 15,
      "palabras_detectadas": ["+soporte (7)", "titulo:soporte (+3)"],
      "es_relevante": true
    }
  ]
}
```

---

### `POST /api/scrape/start`

Inicia una nueva ejecución de scraping.

**Body (JSON):**

```json
{
  "portales": ["elempleo", "infojobs"],
  "modalidades": ["remoto", "hibrido"],
  "terminos": {
    "elempleo": ["remoto sistemas", "teletrabajo soporte"],
    "infojobs": ["programador junior remoto"]
  },
  "mantener_viejas": false,
  "umbral": 8,
  "notificar": false,
  "stack_titulo": ["soporte", "linux", "devops"],
  "palabras_positivas": {"soporte": 7, "devops": 9},
  "palabras_negativas": {"senior": -10}
}
```

Todos los campos son opcionales; si se omiten, se usan los valores de `config.yaml`. `modalidades` acepta los nombres definidos en la sección `modalidades` de `config.yaml` (`remoto`, `hibrido`, `presencial`); la oferta debe mencionar alguna de ellas para ser considerada. `stack_titulo` son las palabras que reciben el bonus de `bonus_titulo.puntos` cuando aparecen en el título de la oferta. `palabras_positivas` y `palabras_negativas` reemplazan los diccionarios de puntaje de `config.yaml` para esa ejecución.

**Respuesta exitosa (200):**

```json
{
  "ok": true,
  "message": "Scraping iniciado correctamente."
}
```

**Respuesta de conflicto (409):** si ya hay un scraping en ejecución.

```json
{
  "ok": false,
  "message": "Ya hay un scraping en ejecución. Espera a que termine."
}
```

---

### `POST /api/cv/analizar`

Analiza una hoja de vida con IA y devuelve el perfil de búsqueda generado (términos, modalidades, palabras clave y bonus de título). El archivo se procesa en memoria y no se guarda.

**Body (multipart/form-data):**

| Campo | Descripción |
|-------|-------------|
| `archivo` | HV en PDF, DOCX o TXT (máx. 5 MB). Obligatorio. |
| `proveedor` | `gemini` u `openai` (compatible con OpenAI: OpenRouter, Groq, Ollama...). |
| `api_key` | API key del proveedor. No requerida para endpoints locales. |
| `url_base` | URL base de la API (vacío = la del proveedor). |
| `modelo` | Nombre del modelo (ej. `gemini-2.0-flash`). |

Los campos de configuración son opcionales; si se omiten, se usan los de la sección `ia` de `config.yaml`.

**Respuesta exitosa (200):**

```json
{
  "ok": true,
  "perfil": {
    "terminos": {"elempleo": ["soporte remoto"], "infojobs": ["soporte tecnico remoto"]},
    "modalidades": ["remoto"],
    "palabras_positivas": {"soporte": 8, "python": 6},
    "palabras_negativas": {"senior": -10, "inglés": -8},
    "stack_titulo": ["soporte", "junior"]
  }
}
```

**Respuestas de error:** 400 si falta el archivo, el formato no es soportado o no se pudo extraer texto; 502 si el proveedor de IA falla (API key inválida, cuota, JSON malformado).

---

### `POST /api/notificaciones/telegram/test`

Envía un mensaje de prueba al chat de Telegram configurado en `config.yaml`.

**Respuesta configurado correctamente (200):**

```json
{
  "ok": true,
  "message": "Mensaje de prueba enviado correctamente al chat 123456789.",
  "bot": "nombre_del_bot"
}
```

**Respuesta sin configurar (400):**

```json
{
  "ok": false,
  "message": "Telegram no está configurado. Revisa config.yaml."
}
```

---

### `GET /api/notificaciones/telegram/status`

Devuelve si Telegram está configurado.

**Respuesta:**

```json
{
  "configurado": true
}
```

---

## Códigos de estado HTTP

| Código | Significado |
|--------|-------------|
| 200    | OK |
| 400    | Bad Request (falta configuración, por ejemplo) |
| 409    | Conflicto: scraping ya en ejecución |
| 500    | Error interno |

---

## Ejemplo con curl

```bash
# Consultar estado
curl http://127.0.0.1:5000/api/scrape/status

# Iniciar scraping
curl -X POST http://127.0.0.1:5000/api/scrape/start \
  -H "Content-Type: application/json" \
  -d '{
    "portales": ["elempleo"],
    "terminos": {"elempleo": ["remoto sistemas"]},
    "mantener_viejas": false,
    "umbral": 8
  }'

# Ver resultados
curl http://127.0.0.1:5000/api/scrape/results

# Probar notificación de Telegram
curl -X POST http://127.0.0.1:5000/api/notificaciones/telegram/test
```

---

## 📚 Más documentación

- [Índice de documentación](README.md)
- [Guía de usuario](guia_usuario.md)
- [Configuración de Telegram](telegram.md)
- [Arquitectura del sistema](arquitectura.md)
- [Guía de desarrollo](desarrollo.md)
- [Licencia](../LICENSE)
