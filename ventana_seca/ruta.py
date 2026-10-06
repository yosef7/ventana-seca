"""La ruta diaria de la persona: «7:30 5 de mayo, 8:00 costa del este, 4 pm costa del este»."""

import re
from datetime import datetime, time, timedelta

from .lugares import buscar

PATRON = re.compile(r"^\s*(\d{1,2})(?::(\d{2}))?\s*([ap])?\.?\s*(?:m\.?)?\s+(.+?)\s*$",
                    re.IGNORECASE)


def leer(texto: str) -> list[tuple[time, str]]:
    paradas = []
    for parte in texto.split(","):
        m = PATRON.match(parte)
        if not m:
            raise ValueError(f"No entiendo «{parte.strip()}». Escribe, por ejemplo, "
                             "«7:30 5 de mayo, 4 pm costa del este».")
        hora, minuto = int(m.group(1)), int(m.group(2) or 0)
        if m.group(3):
            hora = hora % 12 + (12 if m.group(3).lower() == "p" else 0)
        if hora > 23 or minuto > 59:
            raise ValueError(f"Hora imposible: «{parte.strip()}».")
        paradas.append((time(hora, minuto), buscar(m.group(4)).clave))
    return sorted(paradas)


def en_fecha(paradas: list[tuple[time, str]], ahora: datetime) -> list[tuple[datetime, str]]:
    """Hoy, si aún queda alguna parada por delante; si no, mañana. Sin las que ya pasaron."""
    hoy = ahora.date()
    if all(datetime.combine(hoy, t) <= ahora for t, _ in paradas):
        hoy += timedelta(days=1)
    return [(datetime.combine(hoy, t), clave) for t, clave in paradas
            if datetime.combine(hoy, t) > ahora]
