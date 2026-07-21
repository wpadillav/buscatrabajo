# Guía de usuario

Esta guía explica paso a paso cómo usar Buscatrabajo desde el navegador.

---

## 1. Iniciar la aplicación

```bash
cd buscatrabajo
source venv/bin/activate
python main.py
```

Verás un mensaje como este:

```
🌐 Servidor web disponible en: http://127.0.0.1:5000
Panel de control: http://127.0.0.1:5000/scrape
Presiona Ctrl+C para detener.
```

Abre tu navegador en **http://127.0.0.1:5000/scrape**.

---

## 2. Panel de scraping

La página `/scrape` tiene dos secciones principales.

### Configuración

#### Portales a scrapear

Marca los portales que quieres consultar:

- **Elempleo (Colombia)**: ofertas principalmente de Colombia.
- **InfoJobs (España / remoto)**: ofertas de España, algunas con opción remoto internacional.

#### Modalidades aceptadas

Marca qué modalidades de trabajo te sirven:

- **Remoto** (seleccionada por defecto)
- **Híbrido**
- **Presencial**

Una oferta solo se considera si su texto (incluida la etiqueta de modalidad del portal) menciona alguna de las modalidades marcadas; por eso debe quedar al menos una seleccionada. Las palabras que identifican cada modalidad se definen en `config.yaml` (sección `modalidades`). Cumplir la modalidad suma 5 puntos base.

#### Umbral de relevancia

Es el puntaje mínimo que debe tener una oferta para ser considerada relevante.

- Valor por defecto: `8`
- Si subes el valor, verás menos ofertas pero más ajustadas.
- Si lo bajas, verás más ofertas, aunque algunas menos relacionadas.

#### Opciones

- **Mantener ofertas viejas**: si la marcas, no se eliminarán las ofertas que ya no aparezcan en la nueva ejecución.
- **Enviar notificación al terminar**: requiere configurar Telegram en `config.yaml`.

#### Términos de búsqueda

Escribe un término por línea para cada portal. Ejemplos:

**Elempleo:**
```
remoto soporte tecnico
call center remoto español
mesa de ayuda remota
```

**InfoJobs:**
```
teletrabajo soporte tecnico
programador junior remoto
call center remoto
```

#### Bonus por palabras en el título

Estas palabras suman puntos extra cuando aparecen en el **título** de la oferta (por defecto, +3 cada una).

- **Palabras sugeridas**: marca o desmarca las casillas precargadas desde `config.yaml` (`bonus_titulo.palabras`).
- **Otras palabras**: escribe las que quieras, una por línea, en el campo de texto.

Las palabras seleccionadas y las escritas se combinan al iniciar el scraping. El puntaje del bonus se ajusta en `config.yaml` (`bonus_titulo.puntos`).

#### Palabras clave y puntajes

Estas palabras se buscan en **todo el texto** de la oferta (título, empresa, ubicación y descripción). Escribe una por línea con formato `palabra: puntos`:

**Positivas (suman):**
```
soporte: 7
devops: 9
linux: 8
```

**Negativas (restan):**
```
senior: -10
java: -3
```

Vienen precargadas desde `config.yaml` (`palabras_clave_positivas` y `palabras_clave_negativas`). Lo que edites aquí aplica solo a esa ejecución; el archivo no se modifica.

---

## 3. Ejecutar el scraping

Pulsa el botón **"Iniciar scraping"**.

Verás:
- Un mensaje de estado en la parte superior.
- Un spinner indicando que está en ejecución.
- Métricas en tiempo real: ofertas procesadas, nuevas relevantes, eliminadas y total relevantes.

El scraping puede tardar entre 30 segundos y 2 minutos dependiendo de la cantidad de términos y la velocidad de los portales.

---

## 4. Ver resultados

Cuando termine, aparecerá automáticamente una sección con las ofertas encontradas.

Cada oferta muestra:
- Título con link directo al portal.
- Puntaje de relevancia.
- Empresa, ubicación, modalidad y salario.
- Palabras clave detectadas (positivas en azul, negativas en rojo).

Puedes hacer clic en el título para abrir la oferta original en una nueva pestaña.

---

## 5. Notificaciones por Telegram

Podés recibir un mensaje en Telegram cada vez que termine un scraping con ofertas relevantes.

1. Configurá tu bot y chat_id en `config.yaml`.
2. En el panel `/scrape` verificá que aparezca "Telegram configurado".
3. Usá el botón **"Enviar mensaje de prueba"** para confirmar.
4. Marcá **"Enviar notificación al terminar"** antes de iniciar el scraping.

La notificación incluye las **ofertas relevantes encontradas en esa ejecución**, no solo las que nunca antes habías visto.

Para más detalles, leé [`telegram.md`](telegram.md).

---

## 6. Dashboard de ofertas guardadas

Ve a **http://127.0.0.1:5000/** para ver todas las ofertas almacenadas en la base de datos.

Desde allí puedes:
- Filtrar por portal.
- Buscar por palabra clave.
- Ver solo relevantes o todas.
- Navegar por páginas.

---

## 7. Buenas prácticas

- No ejecutes scraping muy frecuentemente (máximo 2-3 veces al día) para no saturar los portales.
- Revisa periódicamente si los selectores siguen funcionando.
- Ajusta el umbral y las palabras clave en `config.yaml` según los resultados que obtengas.
- Usá el modo CLI (`python main.py --cli`) si quieres automatizarlo con cron.

---

## 📚 Más documentación

- [Índice de documentación](README.md)
- [Configuración de Telegram](telegram.md)
- [Arquitectura del sistema](arquitectura.md)
- [API interna](api.md)
- [Guía de desarrollo](desarrollo.md)
- [Licencia](../LICENSE)
