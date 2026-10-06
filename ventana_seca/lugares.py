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
        Lugar("5-de-mayo", "Plaza 5 de Mayo", 8.9620, -79.5415,
              "tramo a pie en el centro, junto al metro"),
        Lugar("costa-del-este", "Costa del Este", 9.0110, -79.4700,
              "caminar por el Parque Costa del Este o junto al mar"),
    )
}


def buscar(texto: str) -> Lugar:
    """Acepta la clave o el nombre: «costa-del-este», «Costa del Este», «5 de mayo»."""
    clave = "-".join(texto.lower().split())
    for lugar in LUGARES.values():
        if clave in (lugar.clave, "-".join(lugar.nombre.lower().split())):
            return lugar
    sin_prefijo = {"-".join(lugar.nombre.lower().split()[1:]): lugar
                   for lugar in LUGARES.values()}
    if clave in sin_prefijo:
        return sin_prefijo[clave]
    raise ValueError(f"No conozco «{texto}». Lugares: {', '.join(sorted(LUGARES))}.")
