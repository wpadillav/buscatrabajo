import json
import re
from datetime import datetime, timedelta
from typing import Iterator
from urllib.parse import urljoin, quote_plus

import dateutil.parser
from bs4 import BeautifulSoup

from core.models import OfertaEmpleo
from scrapers.base import BaseScraper


class ElempleoScraper(BaseScraper):
    """Scraper para elempleo.com/co/

    Ver docs/desarrollo.md para aprender cómo agregar nuevos portales.
    """

    PORTAL = "elempleo"
    BASE_URL = "https://www.elempleo.com/co/ofertas-empleo/"

    def buscar(self, termino: str) -> Iterator[OfertaEmpleo]:
        url = f"{self.BASE_URL}?trabajo={quote_plus(termino)}"
        print(f"[{self.PORTAL}] Buscando: {termino} -> {url}")

        soup = self._get(url)
        if not soup:
            print(f"[{self.PORTAL}] No se pudo cargar la página de búsqueda.")
            return

        # Elempleo lista ofertas en divs con clase .result-item
        contenedores = (
            soup.select("div.result-item")
            or soup.select("div.job-card")
            or soup.select("article")
            or soup.select("div[role='listitem']")
        )

        if not contenedores:
            print(f"[{self.PORTAL}] No se encontraron contenedores de ofertas. El sitio pudo cambiar.")
            return

        for contenedor in contenedores:
            oferta = self._extraer_oferta(contenedor)
            if oferta:
                yield oferta

    def _extraer_oferta(self, contenedor: BeautifulSoup) -> OfertaEmpleo | None:
        area_bind = contenedor.find("div", attrs={"data-ga4-offerdata": True})

        if area_bind:
            try:
                datos = json.loads(area_bind["data-ga4-offerdata"])
                titulo = datos.get("title", "").strip()
                empresa = datos.get("company", "").strip()
                ubicacion = datos.get("location", "").strip()
                salario = datos.get("salary", "").strip()
                id_externo = str(datos.get("id", ""))
                url = urljoin(self.BASE_URL, datos.get("data-url", area_bind.get("data-url", "")))
            except (json.JSONDecodeError, KeyError):
                return self._extraer_oferta_fallback(contenedor)
        else:
            return self._extraer_oferta_fallback(contenedor)

        # Si no conseguimos URL, fallback
        if not url or url == self.BASE_URL:
            link = contenedor.find("a", class_=re.compile(r"js-offer-title|titulo"))
            if link and link.get("href"):
                url = urljoin(self.BASE_URL, link["href"].strip())
            else:
                return None

        if not id_externo:
            id_externo = self._extraer_id(url)

        descripcion = self._extraer_texto(
            contenedor,
            ["p.description", "div.description", ".job-description", ".summary", ".js-offer-summary"],
        )

        fecha_texto = self._extraer_texto(
            contenedor,
            ["span.date", "div.date", ".job-date", "time", ".js-offer-date"],
        )
        fecha_publicacion = self._parsear_fecha(fecha_texto)

        modalidad = self._inferir_modalidad(f"{titulo} {ubicacion}", descripcion)

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

    def _extraer_oferta_fallback(self, contenedor: BeautifulSoup) -> OfertaEmpleo | None:
        link = (
            contenedor.find("a", class_=re.compile(r"js-offer-title|titulo"))
            or contenedor.find("a", href=re.compile(r"/co/ofertas-trabajo/"))
            or contenedor.find("a")
        )
        if not link or not link.get("href"):
            return None

        url = urljoin(self.BASE_URL, link.get("href").strip())
        titulo = link.get_text(strip=True)
        id_externo = self._extraer_id(url)

        empresa = self._extraer_texto(
            contenedor,
            ["span.info-company-name", ".js-offer-company", "h3.company-name-text", ".company"],
        )

        ubicacion = self._extraer_texto(
            contenedor,
            ["span.js-offer-location", ".location", ".city", "[data-testid='job-location']"],
        )

        descripcion = self._extraer_texto(
            contenedor,
            ["p.description", "div.description", ".job-description", ".summary"],
        )

        salario = self._extraer_texto(
            contenedor,
            ["span.salary", "div.salary", ".job-salary", "[data-testid='salary']"],
        )

        fecha_texto = self._extraer_texto(
            contenedor,
            ["span.date", "div.date", ".job-date", "time", "[data-testid='job-date']"],
        )
        fecha_publicacion = self._parsear_fecha(fecha_texto)
        modalidad = self._inferir_modalidad(f"{titulo} {ubicacion}", descripcion)

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

    def _extraer_texto(self, contenedor: BeautifulSoup, selectores: list[str]) -> str:
        for selector in selectores:
            elem = contenedor.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""

    def _extraer_id(self, url: str) -> str:
        match = re.search(r"/ofertas-trabajo/[^/]+-(\d+)$", url)
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
        try:
            return dateutil.parser.parse(texto, dayfirst=True, fuzzy=True)
        except Exception:
            return None

    def _inferir_modalidad(self, ubicacion: str, descripcion: str) -> str:
        texto = f"{ubicacion} {descripcion}".lower()
        if "remoto" in texto or "home office" in texto or "teletrabajo" in texto:
            return "Remoto"
        if "híbrido" in texto or "hibrido" in texto:
            return "Híbrido"
        if "presencial" in texto:
            return "Presencial"
        return "No especificada"
