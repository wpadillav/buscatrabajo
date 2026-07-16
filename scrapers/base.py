import time
from abc import ABC, abstractmethod
from typing import Iterator

import httpx
from bs4 import BeautifulSoup

from core.models import OfertaEmpleo


class BaseScraper(ABC):
    """Clase base para todos los scrapers de portales de empleo."""

    def __init__(self, config: dict):
        self.config = config
        self.nombre = self.__class__.__name__.replace("Scraper", "").lower()
        self.headers = {
            "User-Agent": config["requests"]["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }

    def _get(self, url: str, intentos: int = None) -> BeautifulSoup | None:
        """Realiza una petición GET con reintentos y retorna un BeautifulSoup."""
        intentos = intentos or self.config["requests"]["max_intentos"]
        timeout = self.config["requests"]["timeout_segundos"]

        for intento in range(1, intentos + 1):
            try:
                with httpx.Client(headers=self.headers, timeout=timeout, follow_redirects=True) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return BeautifulSoup(response.text, "html.parser")
            except Exception as e:
                print(f"[{self.nombre}] Intento {intento}/{intentos} fallido para {url}: {e}")
                if intento < intentos:
                    time.sleep(2 ** intento)
        return None

    def _esperar(self):
        """Pausa respetuosa entre peticiones."""
        time.sleep(self.config["requests"]["delay_entre_paginas_segundos"])

    @abstractmethod
    def buscar(self, termino: str) -> Iterator[OfertaEmpleo]:
        """Busca ofertas para un término y retorna un generador."""
        raise NotImplementedError
