# Buscatrabajo 🔍

[![Tests](https://github.com/wpadillav/buscatrabajo/actions/workflows/tests.yml/badge.svg)](https://github.com/wpadillav/buscatrabajo/actions/workflows/tests.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Agregador de ofertas de empleo **remoto** y **freelance** con interfaz web.

Por defecto está enfocado en perfiles de **soporte técnico / call center en español (sin inglés)** y **desarrollador junior**, con modalidad de trabajo seleccionable (remoto, híbrido o presencial). Todo el perfil de puntaje se puede ajustar desde el navegador o en `config.yaml`.

> MVP enfocado en **Elempleo (Colombia)** e **InfoJobs**.

---

## 🚀 Características

- **Interfaz web** para configurar y ejecutar el scraping.
- Selección de portales: Elempleo e InfoJobs.
- **Análisis de HV/CV con IA**: sube tu hoja de vida y la IA rellena el perfil de búsqueda (términos, modalidades, palabras clave). Soporta Gemini y cualquier API compatible con OpenAI (OpenRouter, Groq, Ollama...).
- Personalización de términos de búsqueda por portal.
- Bonus configurable por palabras clave en el título de la oferta.
- Ajuste del umbral de relevancia en tiempo real.
- Ejecución asíncrona: el scraping corre en segundo plano sin bloquear la web.
- Filtro por palabras clave y scoring según tu stack técnico.
- Limpieza automática de ofertas que ya no aparecen.
- Visualización de resultados con links directos a cada oferta.
- Exportación a CSV y notificaciones opcionales (Telegram / email).

---

## 📁 Estructura del proyecto

```
buscatrabajo/
├── main.py                  # Punto de entrada (por defecto levanta la web)
├── config.yaml              # Configuración base
├── requirements.txt
├── ejecutar.sh              # Script para cron
├── core/
│   ├── models.py            # Modelo OfertaEmpleo
│   ├── database.py          # SQLite
│   ├── scorer.py            # Motor de relevancia
│   ├── notificador.py       # Telegram / Email
│   ├── worker.py            # Worker asíncrono de scraping
│   ├── cv.py                # Extracción de texto de HV (PDF/DOCX/TXT)
│   └── perfil_ia.py         # Análisis de HV con LLM (Gemini / OpenAI-compatible)
├── scrapers/
│   ├── base.py              # Clase base
│   ├── elempleo.py          # Scraper Elempleo CO
│   └── infojobs.py          # Scraper InfoJobs
├── web/
│   ├── server.py            # Servidor Flask
│   ├── templates/           # HTML con Jinja2
│   └── static/              # CSS
├── tests/
│   ├── test_scorer.py       # Tests del motor de scoring
│   ├── test_cv.py           # Tests de extracción de HV
│   └── test_perfil_ia.py    # Tests del análisis con IA
├── data/
│   └── ofertas.db           # Base de datos local
└── docs/                    # Documentación extendida
    ├── arquitectura.md
    ├── guia_usuario.md
    ├── api.md
    └── desarrollo.md
```

---

## ⚙️ Instalación

```bash
cd buscatrabajo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ▶️ Uso principal (modo web)

```bash
python main.py
```

Abre tu navegador en:

- **Dashboard de ofertas:** http://127.0.0.1:5000/
- **Panel de scraping:** http://127.0.0.1:5000/scrape

Desde el panel `/scrape` puedes:

1. Elegir los portales a scrapear.
2. Elegir las modalidades aceptadas (remoto, híbrido, presencial).
3. Escribir los términos de búsqueda (uno por línea).
4. Seleccionar o escribir las palabras que reciben bonus al aparecer en el título.
5. Editar las palabras clave positivas y negativas con sus puntajes.
6. Ajustar el umbral de relevancia.
7. Decidir si mantener o eliminar ofertas viejas.
8. Pulsar **"Iniciar scraping"**.

El scraping se ejecuta en segundo plano. La página muestra el estado, las métricas y las ofertas encontradas al finalizar.

### Cambiar host o puerto

```bash
python main.py --host 0.0.0.0 --port 8080
```

---

## 🖥️ Uso en consola (modo CLI)

Si prefieres ejecutar el scraping sin abrir el navegador:

```bash
python main.py --cli
```

Otras opciones CLI:

```bash
# Solo Elempleo
python main.py --cli --portal elempleo

# Scrapear y luego levantar el servidor web
python main.py --cli --web

# Solo levantar el servidor web
python main.py --web-only

# Exportar a CSV
python main.py --cli --exportar data/ofertas_relevantes.csv

# Mantener ofertas viejas (no eliminar)
python main.py --cli --mantener-viejas

# Enviar notificación al terminar
python main.py --cli --notify
```

---

## 🛠️ Personalización

Edita `config.yaml` para ajustar la configuración por defecto (los valores de puntaje también se pueden cambiar por ejecución desde el panel web, sin editar el archivo):

- `modalidades`: modalidades de trabajo aceptadas (`remoto`, `hibrido`, `presencial`); cada una agrupa las palabras que la identifican y `activa` define la selección por defecto.
- `palabras_clave_positivas`: skills y roles que suman puntos.
- `palabras_clave_negativas`: roles o requisitos que restan puntos.
- `bonus_titulo`: palabras que suman puntos extra si aparecen en el título (`puntos` define cuánto suman).
- `umbral_relevancia`: puntaje mínimo para considerar una oferta relevante.
- `busquedas`: términos de búsqueda por portal (usados por defecto en CLI y web).
- `ia`: proveedor LLM para el análisis de HV (`proveedor`: `gemini` u `openai`, `api_key`, `url_base`, `modelo`). También editable por análisis desde el panel web.
- `notificaciones`: configuración de Telegram y email.

---

## 🔔 Notificaciones

### Telegram

1. Crea un bot con [@BotFather](https://t.me/BotFather) y copia el token.
2. Obtén tu `chat_id`:
   - Escribe un mensaje a tu bot.
   - Visita `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` y busca `"chat":{"id":123456789`.
3. Edita `config.yaml`:

```yaml
notificaciones:
  telegram:
    bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    chat_id: "123456789"
```

4. En el panel web, verás el estado de Telegram y un botón para **enviar mensaje de prueba**.
5. Marca "Enviar notificación al terminar" al iniciar un scraping.

La notificación incluye las **ofertas relevantes encontradas en esa ejecución**, incluso si ya estaban guardadas en la base de datos.

> En modo CLI usa: `python main.py --cli --notify`

---

## 📅 Programar ejecución automática

Aunque el modo web es el principal, puedes programar ejecuciones CLI con cron:

```bash
chmod +x ejecutar.sh
crontab -e
```

Ejemplo para ejecutar todos los días a las 8:00 AM:

```cron
0 8 * * * /ruta/completa/buscatrabajo/ejecutar.sh >> /ruta/completa/buscatrabajo/data/ejecucion.log 2>&1
```

---

## 🧪 Tests

```bash
python -m pytest tests/
```

---

## 📚 Documentación extendida

- [`docs/README.md`](docs/README.md) — Índice de toda la documentación.
- [`docs/guia_usuario.md`](docs/guia_usuario.md) — Guía paso a paso del uso web.
- [`docs/telegram.md`](docs/telegram.md) — Configurar notificaciones por Telegram.
- [`docs/arquitectura.md`](docs/arquitectura.md) — Cómo está construida la aplicación.
- [`docs/api.md`](docs/api.md) — Endpoints de la API interna.
- [`docs/desarrollo.md`](docs/desarrollo.md) — Cómo extender el proyecto.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Cómo contribuir al proyecto.

---

## 📜 Licencia

Este proyecto está licenciado bajo la **GNU Affero General Public License v3.0 (AGPL-3.0)**.

Mantiene las 4 libertades del software libre:
1. Usar el programa para cualquier propósito.
2. Estudiar cómo funciona y adaptarlo a tus necesidades.
3. Redistribuir copias.
4. Mejorar el programa y publicar esas mejoras.

Ver [`LICENSE`](LICENSE) para el texto completo.

---

## ⚠️ Notas importantes

1. **Los selectores CSS pueden cambiar.** Si un portal deja de funcionar, revisa `scrapers/elempleo.py` o `scrapers/infojobs.py`.
2. **Respeta los robots.txt** y no abuses de las peticiones. El delay entre páginas está configurado por defecto.
3. **LinkedIn y Workana no están incluidos** en este MVP por protecciones anti-bot.
4. **Servidor de desarrollo:** Flask corre en modo desarrollo. Para producción usa Gunicorn + Nginx.
