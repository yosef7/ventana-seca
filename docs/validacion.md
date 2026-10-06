# Validación

[Inicio](../README.md) · [Arquitectura](arquitectura.md)

Tres niveles: pruebas automáticas, ejecuciones con el pronóstico y el modelo reales, y una prueba afuera en una ruta diaria.

## 1. Pruebas automáticas

```sh
uv run pytest
```

**25 pruebas aprobadas** el 6 oct 2026. Usan un pronóstico sintético con un día típico de octubre (mañana seca, aguacero de 2:00 a 5:00 p. m.) y un cliente falso en lugar de Ollama, así que no necesitan red ni modelo.

| Grupo | Qué se comprueba |
| --- | --- |
| Ventanas | La mejor ventana cae en la mañana y ninguna toca el aguacero; solo horas de luz futuras; ventanas del mismo día separadas por 3 horas; letras en orden; como máximo dos por día; un dato faltante se toma como lluvia; sin horas de luz no hay candidatas |
| Gemma | Elige según la preferencia y el código suma lo imprescindible; no puede inventar ventanas ni objetos; los objetos fuera de la lista se descartan; sin Ollama decide la regla fija; el pedido limita la elección a las etiquetas existentes, no muestra letras y apaga el razonamiento; capa y linterna cuando hacen falta |
| Tarjeta y calendario | Fechas y horas en español; aviso «Ojo» aunque el modelo suavice el riesgo; ancho máximo de la tarjeta; `.ics` en UTC con aviso 30 minutos antes y texto escapado |
| Sin señal | Sin red y sin copia, error claro; con copia, la usa y dice cuándo se guardó; comando completo sin conexión y sin IA |
| Ruta | Lectura de `7:30`, `12 pm`, `4pm`, `16:00` y de nombres con o sin guiones; errores claros para entradas imposibles; ruta de hoy mientras quede alguna parada; cada parada toma las horas del pronóstico que le tocan; la capa de la tarde se lleva desde la mañana; la tarjeta muestra todas las paradas; la ruta se guarda y se reusa con `--mi-ruta` |

## 2. Ejecuciones reales

Equipo: MacBook con 8 GB de RAM, Ollama 0.35.1, `gemma4:e2b` (4,6 GB, Q4_K_M). Pronóstico real de Open-Meteo descargado entre el 5 oct a las 11:59 p. m. y el 6 oct a las 12:36 a. m.

| Prueba | Resultado | Qué cambió |
| --- | --- | --- |
| Sin IA, Parque Natural Metropolitano, 2 horas | Propuso el mar 6 oct de 7:00 a 9:00 a. m. (20 % de lluvia, puntaje 80) y dejó fuera las tardes | Se corrigieron el doble punto en «a. m..», los decimales con coma y `--dias`, que cubría un día menos porque Open-Meteo cuenta hoy |
| Con Gemma, con el razonamiento activado | Elecciones correctas en **38 a 114 s** | Se apagó el razonamiento: **7 a 9 s** |
| Gemma con «después del trabajo, no antes de las 4» | Eligió el mié 7 oct a las 6:00 p. m., pero escribió «poca probabilidad de lluvia» para un **53 %** | Se agregó el aviso «Ojo», que genera el código para toda ventana con puntaje menor de 60 |
| Gemma con «voy con mi hija de 6 años, que no aguanta el calor» | Eligió la mañana fresca y mencionó el bosque | — |
| Gemma con candidatas pegadas | Ofrecía 7:00–8:00 y 8:00–9:00 como opciones distintas | Ventanas del mismo día separadas por 3 horas |
| Ruta real, sin preferencia | Escribió «La opción B tiene la menor probabilidad…», una letra que la tarjeta no muestra | Gemma ahora elige entre etiquetas legibles |
| Ruta, «quiero caminar un rato en la hora del almuerzo» | Primero eligió las 8:00 a. m. sin explicar por qué descartaba el almuerzo; después, con la instrucción nueva, eligió las 12:00 p. m. y advirtió: «Prepárate para estar muy húmedo y caluroso» | Instrucción: respetar la hora pedida si existe y advertir el riesgo |
| Ruta, «solo puedo salir al terminar el trabajo, a las 4» | Eligió las 4:00 p. m. y advirtió que hay mucha lluvia; la tarjeta agregó «Ojo» (88 %) | — |
| Descarga que no respondió en 15 s | Usó la copia guardada y la tarjeta dijo «Sin señal (no se pudo descargar: timed out)» | — |

## 3. Prueba afuera: ruta del martes 6 oct 2026

Ruta diaria del autor: Plaza 5 de Mayo a las 7:30 a. m. y Costa del Este a las 8:00 a. m., 12:00 p. m. y 4:00 p. m.

```sh
uv run python -m ventana_seca \
  --ruta "7:30 5 de mayo, 8:00 costa del este, 12 pm costa del este, 4 pm costa del este"
```

Pronóstico calculado el 6 oct a las 12:21 a. m. y sin cambios a las 12:36 a. m. Ventana seca recomendó salir a las **8:00 a. m. en Costa del Este** y llevar agua, gorra, bloqueador y capa de lluvia.

| Parada | Pronóstico | Qué pasó |
| --- | --- | --- |
| 7:30 a. m. · Plaza 5 de Mayo | 20 % · 31 °C · seco | [Pendiente] |
| 8:00 a. m. · Costa del Este | 18 % · 31 °C · seco | [Pendiente] |
| 12:00 p. m. · Costa del Este | 66 % · 39 °C · lluvia y calor | [Pendiente] |
| 4:00 p. m. · Costa del Este | 88 % · 31 °C · lluvia | [Pendiente] |

[Pendiente]: completar la tabla al final del día y agregar la foto de la salida de las 8:00 a. m.
