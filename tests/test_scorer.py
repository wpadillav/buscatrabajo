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
