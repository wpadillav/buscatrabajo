import pytest

from core.perfil_ia import (
    ErrorProveedorIA,
    _extraer_json,
    _validar_perfil,
    analizar_cv,
)


def test_extraer_json_plano():
    assert _extraer_json('{"a": 1}') == {"a": 1}


def test_extraer_json_con_markdown():
    texto = 'Aquí está el perfil:\n```json\n{"a": 1}\n```\nEspero que sirva.'
    assert _extraer_json(texto) == {"a": 1}


def test_extraer_json_invalido():
    with pytest.raises(ErrorProveedorIA):
        _extraer_json("no hay json aquí")


def test_validar_perfil_normaliza():
    datos = {
        "terminos": {"Elempleo": ["Soporte Remoto", 123, ""], "infojobs": "no-lista"},
        "modalidades": ["Remoto", "luna", "hibrido"],
        "palabras_positivas": {"Soporte": "8", "mala": "xyz", "neg": -5},
        "palabras_negativas": {"Senior": 10, "inglés": -8},
        "stack_titulo": ["Soporte", "", "Junior"],
    }
    perfil = _validar_perfil(datos)

    assert perfil["terminos"] == {"elempleo": ["soporte remoto"]}
    assert perfil["modalidades"] == ["remoto", "hibrido"]
    assert perfil["palabras_positivas"] == {"soporte": 8, "neg": 5}
    assert perfil["palabras_negativas"] == {"senior": -10, "inglés": -8}
    assert perfil["stack_titulo"] == ["soporte", "junior"]


def test_validar_perfil_vacio():
    perfil = _validar_perfil({})
    assert perfil == {
        "terminos": {},
        "modalidades": [],
        "palabras_positivas": {},
        "palabras_negativas": {},
        "stack_titulo": [],
    }


def test_analizar_cv_sin_api_key():
    with pytest.raises(ErrorProveedorIA, match="API key"):
        analizar_cv("texto del cv", {"proveedor": "gemini", "api_key": "", "modelo": "x", "url_base": ""})


def test_analizar_cv_sin_modelo():
    with pytest.raises(ErrorProveedorIA, match="modelo"):
        analizar_cv("texto del cv", {"proveedor": "gemini", "api_key": "k", "modelo": "", "url_base": ""})


def test_analizar_cv_proveedor_desconocido():
    with pytest.raises(ErrorProveedorIA, match="no soportado"):
        analizar_cv("texto del cv", {"proveedor": "claude", "api_key": "k", "modelo": "x", "url_base": ""})


def test_analizar_cv_local_sin_api_key_ok(monkeypatch):
    """Un endpoint local (Ollama) no requiere API key."""
    import core.perfil_ia as perfil_ia

    class RespuestaFalsa:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": '{"modalidades": ["remoto"]}'}}]}

    monkeypatch.setattr(perfil_ia.httpx, "post", lambda *a, **kw: RespuestaFalsa())

    perfil = analizar_cv(
        "texto del cv",
        {"proveedor": "openai", "api_key": "", "modelo": "llama3.1", "url_base": "http://localhost:11434/v1"},
    )
    assert perfil["modalidades"] == ["remoto"]
