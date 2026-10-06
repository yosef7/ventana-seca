"""Uso: uv run python -m ventana_seca --lugar metropolitano --preferencia "temprano"."""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import gemma, pronostico, tarjeta, ventanas
from .lugares import LUGARES


def argumentos(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="ventana_seca",
        description="Encuentra la ventana sin lluvia para salir en Ciudad de Panamá.")
    p.add_argument("--lugar", choices=sorted(LUGARES), default="metropolitano")
    p.add_argument("--duracion", type=int, choices=range(1, 5), default=1, metavar="HORAS",
                   help="cuánto vas a estar afuera, de 1 a 4 horas (1 por defecto)")
    p.add_argument("--dias", type=int, choices=range(1, 8), default=3, metavar="DÍAS",
                   help="cuántos días mirar, de 1 a 7 (3 por defecto)")
    p.add_argument("--preferencia", default="",
                   help='lo que prefieres, en tus palabras: "temprano, voy con mi hija"')
    p.add_argument("--ics", type=Path, metavar="ARCHIVO",
                   help="guarda un evento de calendario con aviso 30 min antes")
    p.add_argument("--sin-conexion", action="store_true",
                   help="usa el último pronóstico guardado, sin internet")
    p.add_argument("--sin-ia", action="store_true", help="elige con la regla fija")
    p.add_argument("--modelo", default=gemma.MODELO, help="modelo de Ollama")
    p.add_argument("--ventanas", action="store_true",
                   help="muestra también todas las ventanas candidatas")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = argumentos(argv)
    lugar = LUGARES[args.lugar]
    ahora = datetime.now(tarjeta.PANAMA).replace(tzinfo=None, second=0, microsecond=0)

    try:
        # Open-Meteo cuenta hoy como el primer día, aunque ya sea de noche.
        prono = pronostico.obtener(lugar, args.dias + 1, ahora,
                                   sin_conexion=args.sin_conexion)
    except pronostico.SinPronostico as error:
        print(error, file=sys.stderr)
        return 1

    limite = ahora + timedelta(days=args.dias)
    horas = [h for h in prono.horas if h.inicio < limite]
    candidatas = ventanas.candidatas(horas, args.duracion, ahora)
    if not candidatas:
        print("No quedan horas de luz en el pronóstico. Prueba con más días.",
              file=sys.stderr)
        return 1

    eleccion = gemma.elegir(candidatas, lugar, args.preferencia, args.modelo,
                            usar_ia=not args.sin_ia)
    elegida = next(v for v in candidatas if v.letra == eleccion.letra)

    if args.ventanas:
        for v in candidatas:
            marca = "→" if v is elegida else " "
            print(f"{marca} {gemma.describir(v)}")
        print()
    print(tarjeta.texto(lugar, elegida, eleccion, prono))
    if args.ics:
        args.ics.write_text(tarjeta.ics(lugar, elegida, eleccion, ahora), encoding="utf-8")
        print(f"\nRecordatorio guardado en {args.ics}. Ábrelo y guarda el teléfono.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
