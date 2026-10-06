"""La tarjeta de un vistazo y el recordatorio de calendario.

La idea es mirar la pantalla una vez, guardar el teléfono y salir: el
recordatorio avisa media hora antes.
"""

from datetime import datetime, timedelta, timezone

DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic")
# Panamá no cambia de horario: siempre UTC-5.
PANAMA = timezone(timedelta(hours=-5))
AVISO_MIN = 30


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
        f"Eligió: {origen}",
    ]
    if pronostico.desde_copia:
        lineas.append(f"Sin señal: pronóstico guardado el {dia_es(pronostico.descargado)} "
                      f"a las {hora_es(pronostico.descargado)}.")
    ancho = max(len(linea) for linea in lineas)
    borde = "─" * (ancho + 2)
    cuerpo = [f"│ {linea.ljust(ancho)} │" for linea in lineas]
    return "\n".join([f"┌{borde}┐", *cuerpo, f"└{borde}┘"])


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
