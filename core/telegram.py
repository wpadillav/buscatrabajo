"""
Utilidades para verificar y probar la configuración de Telegram.

Ver docs/telegram.md para la guía de configuración paso a paso.
"""

import httpx


def telegram_configurado(config: dict) -> bool:
    cfg = config.get("notificaciones", {}).get("telegram", {})
    return bool(cfg.get("bot_token") and cfg.get("chat_id"))


def obtener_info_bot(bot_token: str) -> dict:
    """Obtiene información del bot para validar el token."""
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = httpx.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def enviar_mensaje_prueba(bot_token: str, chat_id: str) -> dict:
    """Envía un mensaje de prueba al chat configurado."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = httpx.post(
        url,
        json={
            "chat_id": chat_id,
            "text": "✅ *Buscatrabajo*: las notificaciones de Telegram están configuradas correctamente.",
            "parse_mode": "Markdown",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
