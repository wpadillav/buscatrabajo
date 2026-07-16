import re
from datetime import datetime, timedelta
from typing import Iterator
from urllib.parse import urljoin, quote_plus

import dateutil.parser
from bs4 import BeautifulSoup

from core.models import OfertaEmpleo
from scrapers.base import BaseScraper


class InfojobsScraper(BaseScraper):
    """Scraper para infojobs.net

    Ver docs/desarrollo.md para aprender cómo agregar nuevos portales.
    """

    PORTAL = "infojobs"
    BASE_URL = "https://www.infojobs.net/ofertas-trabajo"

    def buscar(self, termino: str) -> Iterator[OfertaEmpleo]:
        url = f"{self.BASE_URL}?keyword={quote_plus(termino)}"
        print(f"[{self.PORTAL}] Buscando: {termino} -> {url}")

        soup = self._get(url)
        if not soup:
            print(f"[{self.PORTAL}] No se pudo cargar la página de búsqueda.")
            return

        contenedores = (
            soup.select("div.ij-OfferCard")
            or soup.select("div.sui-AtomCard")
            or soup.select("article")
        )

        if not contenedores:
            print(f"[{self.PORTAL}] No se encontraron contenedores de ofertas. El sitio pudo cambiar.")
            return

        for contenedor in contenedores:
            oferta = self._extraer_oferta(contenedor)
            if oferta:
                yield oferta

    def _extraer_oferta(self, contenedor: BeautifulSoup) -> OfertaEmpleo | None:
        # Título: dentro de h2 con clase ij-OfferCardContent-description-title
        titulo_elem = contenedor.select_one("h2.ij-OfferCardContent-description-title a")
        if not titulo_elem:
            titulo_elem = contenedor.find("a", href=re.compile(r"/of-[a-f0-9]"))
        if not titulo_elem or not titulo_elem.get("href"):
            return None

        href = titulo_elem["href"].strip()
        # Protocol-relative URLs
        if href.startswith("//"):
            href = "https:" + href
        url = urljoin(self.BASE_URL, href)
        titulo = titulo_elem.get_text(strip=True)

        id_externo = self._extraer_id(url)

        empresa_elem = contenedor.select_one("h3.ij-OfferCardContent-description-subtitle a")
        empresa = empresa_elem.get_text(strip=True) if empresa_elem else ""

        # Detalles: ubicación, teletrabajo, fecha, contrato, jornada, salario
        detalles = [
            li.get_text(strip=True)
            for li in contenedor.select("li.ij-OfferCardContent-description-list-item")
        ]

        ubicacion = detalles[0] if len(detalles) > 0 else ""
        modalidad_raw = detalles[1] if len(detalles) > 1 else ""
        fecha_texto = detalles[2] if len(detalles) > 2 else ""
        salario = detalles[-1] if len(detalles) > 3 else ""

        fecha_publicacion = self._parsear_fecha(fecha_texto)
        modalidad = self._inferir_modalidad(modalidad_raw, "")

        # Descripción: no siempre hay resumen en el listado
        descripcion = modalidad_raw

        return OfertaEmpleo(
            id_externo=id_externo,
            portal=self.PORTAL,
            titulo=titulo,
            empresa=empresa,
            ubicacion=ubicacion,
            url=url,
            descripcion=descripcion,
            fecha_publicacion=fecha_publicacion,
            salario=salario,
            modalidad=modalidad,
        )

    def _extraer_id(self, url: str) -> str:
        match = re.search(r"/of-([a-f0-9]+)", url)
        if match:
            return match.group(1)
        return str(hash(url) % 10_000_000)

    def _parsear_fecha(self, texto: str):
        if not texto:
            return None
        texto = texto.lower()
        if "hoy" in texto:
            return datetime.now()
        if "ayer" in texto:
            return datetime.now() - timedelta(days=1)
        # InfoJobs usa "Hace Xd"
        match = re.search(r"hace\s+(\d+)\s*d", texto)
        if match:
            return datetime.now() - timedelta(days=int(match.group(1)))
        try:
            return dateutil.parser.parse(texto, dayfirst=True, fuzzy=True)
        except Exception:
            return None

    def _inferir_modalidad(self, texto: str, descripcion: str) -> str:
        texto = f"{texto} {descripcion}".lower()
        if "remoto" in texto or "home office" in texto or "teletrabajo" in texto:
            return "Remoto"
        if "híbrido" in texto or "hibrido" in texto:
            return "Híbrido"
        if "presencial" in texto:
            return "Presencial"
        return "No especificada"
