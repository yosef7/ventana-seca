# Demo

[Inicio](../README.md)

Salidas reales de Ventana seca del **martes 6 oct 2026 a las 12:36 a. m.**, con el pronóstico de Open-Meteo y `gemma4:e2b` en una MacBook de 8 GB. Los `.txt` son la salida tal cual; las imágenes y el video se dibujan a partir de ellos con [`scripts/generar_demo.py`](../scripts/generar_demo.py):

```sh
uv run --with pillow python scripts/generar_demo.py
```

| Archivo | Qué muestra |
| --- | --- |
| [`ventana-seca-demo.mp4`](ventana-seca-demo.mp4) | Video de 31 s sin narración: portada y las tres escenas, primero el comando y luego la tarjeta |
| [`ruta.png`](ruta.png) · [`ruta.txt`](ruta.txt) | Ruta diaria sin preferencia: Gemma elige las 8:00 a. m. en Costa del Este y la capa entra en la lista por la lluvia de las 4 p. m. |
| [`ruta-almuerzo.png`](ruta-almuerzo.png) · [`ruta-almuerzo.txt`](ruta-almuerzo.txt) | Misma ruta pidiendo caminar en el almuerzo: Gemma respeta la hora y advierte; el código agrega «Ojo» por el 66 % |
| [`lugar.png`](lugar.png) · [`lugar.txt`](lugar.txt) | Parque Natural Metropolitano, dos horas, «temprano, voy con mi hija de 6 años» |
