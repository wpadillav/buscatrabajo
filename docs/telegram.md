# Configuración de notificaciones por Telegram

Buscatrabajo puede enviarte un mensaje a Telegram cada vez que termine un scraping y encuentre ofertas relevantes.

---

## ¿Qué necesitás?

1. Una cuenta de Telegram.
2. Un bot de Telegram (creado con @BotFather).
3. Tu `chat_id`.

---

## Paso 1: Crear el bot

1. Abre Telegram y busca [@BotFather](https://t.me/BotFather).
2. Inicia una conversación y escribe `/newbot`.
3. Elegí un nombre y un username para tu bot (debe terminar en `bot`, por ejemplo `buscatrabajo_bot`).
4. @BotFather te responderá con un mensaje similar a este:

```
Done! Congratulations on your new bot.
You will find it at t.me/buscatrabajo_bot.
Use this token to access the HTTP API:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

Copiá el token y guardalo. **No lo compartas con nadie.**

---

## Paso 2: Obtener tu chat_id

### Método A: con @userinfobot

1. Buscá [@userinfobot](https://t.me/userinfobot) en Telegram.
2. Iniciá una conversación.
3. El bot te responderá con tu ID:

```
Id: 123456789
First: TuNombre
```

### Método B: con la API de Telegram

1. Primero escribí un mensaje a tu bot recién creado.
2. Abrí en el navegador:

```
https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates
```

Reemplazá `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` por tu token real.

3. Buscá en la respuesta JSON algo como:

```json
{
  "message": {
    "chat": {
      "id": 123456789,
      "first_name": "TuNombre"
    }
  }
}
```

El número `123456789` es tu `chat_id`.

---

## Paso 3: Configurar Buscatrabajo

Editá el archivo `config.yaml`:

```yaml
notificaciones:
  telegram:
    bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    chat_id: "123456789"
```

Guardá el archivo y reiniciá el servidor si está corriendo.

---

## Paso 4: Probar la configuración

1. Levantá la aplicación:

```bash
python main.py
```

2. Abrí http://127.0.0.1:5000/scrape
3. En la sección "Notificaciones" deberías ver: **"Telegram configurado"**.
4. Presioná el botón **"Enviar mensaje de prueba"**.
5. Revisá Telegram: deberías recibir un mensaje de confirmación.

---

## Paso 5: Activar notificaciones en un scraping

En el panel `/scrape`:

1. Configurá el scraping como siempre.
2. Marcá la opción **"Enviar notificación al terminar"**.
3. Iniciá el scraping.

Cuando termine, si encontró ofertas relevantes, recibirás un mensaje en Telegram con:
- Cantidad de ofertas encontradas.
- Título, relevancia, empresa, ubicación y modalidad de cada una.
- Link directo para abrir la oferta.

> Las notificaciones incluyen las **ofertas relevantes encontradas en esa ejecución**, incluso si ya estaban guardadas en la base de datos. De esta forma siempre recibís el resumen de lo que se scrapeó.

---

## Notificaciones desde la consola

Si usás el modo CLI, activá las notificaciones con `--notify`:

```bash
python main.py --cli --notify
```

---

## Solución de problemas

### "Telegram no configurado"

Significa que `bot_token` o `chat_id` están vacíos en `config.yaml`. Revisá que ambos tengan valor.

### "Token inválido"

El token que ingresaste no es correcto o el bot fue eliminado. Volvé a @BotFather y generá uno nuevo.

### No recibo el mensaje de prueba

- Asegurate de haber escrito primero un mensaje a tu bot.
- Verificá que el `chat_id` sea el correcto.
- Si usás un grupo, el `chat_id` suele ser negativo (ej: `-123456789`).

### Error de red

Si ves "Error enviando mensaje de prueba", verificá tu conexión a internet y que no haya un firewall bloqueando `api.telegram.org`.

---

## Seguridad

- El `bot_token` es sensible. No lo subas a repositorios públicos.
- Considerá usar variables de entorno para el token en producción.
- El archivo `config.yaml` está en `.gitignore` por defecto.

---

## 📚 Más documentación

- [Índice de documentación](README.md)
- [Guía de usuario](guia_usuario.md)
- [Arquitectura del sistema](arquitectura.md)
- [API interna](api.md)
- [Guía de desarrollo](desarrollo.md)
- [Licencia](../LICENSE)
