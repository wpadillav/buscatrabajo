from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OfertaEmpleo(BaseModel):
    """Modelo de una oferta de empleo detectada por el scraper."""

    id_externo: str = Field(..., description="Identificador único de la oferta en el portal")
    portal: str = Field(..., description="Nombre del portal de empleo")
    titulo: str = Field(..., description="Título de la vacante")
    empresa: str = Field(default="", description="Nombre de la empresa")
    ubicacion: str = Field(default="", description="Ubicación o modalidad")
    url: str = Field(..., description="URL directa de la oferta")
    descripcion: str = Field(default="", description="Resumen o descripción completa")
    fecha_publicacion: Optional[datetime] = Field(default=None, description="Fecha de publicación si está disponible")
    salario: str = Field(default="", description="Rango salarial si está disponible")
    modalidad: str = Field(default="", description="Remoto/híbrido/presencial")

    # Campos calculados por el motor de scoring
    puntos_relevancia: int = Field(default=0, description="Puntaje de ajuste al perfil")
    palabras_detectadas: list[str] = Field(default_factory=list, description="Palabras clave encontradas")
    es_relevante: bool = Field(default=False, description="Supera el umbral de relevancia")

    def id_unico(self) -> str:
        """Genera un ID único global para deduplicación."""
        return f"{self.portal}:{self.id_externo}"
