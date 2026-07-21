"""
Motor de relevancia de ofertas de empleo.

Las palabras clave se configuran en config.yaml. Ver README.md para
personalizar el perfil de búsqueda.
"""

import re
from core.models import OfertaEmpleo


class Scorer:
    """Calcula la relevancia de una oferta según el perfil configurado."""

    def __init__(
        self,
        obligatorias: list[str],
        positivas: dict[str, int],
        negativas: dict[str, int],
        umbral: int,
        stack_titulo: list[str] | None = None,
        bonus_titulo_puntos: int = 3,
    ):
        self.obligatorias = [self._normalizar(p) for p in obligatorias]
        self.positivas = {self._normalizar(k): v for k, v in positivas.items()}
        self.negativas = {self._normalizar(k): v for k, v in negativas.items()}
        self.umbral = umbral
        self.stack_titulo = [self._normalizar(p) for p in (stack_titulo or [])]
        self.bonus_titulo_puntos = bonus_titulo_puntos

    @staticmethod
    def _normalizar(texto: str) -> str:
        return texto.lower().strip()

    def _contiene_frase(self, texto: str, frase: str) -> bool:
        """Busca una frase completa dentro de un texto normalizado."""
        return frase in self._normalizar(texto)

    def evaluar(self, oferta: OfertaEmpleo) -> OfertaEmpleo:
        texto_completo = (
            f"{oferta.titulo} {oferta.empresa} {oferta.ubicacion} "
            f"{oferta.modalidad} {oferta.descripcion}"
        )
        texto_normalizado = self._normalizar(texto_completo)

        # 1. Debe cumplir al menos una palabra obligatoria
        cumple_obligatoria = any(
            self._contiene_frase(texto_completo, palabra) for palabra in self.obligatorias
        )

        puntos = 0
        palabras_detectadas = []

        if cumple_obligatoria:
            puntos += 5  # Bonus base por ser remoto/teletrabajo/home office

        # 2. Sumar puntos positivos
        for palabra, valor in self.positivas.items():
            if palabra in texto_normalizado:
                puntos += valor
                palabras_detectadas.append(f"+{palabra} ({valor})")

        # 3. Restar puntos negativos
        for palabra, valor in self.negativas.items():
            if palabra in texto_normalizado:
                puntos += valor  # valor ya es negativo
                palabras_detectadas.append(f"{palabra} ({valor})")

        # 4. Bonus por palabras del stack exacto en el título
        titulo_normalizado = self._normalizar(oferta.titulo)
        for palabra in self.stack_titulo:
            if palabra in titulo_normalizado:
                puntos += self.bonus_titulo_puntos
                palabras_detectadas.append(f"titulo:{palabra} (+{self.bonus_titulo_puntos})")

        oferta.puntos_relevancia = max(0, puntos)
        oferta.palabras_detectadas = palabras_detectadas
        oferta.es_relevante = cumple_obligatoria and puntos >= self.umbral

        return oferta
