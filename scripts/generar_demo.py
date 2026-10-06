"""Convierte las salidas reales de demo/*.txt en imágenes y en un video corto.

Uso: uv run --with pillow python scripts/generar_demo.py
Necesita ffmpeg y la fuente Menlo de macOS. Las salidas se capturan antes,
ejecutando Ventana seca de verdad; este script solo las dibuja.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
DEMO = RAIZ / "demo"
# Orden del video: la ruta diaria primero, que es la historia del proyecto.
ESCENAS = ("ruta", "ruta-almuerzo", "lugar")

ESCALA = 2
# Renglón casi igual al alto de la letra para que el marco │ de la tarjeta no se corte.
LETRA, ALTO_LINEA, MARGEN, BARRA = 15 * ESCALA, 18 * ESCALA, 28 * ESCALA, 34 * ESCALA
MONO = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", LETRA)
SANS = "/System/Library/Fonts/Helvetica.ttc"
ANCHO_CARACTER = MONO.getlength("M")

FONDO, VENTANA, BARRA_COLOR = "#0f1115", "#1b1e24", "#2a2e36"
COLORES = {"cmd": "#7fd1e8", "titulo": "#ffffff", "sel": "#f5c66b", "ojo": "#ff8a6b",
           "ia": "#8fdc8f", "texto": "#e6e9ef"}


def color(linea: str) -> str:
    if linea.startswith("$ "):
        return COLORES["cmd"]
    if "Ventana seca ·" in linea:
        return COLORES["titulo"]
    if "→" in linea or "Para salir:" in linea:
        return COLORES["sel"]
    if "Ojo:" in linea:
        return COLORES["ojo"]
    if "Eligió: Gemma" in linea:
        return COLORES["ia"]
    return COLORES["texto"]


def tamano(lineas: list[str]) -> tuple[int, int]:
    columnas = max(len(linea) for linea in lineas)
    return (round(columnas * ANCHO_CARACTER) + 2 * MARGEN,
            len(lineas) * ALTO_LINEA + 2 * MARGEN + BARRA)


def lienzo(ancho: int, alto: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    imagen = Image.new("RGB", (ancho, alto), VENTANA)
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((0, 0, ancho, BARRA), fill=BARRA_COLOR)
    for i, tono in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        x, y, r = 22 * ESCALA + i * 20 * ESCALA, BARRA // 2, 6 * ESCALA
        dibujo.ellipse((x - r, y - r, x + r, y + r), fill=tono)
    dibujo.text((90 * ESCALA, BARRA // 2), "ventana-seca — zsh", fill="#9aa3b2",
                font=ImageFont.truetype(SANS, 13 * ESCALA), anchor="lm")
    return imagen, dibujo


def terminal(lineas: list[str], ancho: int, alto: int) -> Image.Image:
    imagen, dibujo = lienzo(ancho, alto)
    for i, linea in enumerate(lineas):
        y = BARRA + MARGEN + i * ALTO_LINEA
        if len(linea) > 2 and linea[0] == "│" and linea[-1] == "│":
            # El marco va en gris; solo el contenido lleva el color de la línea.
            borde = COLORES["texto"]
            dibujo.text((MARGEN, y), linea[0], fill=borde, font=MONO)
            dibujo.text((MARGEN + ANCHO_CARACTER, y), linea[1:-1], fill=color(linea), font=MONO)
            dibujo.text((MARGEN + ANCHO_CARACTER * (len(linea) - 1), y), linea[-1], fill=borde,
                        font=MONO)
        else:
            dibujo.text((MARGEN, y), linea, fill=color(linea), font=MONO)
    return imagen


def portada(ancho: int, alto: int) -> Image.Image:
    imagen, dibujo = lienzo(ancho, alto)
    centro = ancho // 2
    medio = BARRA + (alto - BARRA) // 2
    dibujo.text((centro, medio - 60 * ESCALA), "Ventana seca", fill="#ffffff",
                font=ImageFont.truetype(SANS, 54 * ESCALA), anchor="mm")
    for i, texto in enumerate(("La hora sin lluvia para salir, en Ciudad de Panamá",
                               "Gemma 4 E2B en local con Ollama · pronóstico de Open-Meteo")):
        dibujo.text((centro, medio + (10 + 38 * i) * ESCALA), texto, fill="#b7c0cf",
                    font=ImageFont.truetype(SANS, 22 * ESCALA), anchor="mm")
    return imagen


def main() -> None:
    escenas = {n: (DEMO / f"{n}.txt").read_text(encoding="utf-8").rstrip().splitlines()
               for n in ESCENAS}

    # Una imagen por escena, a su medida, para el README y el artículo.
    for nombre, lineas in escenas.items():
        terminal(lineas, *tamano(lineas)).save(DEMO / f"{nombre}.png", optimize=True)

    # Video: cuadros del mismo tamaño. Primero el comando solo, luego la salida completa.
    ancho = max(tamano(lineas)[0] for lineas in escenas.values())
    alto = max(tamano(lineas)[1] for lineas in escenas.values())
    ancho, alto = ancho + ancho % 2, alto + alto % 2
    cuadros = [(portada(ancho, alto), 3.0)]
    for lineas in escenas.values():
        cuadros += [(terminal(lineas[:1], ancho, alto), 1.5),
                    (terminal(lineas, ancho, alto), 6.0)]

    with tempfile.TemporaryDirectory() as carpeta:
        lista = []
        for i, (imagen, segundos) in enumerate(cuadros):
            png = Path(carpeta) / f"cuadro{i:02d}.png"
            imagen.save(png)
            lista += [f"file '{png}'", f"duration {segundos}"]
        lista.append(f"file '{png}'")  # ffmpeg ignora la duración del último cuadro
        indice = Path(carpeta) / "cuadros.txt"
        indice.write_text("\n".join(lista), encoding="utf-8")
        subprocess.run([shutil.which("ffmpeg"), "-y", "-loglevel", "error", "-f", "concat",
                        "-safe", "0", "-i", str(indice), "-vf", "format=yuv420p", "-r", "30",
                        "-c:v", "libx264", "-movflags", "+faststart",
                        str(DEMO / "ventana-seca-demo.mp4")], check=True, timeout=300)


if __name__ == "__main__":
    main()
