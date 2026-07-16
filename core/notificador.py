"""
Envío de notificaciones de ofertas relevantes por Telegram y email.

Para configurar Telegram, ver docs/telegram.md.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

from core.models import OfertaEmpleo


class Notificador:
    """Envía alertas de ofertas relevantes por Telegram o email."""

    def __init__(self, config: dict):
        self.config = config.get("notificaciones", {})

    def telegram_configurado(self) -> bool:
        cfg = self.config.get("telegram", {})
        return bool(cfg.get("bot_token") and cfg.get("chat_id"))

    def email_configurado(self) -> bool:
        cfg = self.config.get("email", {})
        return all([
            cfg.get("smtp_host"),
            cfg.get("usuario"),
            cfg.get("password"),
            cfg.get("destinatario"),
        ])

    def notificar_nuevas(self, ofertas: list[OfertaEmpleo]):
        if not ofertas:
            return

        self._notificar_telegram(ofertas)
        self._notificar_email(ofertas)

    def _notificar_telegram(self, ofertas: list[OfertaEmpleo]):
        cfg = self.config.get("telegram", {})
        bot_token = cfg.get("bot_token")
        chat_id = cfg.get("chat_id")
        if not bot_token or not chat_id:
            return

        mensaje = self._construir_mensaje_telegram(ofertas)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            response = httpx.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": mensaje,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            response.raise_for_status()
            resultado = response.json()
            if not resultado.get("ok"):
                print(f"[Telegram] Error en respuesta: {resultado}")
        except Exception as e:
            print(f"[Telegram] Error enviando mensaje: {e}")

    def _construir_mensaje_telegram(self, ofertas: list[OfertaEmpleo]) -> str:
        lineas = [
            "🔔 *Ofertas relevantes encontradas*",
            f"Se encontraron *{len(ofertas)}* oferta(s) que se ajustan a tu perfil:\n",
        ]

        for i, o in enumerate(ofertas[:10], start=1):
            detalles = []
            if o.empresa:
                detalles.append(f"🏢 {o.empresa}")
            if o.modalidad and o.modalidad != "No especificada":
                detalles.append(f"🌎 {o.modalidad}")
            if o.ubicacion:
                detalles.append(f"📍 {o.ubicacion}")

            lineas.append(
                f"*{i}. {o.titulo}*\n"
                f"⭐ Relevancia: {o.puntos_relevancia} pts\n"
                f"{' | '.join(detalles)}\n"
                f"🔗 [Ver oferta]({o.url})"
            )

        if len(ofertas) > 10:
            lineas.append(f"\n_Y {len(ofertas) - 10} oferta(s) más en el dashboard._")

        return "\n\n".join(lineas)

    def _notificar_email(self, ofertas: list[OfertaEmpleo]):
        cfg = self.config.get("email", {})
        smtp_host = cfg.get("smtp_host")
        usuario = cfg.get("usuario")
        password = cfg.get("password")
        destinatario = cfg.get("destinatario")

        if not all([smtp_host, usuario, password, destinatario]):
            return

        html = self._generar_html(ofertas)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{len(ofertas)} oferta(s) relevante(s) encontrada(s)"
        msg["From"] = usuario
        msg["To"] = destinatario
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(smtp_host, cfg.get("smtp_port", 587)) as server:
                server.starttls()
                server.login(usuario, password)
                server.sendmail(usuario, destinatario, msg.as_string())
        except Exception as e:
            print(f"[Email] Error enviando mensaje: {e}")

    def _generar_html(self, ofertas: list[OfertaEmpleo]) -> str:
        filas = ""
        for o in ofertas:
            filas += f"""
            <tr>
                <td>{o.puntos_relevancia}</td>
                <td><a href="{o.url}">{o.titulo}</a></td>
                <td>{o.empresa}</td>
                <td>{o.modalidad}</td>
                <td>{', '.join(o.palabras_detectadas[:5])}</td>
            </tr>
            """
        return f"""
        <html>
        <body>
            <h2>Ofertas relevantes encontradas</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><th>Puntos</th><th>Título</th><th>Empresa</th><th>Modalidad</th><th>Palabras clave</th></tr>
                {filas}
            </table>
        </body>
        </html>
        """
