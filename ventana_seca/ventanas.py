"""Cálculo de las ventanas candidatas. Aquí no interviene la IA: solo números."""

import string
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from .pronostico import Hora

# Por encima de esta sensación térmica, salir a mediodía en Panamá ya cuesta.
CALOR_C = 32
UV_ALTO = 7
UMBRAL_BUENA = 60
# Dos ventanas del mismo día deben estar separadas para que haya una opción real.
SEPARACION = timedelta(hours=3)


@dataclass(frozen=True)
class Ventana:
    letra: str
    inicio: datetime
    fin: datetime
    lluvia_pct: int
    lluvia_mm: float
    sensacion_max: float
    uv_max: float
    puntaje: int

    @property
    def buena(self) -> bool:
        return self.puntaje >= UMBRAL_BUENA


def puntuar(tramo: list[Hora]) -> Ventana:
    lluvia_pct = max(h.lluvia_pct for h in tramo)
    lluvia_mm = round(sum(h.lluvia_mm for h in tramo), 1)
    sensacion = max(h.sensacion_c for h in tramo)
    uv = max(h.uv for h in tramo)
    castigo = (lluvia_pct + 15 * lluvia_mm + 4 * max(0, sensacion - CALOR_C)
               + 3 * max(0, uv - UV_ALTO))
    return Ventana("", tramo[0].inicio, tramo[-1].inicio + timedelta(hours=1),
                   lluvia_pct, lluvia_mm, sensacion, uv, max(0, round(100 - castigo)))


def candidatas(horas: list[Hora], duracion_h: int, ahora: datetime,
               maximo: int = 5, por_dia: int = 2) -> list[Ventana]:
    """Las mejores ventanas de día, separadas entre sí, en orden cronológico.

    Se dejan hasta `por_dia` por fecha para que haya de dónde escoger: una
    mañana y una tarde, por ejemplo, aunque la tarde puntúe menos.
    """
    horas = sorted(horas, key=lambda h: h.inicio)
    todas = []
    for i in range(len(horas) - duracion_h + 1):
        tramo = horas[i:i + duracion_h]
        seguidas = all(b.inicio - a.inicio == timedelta(hours=1)
                       for a, b in zip(tramo, tramo[1:]))
        if seguidas and tramo[0].inicio >= ahora and all(h.de_dia for h in tramo):
            todas.append(puntuar(tramo))

    elegidas: list[Ventana] = []
    for v in sorted(todas, key=lambda v: (-v.puntaje, v.inicio)):
        if len(elegidas) == maximo:
            break
        mismo_dia = sum(e.inicio.date() == v.inicio.date() for e in elegidas)
        solapa = any(v.inicio < e.fin + SEPARACION and e.inicio < v.fin + SEPARACION
                     for e in elegidas)
        if mismo_dia < por_dia and not solapa:
            elegidas.append(v)

    elegidas.sort(key=lambda v: v.inicio)
    return [replace(v, letra=letra) for letra, v in zip(string.ascii_uppercase, elegidas)]
