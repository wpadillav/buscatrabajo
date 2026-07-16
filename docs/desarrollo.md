# Guía de desarrollo

Este documento explica cómo extender Buscatrabajo: agregar portales, modificar el scoring y contribuir al proyecto.

---

## Entorno de desarrollo

```bash
cd buscatrabajo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Cómo agregar un nuevo portal

### 1. Crear el scraper

Crea un archivo en `scrapers/` que herede de `BaseScraper`:

```python
from core.models import OfertaEmpleo
from scrapers.base import BaseScraper


class NuevoPortalScraper(BaseScraper):
    PORTAL = "nuevoportal"
    BASE_URL = "https://www.nuevoportal.com"

    def buscar(self, termino: str):
        url = f"{self.BASE_URL}/buscar?q={termino}"
        soup = self._get(url)
        if not soup:
            return

        contenedores = soup.select("div.oferta")
        for contenedor in contenedores:
            oferta = self._extraer_oferta(contenedor)
            if oferta:
                yield oferta

    def _extraer_oferta(self, contenedor):
        # Extrae los campos necesarios
        return OfertaEmpleo(
            id_externo="...",
            portal=self.PORTAL,
            titulo="...",
            empresa="...",
            ubicacion="...",
            url="...",
            descripcion="...",
            salario="...",
            modalidad="...",
        )
```

### 2. Registrar el scraper en el worker

Edita `core/worker.py` y agrega el nuevo scraper al diccionario:

```python
from scrapers.nuevoportal import NuevoPortalScraper

scrapers_disponibles = {
    "elempleo": ElempleoScraper(config),
    "infojobs": InfojobsScraper(config),
    "nuevoportal": NuevoPortalScraper(config),
}
```

### 3. Actualizar la interfaz web

En `web/templates/scrape.html` agrega una nueva opción en los checkboxes de portales.

### 4. Actualizar config.yaml

Agrega términos de búsqueda por defecto:

```yaml
busquedas:
  elempleo: [...]
  infojobs: [...]
  nuevoportal:
    - termino1
    - termino2
```

---

## Cómo modificar el scoring

Edita `config.yaml`:

```yaml
palabras_clave_positivas:
  kubernetes: 10
  terraform: 9

palabras_clave_negativas:
  java: -3
  angular: -2
```

Si necesitas lógica más compleja, edita `core/scorer.py`. Mantén el método `evaluar()` que recibe y retorna un `OfertaEmpleo`.

---

## Cómo ejecutar tests

```bash
python -m pytest tests/
```

Para agregar tests, crea archivos en `tests/` con prefijo `test_`.

---

## Convenciones de código

- Usa tipado estático cuando sea posible (`list[str]`, `dict[str, int]`).
- Documenta funciones públicas con docstrings.
- Maneja errores de red con reintentos.
- Respeta los delays configurados para no saturar los portales.

---

## Depuración

### Ver logs del scraping

En modo web, el estado se actualiza en `GET /api/scrape/status`. También puedes agregar `print()` en el worker durante el desarrollo.

### Inspeccionar HTML de un portal

```bash
source venv/bin/activate
python -c "
import httpx
from bs4 import BeautifulSoup
url = 'https://www.elempleo.com/co/ofertas-empleo/?trabajo=remoto+sistemas'
r = httpx.get(url, headers={'User-Agent': 'Mozilla/5.0'})
print(r.status_code)
print(BeautifulSoup(r.text, 'html.parser').title.string)
"
```

---

## Roadmap sugerido

- [ ] Agregar LinkedIn vía IMAP.
- [ ] Agregar Workana con Playwright.
- [ ] Historial de ejecuciones.
- [ ] Favoritos y estados de aplicación.
- [ ] Estadísticas y gráficas.
- [ ] Autenticación en el panel web.

---

## 📚 Más documentación

- [Índice de documentación](README.md)
- [Guía de usuario](guia_usuario.md)
- [Configuración de Telegram](telegram.md)
- [Arquitectura del sistema](arquitectura.md)
- [API interna](api.md)
- [Licencia](../LICENSE)
