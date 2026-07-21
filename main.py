#!/usr/bin/env python3
"""
Buscatrabajo - Agregador de ofertas de empleo remoto/freelance.

Por defecto levanta el servidor web. Usa --cli para ejecutar scraping en consola.

Uso:
    python main.py                              # Levanta servidor web
    python main.py --cli                        # Ejecuta scraping en consola
    python main.py --cli --web                  # Scrapea en consola y luego levanta web
    python main.py --web-only                   # Solo levanta servidor web

Documentación:
    - README.md              Guía rápida e instalación.
    - docs/guia_usuario.md   Uso de la interfaz web.
    - docs/arquitectura.md   Arquitectura y flujo de datos.
    - docs/telegram.md       Configuración de notificaciones.
    - docs/api.md            Endpoints de la API interna.
    - docs/desarrollo.md     Cómo extender el proyecto.
"""

import argparse
import csv
from pathlib import Path

import yaml

from core.database import Database
from core.models import OfertaEmpleo
from core.notificador import Notificador
from core.scorer import Scorer
from core.worker import modalidades_activas
from scrapers.elempleo import ElempleoScraper
from scrapers.infojobs import InfojobsScraper


CONFIG_PATH = Path(__file__).parent / "config.yaml"


def cargar_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ejecutar_scraping(config: dict, args) -> Database:
    db = Database()
    bonus_config = config.get("bonus_titulo", {})
    scorer = Scorer(
        obligatorias=modalidades_activas(config),
        positivas=config["palabras_clave_positivas"],
        negativas=config["palabras_clave_negativas"],
        umbral=config["umbral_relevancia"],
        stack_titulo=bonus_config.get("palabras", []),
        bonus_titulo_puntos=bonus_config.get("puntos", 3),
    )

    scrapers_disponibles = {
        "elempleo": ElempleoScraper(config),
        "infojobs": InfojobsScraper(config),
    }

    portales = [args.portal] if args.portal else list(scrapers_disponibles.keys())
    scrapers = [scrapers_disponibles[p] for p in portales if p in scrapers_disponibles]

    nuevas_relevantes: list[OfertaEmpleo] = []
    total_procesadas = 0
    ids_vistos_por_portal: dict[str, set[str]] = {}

    for scraper in scrapers:
        portal = scraper.PORTAL
        ids_vistos_por_portal[portal] = set()
        terminos = config["busquedas"].get(portal, [])

        for termino in terminos:
            for oferta in scraper.buscar(termino):
                total_procesadas += 1
                oferta = scorer.evaluar(oferta)
                ids_vistos_por_portal[portal].add(oferta.id_unico())
                es_nueva = db.guardar(oferta)
                if es_nueva and oferta.es_relevante:
                    nuevas_relevantes.append(oferta)

            scraper._esperar()

    # Limpieza de ofertas viejas
    eliminadas = 0
    if not args.mantener_viejas:
        for portal, ids_vistos in ids_vistos_por_portal.items():
            if ids_vistos:
                eliminadas += db.eliminar_no_vistas(ids_vistos, portal=portal)

    # Resumen
    stats = db.contar()
    print("\n=== RESUMEN ===")
    print(f"Ofertas procesadas en esta ejecución: {total_procesadas}")
    print(f"Nuevas ofertas relevantes: {len(nuevas_relevantes)}")
    if eliminadas > 0:
        print(f"Ofertas viejas eliminadas: {eliminadas}")
    print(f"Total en base de datos: {stats['total']} ({stats['relevantes']} relevantes)")

    if nuevas_relevantes:
        print("\n--- TOP OFERTAS NUEVAS ---")
        for oferta in sorted(nuevas_relevantes, key=lambda o: o.puntos_relevancia, reverse=True)[:10]:
            print(f"\n⭐ {oferta.puntos_relevancia} | {oferta.titulo}")
            print(f"   🏢 {oferta.empresa or 'No especificada'} | 🌎 {oferta.modalidad}")
            print(f"   🔗 {oferta.url}")
            print(f"   🔑 {', '.join(oferta.palabras_detectadas[:5])}")

    if args.notify and nuevas_relevantes:
        Notificador(config).notificar_nuevas(nuevas_relevantes)

    if args.exportar:
        exportar_csv(db, args.exportar)
        print(f"\n📄 Exportadas ofertas relevantes a: {args.exportar}")

    return db


def exportar_csv(db: Database, ruta: Path):
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Portal", "Título", "Empresa", "Ubicación", "Modalidad",
            "Salario", "URL", "Puntos", "Palabras clave", "Fecha publicación"
        ])
        for row in db.obtener_relevantes():
            writer.writerow([
                row["portal"], row["titulo"], row["empresa"], row["ubicacion"],
                row["modalidad"], row["salario"], row["url"], row["puntos_relevancia"],
                row["palabras_detectadas"], row["fecha_publicacion"]
            ])


def main():
    parser = argparse.ArgumentParser(description="Busca ofertas de empleo remoto/freelance")
    parser.add_argument(
        "--config", type=Path, default=CONFIG_PATH, help="Ruta al archivo de configuración"
    )
    parser.add_argument(
        "--cli", action="store_true",
        help="Ejecutar scraping en consola en lugar de levantar el servidor web"
    )
    parser.add_argument(
        "--exportar", type=Path, default=None, help="Exportar resultados relevantes a CSV"
    )
    parser.add_argument(
        "--notify", action="store_true", help="Enviar notificaciones de ofertas nuevas"
    )
    parser.add_argument(
        "--portal", choices=["elempleo", "infojobs"], default=None, help="Ejecutar solo un portal"
    )
    parser.add_argument(
        "--web", action="store_true", help="Levantar servidor web después de scrapear (solo con --cli)"
    )
    parser.add_argument(
        "--web-only", action="store_true", help="Solo levantar servidor web (sin scrapear)"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host del servidor web (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Puerto del servidor web (default: 5000)"
    )
    parser.add_argument(
        "--mantener-viejas", action="store_true",
        help="No eliminar ofertas que no aparecieron en esta ejecución"
    )
    args = parser.parse_args()

    if args.web_only:
        iniciar_web(args)
        return

    if args.cli:
        config = cargar_config(args.config)
        ejecutar_scraping(config, args)
        if args.web:
            iniciar_web(args)
        return

    # Comportamiento por defecto: levantar servidor web
    iniciar_web(args)


def iniciar_web(args):
    from web.server import iniciar_servidor
    iniciar_servidor(host=args.host, port=args.port, config_path=args.config)


if __name__ == "__main__":
    main()
