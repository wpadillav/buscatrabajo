import io

import pytest

from core.cv import extraer_texto


def test_extraer_txt():
    texto = extraer_texto("hv.txt", "Juan Pérez\nSoporte técnico".encode("utf-8"))
    assert "Juan Pérez" in texto
    assert "Soporte técnico" in texto


def test_extraer_docx():
    import docx

    buffer = io.BytesIO()
    documento = docx.Document()
    documento.add_paragraph("María Gómez - Desarrolladora Junior")
    documento.save(buffer)

    texto = extraer_texto("hv.docx", buffer.getvalue())
    assert "Desarrolladora Junior" in texto


def test_extension_no_soportada():
    with pytest.raises(ValueError, match="no soportado"):
        extraer_texto("hv.xlsx", b"datos")


def test_archivo_sin_texto():
    with pytest.raises(ValueError, match="No se pudo extraer texto"):
        extraer_texto("hv.txt", b"   ")
