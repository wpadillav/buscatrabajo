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
  "terminos": {
    "elempleo": ["remoto sistemas", "teletrabajo soporte"],
    "infojobs": ["remoto sysadmin"]
  },
  "mantener_viejas": false,
  "umbral": 8,
  "notificar": false
}
```

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
