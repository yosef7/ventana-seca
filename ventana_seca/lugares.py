"""Lugares públicos para salir en Ciudad de Panamá.

Las coordenadas son aproximadas y corresponden al lugar, no a la persona: el
pronóstico se pide para el parque, así que tu ubicación nunca sale del equipo.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Lugar:
    clave: str
    nombre: str
    latitud: float
    longitud: float
    actividad: str
    # Sendero con bosque: mosquitos y barro después de la lluvia.
    bosque: bool = False


LUGARES = {
    lugar.clave: lugar
    for lugar in (
        Lugar("metropolitano", "Parque Natural Metropolitano", 8.9940, -79.5435,
              "sendero en bosque tropical", bosque=True),
        Lugar("camino-de-cruces", "Parque Nacional Camino de Cruces", 9.0300, -79.5700,
              "sendero histórico en bosque", bosque=True),
        Lugar("ancon", "Cerro Ancón", 8.9615, -79.5475,
              "subida corta con vista a la ciudad", bosque=True),
        Lugar("cinta-costera", "Cinta Costera", 8.9720, -79.5270,
              "caminar o correr junto al mar"),
        Lugar("amador", "Calzada de Amador", 8.9170, -79.5330,
              "caminar, correr o pedalear entre islas"),
    )
}
