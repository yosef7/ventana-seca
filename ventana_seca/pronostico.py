"""Pronóstico por hora de Open-Meteo, con copia local para usarlo sin señal."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from .lugares import Lugar

URL = "https://api.open-meteo.com/v1/forecast"
VARIABLES = ("precipitation_probability", "precipitation", "apparent_temperature",
             "uv_index", "is_day")
ZONA = "America/Panama"
CARPETA = Path("datos")


@dataclass(frozen=True)
class Hora:
    inicio: datetime
    lluvia_pct: int
    lluvia_mm: float
    sensacion_c: float
    uv: float
    de_dia: bool


@dataclass(frozen=True)
class Pronostico:
    horas: list[Hora]
    descargado: datetime
    desde_copia: bool
    motivo: str = ""


class SinPronostico(RuntimeError):
    """No hay conexión ni copia local del pronóstico."""


def descargar(lugar: Lugar, dias: int, timeout: float = 15) -> dict:
    consulta = urlencode({
        "latitude": lugar.latitud,
        "longitude": lugar.longitud,
        "hourly": ",".join(VARIABLES),
        "forecast_days": dias,
        "timezone": ZONA,
    })
    with urlopen(f"{URL}?{consulta}", timeout=timeout) as respuesta:
        return json.load(respuesta)


def obtener(lugar: Lugar, dias: int, ahora: datetime, sin_conexion: bool = False,
            carpeta: Path = CARPETA, descargador=descargar) -> Pronostico:
    """Descarga el pronóstico y guarda una copia; sin red, usa la última copia."""
    copia = carpeta / f"{lugar.clave}.json"
    motivo = "modo sin conexión"
    if not sin_conexion:
        try:
            datos = descargador(lugar, dias)
        except (URLError, TimeoutError, OSError) as error:
            motivo = f"no se pudo descargar: {getattr(error, 'reason', error)}"
        else:
            datos["_descargado"] = ahora.isoformat(timespec="minutes")
            carpeta.mkdir(parents=True, exist_ok=True)
            copia.write_text(json.dumps(datos), encoding="utf-8")
            return Pronostico(horas(datos), ahora, desde_copia=False)
    if not copia.exists():
        raise SinPronostico(
            f"Sin pronóstico ({motivo}) y sin copia guardada para {lugar.nombre}. "
            "Ejecuta Ventana seca una vez con conexión antes de salir."
        )
    datos = json.loads(copia.read_text(encoding="utf-8"))
    return Pronostico(horas(datos), datetime.fromisoformat(datos["_descargado"]),
                      desde_copia=True, motivo=motivo)


def horas(datos: dict) -> list[Hora]:
    """Convierte la respuesta de Open-Meteo en horas.

    Un dato faltante se toma por el lado prudente: lluvia probable, calor y UV alto.
    """
    h = datos["hourly"]
    resultado = []
    for i, texto in enumerate(h["time"]):
        def valor(nombre, prudente):
            v = h[nombre][i]
            return prudente if v is None else v

        resultado.append(Hora(
            inicio=datetime.fromisoformat(texto),
            lluvia_pct=int(valor("precipitation_probability", 100)),
            lluvia_mm=float(valor("precipitation", 0.0)),
            sensacion_c=float(valor("apparent_temperature", 40.0)),
            uv=float(valor("uv_index", 11.0)),
            de_dia=bool(valor("is_day", 0)),
        ))
    return resultado
