"""
Worker asíncrono para ejecutar el scraping sin bloquear el servidor web.

Más detalles sobre el flujo de ejecución en docs/arquitectura.md.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from core.database import Database
from core.models import OfertaEmpleo
from core.notificador import Notificador
from core.scorer import Scorer
from scrapers.elempleo import ElempleoScraper
from scrapers.infojobs import InfojobsScraper


@dataclass
class EstadoScraping:
    status: str = "idle"  # idle, running, completed, error
    message: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total: int = 0
    nuevas: int = 0
    eliminadas: int = 0
    relevantes: int = 0
    ofertas: list[dict] = field(default_factory=list)


class ScrapingWorker:
    """
    Ejecuta el scraping en un hilo separado y mantiene el estado accesible
    para el servidor web.
    """

    _instancia = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._init()
        return cls._instancia

    def _init(self):
        self.estado = EstadoScraping()
        self._estado_lock = threading.Lock()
        self._hilo: threading.Thread | None = None
        self._callback_finalizado: Callable | None = None

    def obtener_estado(self) -> EstadoScraping:
        with self._estado_lock:
            return EstadoScraping(
                status=self.estado.status,
                message=self.estado.message,
                started_at=self.estado.started_at,
                finished_at=self.estado.finished_at,
                total=self.estado.total,
                nuevas=self.estado.nuevas,
                eliminadas=self.estado.eliminadas,
                relevantes=self.estado.relevantes,
                ofertas=list(self.estado.ofertas),
            )

    def _actualizar_estado(self, **kwargs):
        with self._estado_lock:
            for clave, valor in kwargs.items():
                setattr(self.estado, clave, valor)

    def esta_corriendo(self) -> bool:
        with self._estado_lock:
            return self.estado.status == "running"

    def iniciar(
        self,
        config: dict,
        portales: list[str] | None = None,
        terminos: dict[str, list[str]] | None = None,
        mantener_viejas: bool = False,
        umbral: int | None = None,
        notificar: bool = False,
    ) -> bool:
        """Inicia el scraping en segundo plano si no hay uno en ejecución."""
        if self.esta_corriendo():
            return False

        self._hilo = threading.Thread(
            target=self._ejecutar,
            args=(config, portales, terminos, mantener_viejas, umbral, notificar),
            daemon=True,
        )
        self._hilo.start()
        return True

    def _ejecutar(
        self,
        config: dict,
        portales: list[str] | None,
        terminos: dict[str, list[str]] | None,
        mantener_viejas: bool,
        umbral: int | None,
        notificar: bool,
    ):
        self._actualizar_estado(
            status="running",
            message="Iniciando scraping...",
            started_at=datetime.now(),
            finished_at=None,
            total=0,
            nuevas=0,
            eliminadas=0,
            relevantes=0,
            ofertas=[],
        )

        try:
            db = Database()
            scorer = Scorer(
                obligatorias=config["palabras_clave_obligatorias"],
                positivas=config["palabras_clave_positivas"],
                negativas=config["palabras_clave_negativas"],
                umbral=umbral if umbral is not None else config["umbral_relevancia"],
            )

            scrapers_disponibles = {
                "elempleo": ElempleoScraper(config),
                "infojobs": InfojobsScraper(config),
            }

            portales = portales or list(scrapers_disponibles.keys())
            terminos = terminos or config.get("busquedas", {})

            scrapers = []
            for portal in portales:
                if portal in scrapers_disponibles:
                    scrapers.append(scrapers_disponibles[portal])

            ofertas_relevantes_corrida: list[OfertaEmpleo] = []
            nuevas_relevantes: list[OfertaEmpleo] = []
            total_procesadas = 0
            ids_vistos_por_portal: dict[str, set[str]] = {}

            for scraper in scrapers:
                portal = scraper.PORTAL
                ids_vistos_por_portal[portal] = set()
                terminos_portal = terminos.get(portal, [])

                self._actualizar_estado(message=f"Scrapeando {portal}...")

                for termino in terminos_portal:
                    for oferta in scraper.buscar(termino):
                        total_procesadas += 1
                        oferta = scorer.evaluar(oferta)
                        ids_vistos_por_portal[portal].add(oferta.id_unico())
                        es_nueva = db.guardar(oferta)

                        if oferta.es_relevante:
                            ofertas_relevantes_corrida.append(oferta)
                            if es_nueva:
                                nuevas_relevantes.append(oferta)

                        self._actualizar_estado(total=total_procesadas)

                    scraper._esperar()

            # Limpieza de ofertas viejas
            eliminadas = 0
            if not mantener_viejas:
                for portal, ids_vistos in ids_vistos_por_portal.items():
                    if ids_vistos:
                        eliminadas += db.eliminar_no_vistas(ids_vistos, portal=portal)

            stats = db.contar()

            # Ordenar ofertas relevantes de la corrida por puntaje y limitar
            ofertas_destacadas = sorted(
                ofertas_relevantes_corrida,
                key=lambda o: o.puntos_relevancia,
                reverse=True,
            )[:50]

            # Enviar notificaciones con las ofertas relevantes encontradas
            # en esta corrida, no solo las nuevas. Así el usuario recibe el
            # resumen aunque las ofertas ya estuvieran en la base de datos.
            if notificar and ofertas_destacadas:
                Notificador(config).notificar_nuevas(ofertas_destacadas)

            self._actualizar_estado(
                status="completed",
                message="Scraping finalizado correctamente.",
                finished_at=datetime.now(),
                total=total_procesadas,
                nuevas=len(nuevas_relevantes),
                eliminadas=eliminadas,
                relevantes=stats["relevantes"],
                ofertas=[o.model_dump() for o in ofertas_destacadas],
            )

        except Exception as e:
            self._actualizar_estado(
                status="error",
                message=f"Error durante el scraping: {str(e)}",
                finished_at=datetime.now(),
            )
        finally:
            if self._callback_finalizado:
                try:
                    self._callback_finalizado()
                except Exception:
                    pass

    def esperar(self, timeout: float | None = None):
        """Espera a que el hilo de scraping termine."""
        if self._hilo and self._hilo.is_alive():
            self._hilo.join(timeout=timeout)
