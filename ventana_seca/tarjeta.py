"""La tarjeta de un vistazo y el recordatorio de calendario.

La idea es mirar la pantalla una vez, guardar el teléfono y salir: el
recordatorio avisa media hora antes.
"""

import textwrap
from datetime import datetime, timedelta, timezone

DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic")
# Panamá no cambia de horario: siempre UTC-5.
PANAMA = timezone(timedelta(hours=-5))
AVISO_MIN = 30
ANCHO = 64


def dia_es(fecha: datetime) -> str:
    return f"{DIAS[fecha.weekday()]} {fecha.day} {MESES[fecha.month - 1]}"


def hora_es(fecha: datetime) -> str:
    h = fecha.hour % 12 or 12
    sufijo = "a. m." if fecha.hour < 12 else "p. m."
    return f"{h}:{fecha.minute:02d} {sufijo}"


def mm_es(mm: float) -> str:
    return f"{mm:.1f} mm".replace(".", ",")


def texto(lugar, ventana, eleccion, pronostico) -> str:
    v = ventana
    origen = "Gemma, en este equipo" if eleccion.por_gemma else "regla fija (sin IA)"
    lineas = [
        f"Ventana seca · {lugar.nombre}",
        f"{dia_es(v.inicio).capitalize()} · {hora_es(v.inicio)} – {hora_es(v.fin)}",
        f"Lluvia: hasta {v.lluvia_pct} % ({mm_es(v.lluvia_mm)})"
        f" · Sensación: {v.sensacion_max:.0f} °C"
        f" · UV: {v.uv_max:.0f}",
        f"Lleva: {', '.join(eleccion.llevar)}",
        f"Por qué: {eleccion.motivo}",
    ]
    if not v.buena:
        # Lo dice el código, no el modelo: un modelo pequeño tiende a suavizar el riesgo.
        lineas.append(f"Ojo: no es una ventana seca de verdad ({v.lluvia_pct} % de lluvia).")
    lineas.append(f"Eligió: {origen}")
    return _caja(lineas + _sin_senal([pronostico]))


def estado(v) -> str:
    if v.lluvia_pct >= 50 or v.lluvia_mm >= 1:
        cielo = "lluvia"
    elif v.lluvia_pct >= 30:
        cielo = "quizá llueve"
    else:
        cielo = "seco"
    return cielo + (" y calor" if v.sensacion_max > 32 else "")


def _caja(lineas: list[str]) -> str:
    # Las líneas cortas quedan tal cual, con su alineación; solo se parten las largas.
    lineas = [corta for linea in lineas
              for corta in ([linea] if len(linea) <= ANCHO
                            else textwrap.wrap(linea, ANCHO, subsequent_indent="  "))]
    ancho = max(len(linea) for linea in lineas)
    borde = "─" * (ancho + 2)
    cuerpo = [f"│ {linea.ljust(ancho)} │" for linea in lineas]
    return "\n".join([f"┌{borde}┐", *cuerpo, f"└{borde}┘"])


def _sin_senal(pronosticos) -> list[str]:
    return [f"Sin señal ({p.motivo}): pronóstico guardado el {dia_es(p.descargado)} "
            f"a las {hora_es(p.descargado)}" for p in pronosticos if p.desde_copia][:1]


def texto_ruta(paradas, eleccion, pronosticos, nombres: dict[str, str]) -> str:
    """Toda la ruta en una caja: cómo está cada parada y cuál conviene para salir."""
    elegida = next(v for v in paradas if v.letra == eleccion.letra)
    ancho_hora = max(len(hora_es(v.inicio)) for v in paradas)
    ancho_lugar = max(len(nombres[v.lugar]) for v in paradas)
    origen = "Gemma, en este equipo" if eleccion.por_gemma else "regla fija (sin IA)"
    lineas = [f"Ventana seca · tu ruta del {dia_es(paradas[0].inicio)}", ""]
    for v in paradas:
        marca = "→" if v is elegida else " "
        lineas.append(f"{marca} {hora_es(v.inicio).rjust(ancho_hora)}  "
                      f"{nombres[v.lugar].ljust(ancho_lugar)}  {v.lluvia_pct:>3} % · "
                      f"{v.sensacion_max:.0f} °C · {estado(v)}")
    lineas += [
        "",
        f"Para salir: {hora_es(elegida.inicio)} en {nombres[elegida.lugar]}",
        f"Lleva hoy: {', '.join(eleccion.llevar)}",
        f"Por qué: {eleccion.motivo}",
    ]
    if not elegida.buena:
        lineas.append(f"Ojo: no es una ventana seca de verdad ({elegida.lluvia_pct} % de lluvia).")
    lineas.append(f"Eligió: {origen}")
    return _caja(lineas + _sin_senal(pronosticos))


def _utc(fecha: datetime) -> str:
    return fecha.replace(tzinfo=PANAMA).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escapar(valor: str) -> str:
    return (valor.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\n", "\\n"))


def ics(lugar, ventana, eleccion, ahora: datetime) -> str:
    """Un evento con alarma, para que el teléfono avise y no haga falta mirarlo."""
    descripcion = f"{eleccion.motivo}\nLleva: {', '.join(eleccion.llevar)}"
    lineas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Ventana seca//ES",
        "BEGIN:VEVENT",
        f"UID:{_utc(ventana.inicio)}-{lugar.clave}@ventana-seca",
        f"DTSTAMP:{_utc(ahora)}",
        f"DTSTART:{_utc(ventana.inicio)}",
        f"DTEND:{_utc(ventana.fin)}",
        f"SUMMARY:{_escapar('Salir: ' + lugar.nombre)}",
        f"LOCATION:{_escapar(lugar.nombre)}",
        f"DESCRIPTION:{_escapar(descripcion)}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{_escapar('Guarda el teléfono y sal: ' + lugar.nombre)}",
        f"TRIGGER:-PT{AVISO_MIN}M",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lineas) + "\r\n"
