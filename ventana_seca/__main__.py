"""Uso: uv run python -m ventana_seca --lugar metropolitano --preferencia "temprano"."""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import gemma, pronostico, ruta, tarjeta, ventanas
from .lugares import LUGARES

RUTA = pronostico.CARPETA / "ruta.txt"


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
    p.add_argument("--ruta", metavar="PARADAS",
                   help='tu ruta del día: "7:30 5 de mayo, 8:00 costa del este, 4 pm costa '
                        'del este". Se guarda para usarla con --mi-ruta')
    p.add_argument("--mi-ruta", action="store_true", help="usa la última ruta guardada")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = argumentos(argv)
    ahora = datetime.now(tarjeta.PANAMA).replace(tzinfo=None, second=0, microsecond=0)
    try:
        if args.ruta or args.mi_ruta:
            return por_ruta(args, ahora)
        return por_lugar(args, ahora)
    except (pronostico.SinPronostico, ValueError) as error:
        print(error, file=sys.stderr)
        return 1


def por_lugar(args, ahora: datetime) -> int:
    lugar = LUGARES[args.lugar]
    # Open-Meteo cuenta hoy como el primer día, aunque ya sea de noche.
    prono = pronostico.obtener(lugar, args.dias + 1, ahora, sin_conexion=args.sin_conexion)
    limite = ahora + timedelta(days=args.dias)
    horas = [h for h in prono.horas if h.inicio < limite]
    candidatas = ventanas.candidatas(horas, args.duracion, ahora)
    if not candidatas:
        raise ValueError("No quedan horas de luz en el pronóstico. Prueba con más días.")

    eleccion = gemma.elegir(candidatas, lugar, args.preferencia, args.modelo,
                            usar_ia=not args.sin_ia)
    elegida = next(v for v in candidatas if v.letra == eleccion.letra)
    if args.ventanas:
        for v in candidatas:
            print(f"{'→' if v is elegida else ' '} {v.letra}: {gemma.describir(v)}")
        print()
    print(tarjeta.texto(lugar, elegida, eleccion, prono))
    guardar_ics(args, lugar, elegida, eleccion, ahora)
    return 0


def por_ruta(args, ahora: datetime) -> int:
    if args.ruta:
        texto = args.ruta
        RUTA.parent.mkdir(parents=True, exist_ok=True)
        RUTA.write_text(texto, encoding="utf-8")
    elif RUTA.exists():
        texto = RUTA.read_text(encoding="utf-8")
    else:
        raise ValueError("Aún no hay ruta guardada. Escríbela una vez con --ruta.")

    paradas = ruta.en_fecha(ruta.leer(texto), ahora)
    pronosticos = {clave: pronostico.obtener(LUGARES[clave], 2, ahora,
                                             sin_conexion=args.sin_conexion)
                   for clave in sorted({clave for _, clave in paradas})}
    candidatas = ventanas.en_ruta(paradas, {c: p.horas for c, p in pronosticos.items()},
                                  timedelta(hours=args.duracion))
    if not candidatas:
        raise ValueError("Ninguna parada de la ruta cae dentro del pronóstico.")

    eleccion = gemma.elegir(candidatas, None, args.preferencia, args.modelo,
                            usar_ia=not args.sin_ia)
    elegida = next(v for v in candidatas if v.letra == eleccion.letra)
    nombres = {clave: LUGARES[clave].nombre for clave in pronosticos}
    print(tarjeta.texto_ruta(candidatas, eleccion, pronosticos.values(), nombres))
    guardar_ics(args, LUGARES[elegida.lugar], elegida, eleccion, ahora)
    return 0


def guardar_ics(args, lugar, elegida, eleccion, ahora: datetime) -> None:
    if args.ics:
        args.ics.write_text(tarjeta.ics(lugar, elegida, eleccion, ahora), encoding="utf-8")
        print(f"\nRecordatorio guardado en {args.ics}. Ábrelo y guarda el teléfono.")


if __name__ == "__main__":
    sys.exit(main())
