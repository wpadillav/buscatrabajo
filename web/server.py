"""
Servidor web para controlar y visualizar el scraping de ofertas de empleo.

Rutas principales:
    /                       Dashboard de ofertas guardadas.
    /scrape                 Panel para configurar y ejecutar scraping.
    /api/scrape/*           API para controlar el scraping.
    /api/notificaciones/*   API para verificar y probar notificaciones.

Ver docs/guia_usuario.md y docs/api.md para más información.
"""

from pathlib import Path

import yaml
from flask import Flask, jsonify, render_template, request

from core.database import Database
from core.telegram import telegram_configurado, obtener_info_bot, enviar_mensaje_prueba
from core.worker import ScrapingWorker


def cargar_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parsear_puntajes(valor) -> dict[str, int] | None:
    """Valida un diccionario palabra -> puntos recibido por la API."""
    if not isinstance(valor, dict):
        return None
    try:
        return {str(k).strip(): int(v) for k, v in valor.items() if str(k).strip()}
    except (TypeError, ValueError):
        return None


def crear_app(config_path: Path | None = None, db_path: Path | None = None) -> Flask:
    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"

    app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))

    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    db = Database(db_path) if db_path else Database()
    worker = ScrapingWorker()

    @app.route("/")
    def index():
        portal = request.args.get("portal", "").strip()
        busqueda = request.args.get("q", "").strip().lower()
        solo_relevantes = request.args.get("relevantes", "1") == "1"
        pagina = request.args.get("pagina", 1, type=int)
        por_pagina = 20

        ofertas, total = db.filtrar(
            portal=portal or None,
            busqueda=busqueda or None,
            solo_relevantes=solo_relevantes,
            pagina=pagina,
            por_pagina=por_pagina,
        )

        total_paginas = (total + por_pagina - 1) // por_pagina

        return render_template(
            "index.html",
            ofertas=ofertas,
            total=total,
            portal=portal,
            busqueda=busqueda,
            solo_relevantes=solo_relevantes,
            pagina=pagina,
            total_paginas=total_paginas,
            portales=db.portales(),
        )

    @app.route("/scrape")
    def scrape_page():
        """Página de control para configurar y ejecutar el scraping."""
        config = cargar_config(config_path)
        estado = worker.obtener_estado()
        telegram_ok = telegram_configurado(config)
        return render_template(
            "scrape.html",
            config=config,
            estado=estado,
            telegram_configurado=telegram_ok,
        )

    @app.route("/api/cv/analizar", methods=["POST"])
    def api_cv_analizar():
        """Analiza una HV/CV con IA y devuelve el perfil de búsqueda generado."""
        from core.cv import extraer_texto
        from core.perfil_ia import ErrorProveedorIA, analizar_cv

        archivo = request.files.get("archivo")
        if not archivo or not archivo.filename:
            return jsonify({"ok": False, "message": "Debes adjuntar un archivo (PDF, DOCX o TXT)."}), 400

        contenido = archivo.read()
        if len(contenido) > 5 * 1024 * 1024:
            return jsonify({"ok": False, "message": "El archivo supera el límite de 5 MB."}), 400

        try:
            texto = extraer_texto(archivo.filename, contenido)
        except ValueError as e:
            return jsonify({"ok": False, "message": str(e)}), 400

        config = cargar_config(config_path)
        cfg_config = config.get("ia", {})
        cfg_ia = {
            "proveedor": request.form.get("proveedor") or cfg_config.get("proveedor", "gemini"),
            "api_key": request.form.get("api_key") or cfg_config.get("api_key", ""),
            "url_base": request.form.get("url_base") or cfg_config.get("url_base", ""),
            "modelo": request.form.get("modelo") or cfg_config.get("modelo", ""),
        }

        try:
            perfil = analizar_cv(texto, cfg_ia)
        except ErrorProveedorIA as e:
            return jsonify({"ok": False, "message": str(e)}), 502

        return jsonify({"ok": True, "perfil": perfil})

    @app.route("/api/scrape/status")
    def api_scrape_status():
        """Devuelve el estado actual del worker de scraping."""
        estado = worker.obtener_estado()
        return jsonify({
            "status": estado.status,
            "message": estado.message,
            "started_at": estado.started_at.isoformat() if estado.started_at else None,
            "finished_at": estado.finished_at.isoformat() if estado.finished_at else None,
            "total": estado.total,
            "nuevas": estado.nuevas,
            "eliminadas": estado.eliminadas,
            "relevantes": estado.relevantes,
        })

    @app.route("/api/scrape/results")
    def api_scrape_results():
        """Devuelve las ofertas relevantes encontradas en la última ejecución."""
        estado = worker.obtener_estado()
        return jsonify({
            "status": estado.status,
            "ofertas": estado.ofertas,
        })

    @app.route("/api/scrape/start", methods=["POST"])
    def api_scrape_start():
        """Inicia una nueva ejecución de scraping con la configuración recibida."""
        if worker.esta_corriendo():
            return jsonify({
                "ok": False,
                "message": "Ya hay un scraping en ejeción. Espera a que termine.",
            }), 409

        data = request.get_json() or {}
        config = cargar_config(config_path)

        portales = data.get("portales", ["elempleo", "infojobs"])
        if not isinstance(portales, list):
            portales = [portales]

        terminos = data.get("terminos", config.get("busquedas", {}))
        mantener_viejas = bool(data.get("mantener_viejas", False))
        umbral = data.get("umbral")
        if umbral is not None:
            umbral = int(umbral)
        notificar = bool(data.get("notificar", False))

        stack_titulo = data.get("stack_titulo")
        if stack_titulo is not None and not isinstance(stack_titulo, list):
            stack_titulo = [stack_titulo]

        positivas = _parsear_puntajes(data.get("palabras_positivas"))
        negativas = _parsear_puntajes(data.get("palabras_negativas"))

        # Modalidades seleccionadas -> palabras obligatorias según config.yaml
        modalidades = data.get("modalidades")
        obligatorias = None
        if isinstance(modalidades, list):
            cfg_modalidades = config.get("modalidades", {})
            obligatorias = []
            for nombre in modalidades:
                modalidad = cfg_modalidades.get(str(nombre))
                if modalidad:
                    obligatorias.extend(modalidad.get("palabras", []))

        iniciado = worker.iniciar(
            config=config,
            portales=portales,
            terminos=terminos,
            mantener_viejas=mantener_viejas,
            umbral=umbral,
            notificar=notificar,
            stack_titulo=stack_titulo,
            positivas=positivas,
            negativas=negativas,
            obligatorias=obligatorias,
        )

        if not iniciado:
            return jsonify({
                "ok": False,
                "message": "No se pudo iniciar el scraping.",
            }), 500

        return jsonify({
            "ok": True,
            "message": "Scraping iniciado correctamente.",
        })

    @app.route("/api/notificaciones/telegram/test", methods=["POST"])
    def api_telegram_test():
        """Envía un mensaje de prueba al chat de Telegram configurado."""
        config = cargar_config(config_path)
        cfg = config.get("notificaciones", {}).get("telegram", {})
        bot_token = cfg.get("bot_token")
        chat_id = cfg.get("chat_id")

        if not bot_token or not chat_id:
            return jsonify({
                "ok": False,
                "message": "Telegram no está configurado. Revisa config.yaml.",
            }), 400

        try:
            info = obtener_info_bot(bot_token)
            if not info.get("ok"):
                return jsonify({
                    "ok": False,
                    "message": f"Token inválido: {info.get('description', 'Error desconocido')}",
                }), 400

            enviar_mensaje_prueba(bot_token, chat_id)
            return jsonify({
                "ok": True,
                "message": f"Mensaje de prueba enviado correctamente al chat {chat_id}.",
                "bot": info.get("result", {}).get("username"),
            })
        except Exception as e:
            return jsonify({
                "ok": False,
                "message": f"Error enviando mensaje de prueba: {str(e)}",
            }), 500

    @app.route("/api/notificaciones/telegram/status")
    def api_telegram_status():
        """Devuelve si Telegram está configurado."""
        config = cargar_config(config_path)
        return jsonify({
            "configurado": telegram_configurado(config),
        })

    @app.route("/oferta/<id_unico>")
    def detalle(id_unico: str):
        oferta = db.obtener_por_id(id_unico)
        if not oferta:
            return render_template("404.html"), 404
        return render_template("detalle.html", oferta=oferta)

    return app


def iniciar_servidor(
    host: str = "127.0.0.1",
    port: int = 5000,
    debug: bool = False,
    config_path: Path | None = None,
    db_path: Path | None = None,
):
    app = crear_app(config_path=config_path, db_path=db_path)
    print(f"\n🌐 Servidor web disponible en: http://{host}:{port}")
    print("Panel de control: http://{host}:{port}/scrape".format(host=host, port=port))
    print("Presiona Ctrl+C para detener.\n")
    app.run(host=host, port=port, debug=debug, use_reloader=False)
