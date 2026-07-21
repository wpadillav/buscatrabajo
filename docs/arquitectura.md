# Arquitectura de Buscatrabajo

Este documento explica cómo está construida la aplicación y cómo interactúan sus componentes.

---

## Visión general

Buscatrabajo es una aplicación Python que consta de tres partes principales:

1. **Scrapers**: obtienen ofertas de empleo de portales web.
2. **Core**: modelos, base de datos, motor de relevancia y worker asíncrono.
3. **Web**: interfaz Flask para controlar el scraping y visualizar resultados.

```
Usuario
   │
   ▼
┌─────────────┐     POST /api/scrape/start
│  Navegador  │──────────────────────────────►┌─────────────┐
│  (web)      │◄──────────────────────────────│   Flask     │
└─────────────┘     GET /api/scrape/status    │   Server    │
                                              └──────┬──────┘
                                                     │
                                                     ▼
                                              ┌─────────────┐
                                              │   Worker    │
                                              │  (thread)   │
                                              └──────┬──────┘
                                                     │
              ┌──────────────────────────────────────┼──────────────────────────────────────┐
              │                                      │                                      │
              ▼                                      ▼                                      ▼
        ┌─────────────┐                        ┌─────────────┐                        ┌─────────────┐
        │   Elempleo  │                        │   InfoJobs  │                        │   SQLite    │
        │   Scraper   │                        │   Scraper   │                        │   Database  │
        └─────────────┘                        └─────────────┘                        └─────────────┘
```

---

## Flujo de una ejecución

### 1. El usuario configura desde la web

En `/scrape` el usuario elige:
- Portales a scrapear
- Términos de búsqueda por portal
- Umbral de relevancia
- Si quiere mantener ofertas viejas
- Si quiere recibir notificación

### 2. La web inicia el worker

La ruta `POST /api/scrape/start` recibe la configuración y llama a `ScrapingWorker.iniciar()`.

El worker es un **singleton** que ejecuta el scraping en un **hilo separado** (`threading.Thread`). Esto permite que el servidor web siga respondiendo mientras el scraping está en curso.

### 3. El worker ejecuta los scrapers

Para cada portal seleccionado:
- Recorre los términos de búsqueda.
- Realiza peticiones HTTP con `httpx`.
- Parsea el HTML con `BeautifulSoup`.
- Extrae datos como título, empresa, ubicación, salario y URL.
- Aplica el motor de relevancia (`Scorer`).
- Guarda en SQLite.
- Si está activado, envía notificaciones por Telegram (`core/notificador.py`).

### 4. Limpieza de ofertas viejas

Si el usuario no marcó "mantener ofertas viejas", el worker elimina las ofertas de cada portal que no aparecieron en la corrida actual.

> **Importante:** la limpieza es por portal. Si un portal falla (no devuelve ofertas), no se eliminan sus ofertas anteriores.

### 5. La web consulta el estado

La página `/scrape` hace polling cada 2 segundos a `GET /api/scrape/status` para mostrar el progreso.

Cuando el worker termina, la web consulta `GET /api/scrape/results` para mostrar las ofertas encontradas.

---

## Componentes principales

### `core/models.py`

Define `OfertaEmpleo`, el modelo de datos de cada oferta. Usa Pydantic para validación.

### `core/database.py`

Gestiona SQLite. Incluye:
- `guardar()`: inserta o actualiza ofertas.
- `filtrar()`: búsqueda con paginación.
- `eliminar_no_vistas()`: limpieza de ofertas obsoletas.
- `portales()`: lista de portales disponibles en la BD.

### `core/scorer.py`

Calcula la relevancia de cada oferta:
- Modalidades aceptadas (`remoto`, `hibrido`, `presencial`): la oferta debe mencionar alguna en su texto o en su etiqueta de modalidad.
- Palabras positivas según el perfil (soporte, call center, junior, etc.).
- Palabras negativas (`senior`, `inglés`, `cloud`, etc.).
- Bonus por palabras clave en el título.

Todos estos criterios se definen en `config.yaml`; el panel web permite sobreescribir por ejecución las modalidades, las palabras positivas, negativas y las del bonus de título (`stack_titulo`).

### `core/worker.py`

Ejecuta el scraping de forma asíncrona. Mantiene un estado compartido protegido con locks.

### `web/server.py`

Aplicación Flask. Expone:
- Rutas HTML: `/`, `/scrape`, `/oferta/<id>`.
- API JSON: `/api/scrape/start`, `/api/scrape/status`, `/api/scrape/results`, `/api/notificaciones/telegram/*`.

### `scrapers/elempleo.py` y `scrapers/infojobs.py`

Implementan la extracción de datos de cada portal. Usan selectores CSS y manejo de errores.

---

## Seguridad y buenas prácticas

- **User-Agent realista** para evitar bloqueos simples.
- **Delay entre peticiones** configurable (`config.yaml`).
- **Reintentos** en caso de errores de red.
- **No se almacenan contraseñas** en el código; las notificaciones se configuran en `config.yaml`.
- El servidor Flask corre en modo desarrollo; para producción se recomienda Gunicorn + Nginx.

---

## Escalabilidad futura

Si se quieren agregar más portales o tareas pesadas, se podría:
- Reemplazar el hilo por un worker con Celery + Redis.
- Usar Playwright para sitios con mucho JavaScript.
- Agregar caché con Redis para reducir scraping repetido.

---

## 📚 Más documentación

- [Índice de documentación](README.md)
- [Guía de usuario](guia_usuario.md)
- [Configuración de Telegram](telegram.md)
- [API interna](api.md)
- [Guía de desarrollo](desarrollo.md)
- [Licencia](../LICENSE)
