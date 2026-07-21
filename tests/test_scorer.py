import pytest
from core.models import OfertaEmpleo
from core.scorer import Scorer


def test_oferta_relevante_remoto_devops():
    scorer = Scorer(
        obligatorias=["remoto"],
        positivas={"devops": 9, "linux": 8, "junior": 5},
        negativas={"senior": -10},
        umbral=8,
    )
    oferta = OfertaEmpleo(
        id_externo="1",
        portal="test",
        titulo="DevOps Junior Remoto",
        empresa="ACME",
        ubicacion="Madrid",
        url="https://example.com/1",
        descripcion="Buscamos DevOps junior con Linux y Docker.",
    )
    scorer.evaluar(oferta)
    assert oferta.es_relevante is True
    assert oferta.puntos_relevancia >= 8


def test_oferta_no_relevante_sin_remoto():
    scorer = Scorer(
        obligatorias=["remoto"],
        positivas={"devops": 9},
        negativas={},
        umbral=5,
    )
    oferta = OfertaEmpleo(
        id_externo="2",
        portal="test",
        titulo="DevOps presencial",
        empresa="ACME",
        ubicacion="Bogotá",
        url="https://example.com/2",
        descripcion="DevOps presencial.",
    )
    scorer.evaluar(oferta)
    assert oferta.es_relevante is False


def test_palabra_negativa_descarta():
    scorer = Scorer(
        obligatorias=["remoto"],
        positivas={"devops": 9},
        negativas={"senior": -10},
        umbral=8,
    )
    oferta = OfertaEmpleo(
        id_externo="3",
        portal="test",
        titulo="DevOps Senior Remoto",
        empresa="ACME",
        ubicacion="",
        url="https://example.com/3",
        descripcion="",
    )
    scorer.evaluar(oferta)
    assert oferta.puntos_relevancia < 8


def test_bonus_titulo_configurable():
    scorer = Scorer(
        obligatorias=["remoto"],
        positivas={},
        negativas={},
        umbral=8,
        stack_titulo=["helpdesk"],
        bonus_titulo_puntos=4,
    )
    oferta = OfertaEmpleo(
        id_externo="4",
        portal="test",
        titulo="Helpdesk remoto",
        empresa="ACME",
        ubicacion="",
        url="https://example.com/4",
        descripcion="",
    )
    scorer.evaluar(oferta)
    # 5 (bonus obligatoria) + 4 (bonus título) = 9
    assert oferta.puntos_relevancia == 9
    assert "titulo:helpdesk (+4)" in oferta.palabras_detectadas


def test_sin_stack_titulo_no_hay_bonus():
    scorer = Scorer(
        obligatorias=["remoto"],
        positivas={},
        negativas={},
        umbral=8,
    )
    oferta = OfertaEmpleo(
        id_externo="5",
        portal="test",
        titulo="Soporte remoto",
        empresa="ACME",
        ubicacion="",
        url="https://example.com/5",
        descripcion="",
    )
    scorer.evaluar(oferta)
    # Solo el bonus base por palabra obligatoria, sin bonus de título
    assert oferta.puntos_relevancia == 5
    assert oferta.palabras_detectadas == []


def test_modalidad_cuenta_como_palabra_obligatoria():
    scorer = Scorer(
        obligatorias=["híbrido"],
        positivas={"soporte": 7},
        negativas={},
        umbral=8,
    )
    oferta = OfertaEmpleo(
        id_externo="6",
        portal="test",
        titulo="Soporte técnico",
        empresa="ACME",
        ubicacion="Madrid",
        url="https://example.com/6",
        descripcion="",
        modalidad="Híbrido",
    )
    scorer.evaluar(oferta)
    # La palabra obligatoria está en el campo modalidad, no en el texto
    assert oferta.es_relevante is True
