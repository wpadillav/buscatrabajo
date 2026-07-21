"""
Extracción de texto de hojas de vida (CV/HV) para análisis con IA.

Soporta PDF, DOCX y TXT. El archivo se procesa en memoria; no se guarda
en disco.
"""

import io

EXTENSIONES_SOPORTADAS = {".pdf", ".docx", ".txt"}


def extraer_texto(nombre_archivo: str, contenido: bytes) -> str:
    """Extrae el texto plano de un archivo de CV. Lanza ValueError con un
    mensaje claro si el formato no es soportado o no hay texto extraíble."""
    extension = _extension(nombre_archivo)

    if extension == ".txt":
        texto = _extraer_txt(contenido)
    elif extension == ".pdf":
        texto = _extraer_pdf(contenido)
    elif extension == ".docx":
        texto = _extraer_docx(contenido)
    else:
        soportadas = ", ".join(sorted(EXTENSIONES_SOPORTADAS))
        raise ValueError(f"Formato '{extension or '(sin extensión)'}' no soportado. Usa: {soportadas}.")

    texto = texto.strip()
    if not texto:
        raise ValueError(
            "No se pudo extraer texto del archivo. "
            "Si es un PDF escaneado (imagen), conviértelo a PDF con texto o DOCX."
        )
    return texto


def _extension(nombre_archivo: str) -> str:
    punto = nombre_archivo.rfind(".")
    return nombre_archivo[punto:].lower() if punto != -1 else ""


def _extraer_txt(contenido: bytes) -> str:
    return contenido.decode("utf-8", errors="replace")


def _extraer_pdf(contenido: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(contenido))
    return "\n".join(pagina.extract_text() or "" for pagina in reader.pages)


def _extraer_docx(contenido: bytes) -> str:
    import docx

    documento = docx.Document(io.BytesIO(contenido))
    return "\n".join(parrafo.text for parrafo in documento.paragraphs)
