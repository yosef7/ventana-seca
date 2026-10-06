"""Gemma, servido en local por Ollama, elige una ventana según lo que pide la persona.

Gemma solo puede devolver la letra de una ventana calculada y objetos de una lista
cerrada. Si no responde o devuelve algo fuera de la lista, decide la regla fija.
"""

import json
from dataclasses import dataclass
from urllib.request import Request, urlopen

from .lugares import Lugar
from .tarjeta import dia_es, hora_es, mm_es
from .ventanas import Ventana

MODELO = "gemma4:e2b"
OLLAMA = "http://127.0.0.1:11434"
EQUIPO = ("agua", "gorra", "bloqueador", "repelente", "capa de lluvia", "linterna",
          "ropa de cambio", "zapatos con agarre")
MOTIVO_MAX = 220

INSTRUCCIONES = """Eres Ventana seca. Ayudas a una persona en Ciudad de Panamá a salir \
al aire libre en temporada de lluvias. Recibes ventanas ya calculadas con su pronóstico \
y lo que la persona prefiere. Elige UNA ventana por su letra: la que mejor equilibre \
poca lluvia con lo que la persona pide. Explica el motivo en una o dos frases cortas, en \
español, hablándole de tú. No repitas cifras ni inventes datos que no estén en la lista. \
Elige de 0 a 4 objetos para llevar, solo de la lista permitida."""


@dataclass(frozen=True)
class Eleccion:
    letra: str
    motivo: str
    llevar: tuple[str, ...]
    por_gemma: bool


def llamar_ollama(cuerpo: dict, timeout: float = 120) -> dict:
    peticion = Request(f"{OLLAMA}/api/chat", data=json.dumps(cuerpo).encode(),
                       headers={"Content-Type": "application/json"})
    with urlopen(peticion, timeout=timeout) as respuesta:
        return json.load(respuesta)


def describir(v: Ventana) -> str:
    return (f"{v.letra}: {dia_es(v.inicio)}, de {hora_es(v.inicio)} a {hora_es(v.fin)} · "
            f"lluvia hasta {v.lluvia_pct} % ({mm_es(v.lluvia_mm)}) · sensación hasta "
            f"{v.sensacion_max:.0f} °C · UV hasta {v.uv_max:.0f} · puntaje {v.puntaje}/100")


def pedido(candidatas: list[Ventana], lugar: Lugar, preferencia: str, modelo: str) -> dict:
    letras = [v.letra for v in candidatas]
    usuario = "\n".join([
        f"Lugar: {lugar.nombre} ({lugar.actividad}).",
        "Ventanas:",
        *(describir(v) for v in candidatas),
        f"Lo que prefiere la persona: {preferencia.strip() or 'sin preferencia, la más seca'}",
        f"Objetos permitidos: {', '.join(EQUIPO)}.",
    ])
    esquema = {
        "type": "object",
        "properties": {
            "letra": {"type": "string", "enum": letras},
            "motivo": {"type": "string"},
            "llevar": {"type": "array", "items": {"type": "string", "enum": list(EQUIPO)}},
        },
        "required": ["letra", "motivo", "llevar"],
    }
    return {
        "model": modelo,
        "stream": False,
        "format": esquema,
        "options": {"temperature": 0.2},
        "messages": [
            {"role": "system", "content": INSTRUCCIONES},
            {"role": "user", "content": usuario},
        ],
    }


def imprescindibles(v: Ventana, lugar: Lugar) -> set[str]:
    """Lo que se lleva siempre, decida lo que decida el modelo."""
    llevar = {"agua"}
    if v.lluvia_pct >= 30:
        llevar.add("capa de lluvia")
    if v.uv_max >= 6:
        llevar |= {"gorra", "bloqueador"}
    if lugar.bosque:
        llevar.add("repelente")
    if v.inicio.hour < 6 or v.fin.hour >= 18:
        llevar.add("linterna")
    return llevar


def por_regla(candidatas: list[Ventana]) -> Ventana:
    return max(candidatas, key=lambda v: (v.puntaje, -v.inicio.timestamp()))


def elegir(candidatas: list[Ventana], lugar: Lugar, preferencia: str = "",
           modelo: str = MODELO, cliente=llamar_ollama, usar_ia: bool = True) -> Eleccion:
    por_letra = {v.letra: v for v in candidatas}
    letra, motivo, sugeridos, por_gemma = None, "", set(), False

    if usar_ia:
        try:
            respuesta = cliente(pedido(candidatas, lugar, preferencia, modelo))
            datos = json.loads(respuesta["message"]["content"])
            if datos.get("letra") in por_letra:
                letra = datos["letra"]
                motivo = " ".join(str(datos.get("motivo", "")).split())[:MOTIVO_MAX]
                sugeridos = {o for o in datos.get("llevar", []) if o in EQUIPO}
                por_gemma = True
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass

    if letra is None:
        letra = por_regla(candidatas).letra
    elegida = por_letra[letra]
    if not motivo:
        motivo = ("Es la ventana con menos lluvia y calor del pronóstico."
                  if elegida.buena else
                  "Ninguna ventana se ve seca de verdad; esta es la menos mala.")
    llevar = sugeridos | imprescindibles(elegida, lugar)
    return Eleccion(letra, motivo, tuple(o for o in EQUIPO if o in llevar), por_gemma)
