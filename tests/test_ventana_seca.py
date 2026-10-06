import json
from datetime import datetime, timedelta
from urllib.error import URLError

import pytest

from ventana_seca import gemma, pronostico, tarjeta, ventanas
from ventana_seca.__main__ import main
from ventana_seca.lugares import LUGARES

METRO = LUGARES["metropolitano"]
CINTA = LUGARES["cinta-costera"]
AHORA = datetime(2026, 10, 6, 5, 0)


def octubre(dias=2, desde=datetime(2026, 10, 6)) -> dict:
    """Respuesta de Open-Meteo con un día típico de octubre: mañana seca y aguacero a las 2."""
    tiempos, prob, mm, sens, uv, dia = [], [], [], [], [], []
    for d in range(dias):
        for h in range(24):
            t = desde.replace(hour=h) + timedelta(days=d)
            tiempos.append(t.isoformat(timespec="minutes"))
            de_dia = 6 <= h < 18
            dia.append(int(de_dia))
            lluvia = 85 if 14 <= h < 17 else (40 if h in (12, 13) else 10)
            prob.append(lluvia)
            mm.append(4.0 if 14 <= h < 17 else 0.0)
            sens.append(26 + (9 if 10 <= h < 15 else 0))
            uv.append(max(0, 10 - abs(12 - h) * 2) if de_dia else 0)
    return {"hourly": {"time": tiempos, "precipitation_probability": prob,
                       "precipitation": mm, "apparent_temperature": sens,
                       "uv_index": uv, "is_day": dia}}


def candidatas(duracion=1, ahora=AHORA):
    return ventanas.candidatas(pronostico.horas(octubre()), duracion, ahora)


def respuesta(contenido) -> dict:
    return {"message": {"content": json.dumps(contenido)}}


# Ventanas -----------------------------------------------------------------

def test_la_mejor_ventana_es_por_la_manana_y_evita_el_aguacero():
    lista = candidatas(duracion=2)
    mejor = gemma.por_regla(lista)
    assert mejor.inicio.hour < 10
    assert mejor.buena
    for v in lista:
        assert not (v.inicio.hour < 17 and v.fin.hour > 14), "toca el aguacero"


def test_solo_horas_de_luz_futuras_sin_solapes_y_letras_en_orden():
    lista = candidatas(duracion=2, ahora=datetime(2026, 10, 6, 7, 30))
    assert [v.letra for v in lista] == list("ABCD")[:len(lista)]
    assert lista == sorted(lista, key=lambda v: v.inicio)
    for v in lista:
        assert v.inicio >= datetime(2026, 10, 6, 7, 30)
        assert 6 <= v.inicio.hour and v.fin.hour <= 18
    for a, b in zip(lista, lista[1:]):
        assert a.fin + ventanas.SEPARACION <= b.inicio


def test_como_maximo_dos_por_dia():
    lista = candidatas()
    por_dia = {}
    for v in lista:
        por_dia[v.inicio.date()] = por_dia.get(v.inicio.date(), 0) + 1
    assert max(por_dia.values()) <= 2


def test_dato_faltante_se_toma_como_lluvia():
    datos = octubre(1)
    datos["hourly"]["precipitation_probability"][7] = None
    hora = pronostico.horas(datos)[7]
    assert hora.lluvia_pct == 100


def test_sin_horas_de_luz_no_hay_candidatas():
    assert candidatas(ahora=datetime(2026, 10, 7, 18, 0)) == []


# Gemma --------------------------------------------------------------------

def test_gemma_elige_segun_la_preferencia_y_suma_imprescindibles():
    lista = candidatas()
    tarde = lista[-1]
    eleccion = gemma.elegir(lista, METRO, "en la tarde", cliente=lambda _: respuesta(
        {"letra": tarde.letra, "motivo": "  Vas  después del trabajo. ", "llevar": ["agua"]}))
    assert eleccion.por_gemma
    assert eleccion.letra == tarde.letra
    assert eleccion.motivo == "Vas después del trabajo."
    assert "repelente" in eleccion.llevar  # el bosque lo pide aunque Gemma no lo diga


def test_gemma_no_puede_inventar_ventanas_ni_objetos():
    lista = candidatas()
    eleccion = gemma.elegir(lista, CINTA, cliente=lambda _: respuesta(
        {"letra": "Z", "motivo": "Inventada", "llevar": ["dron"]}))
    assert not eleccion.por_gemma
    assert eleccion.letra == gemma.por_regla(lista).letra
    assert "dron" not in eleccion.llevar


def test_objetos_fuera_de_lista_se_descartan():
    lista = candidatas()
    eleccion = gemma.elegir(lista, CINTA, cliente=lambda _: respuesta(
        {"letra": "A", "motivo": "Temprano.", "llevar": ["ropa de cambio", "paraguas"]}))
    assert "ropa de cambio" in eleccion.llevar
    assert "paraguas" not in eleccion.llevar


def test_sin_ollama_decide_la_regla():
    def caido(_):
        raise URLError("connection refused")

    lista = candidatas()
    eleccion = gemma.elegir(lista, METRO, cliente=caido)
    assert not eleccion.por_gemma
    assert eleccion.letra == gemma.por_regla(lista).letra
    assert eleccion.motivo


def test_el_pedido_limita_la_letra_a_las_candidatas_y_no_razona_de_mas():
    lista = candidatas()
    cuerpo = gemma.pedido(lista, METRO, "", gemma.MODELO)
    assert cuerpo["format"]["properties"]["letra"]["enum"] == [v.letra for v in lista]
    assert cuerpo["think"] is False
    assert "sin preferencia" in cuerpo["messages"][1]["content"]


def test_capa_y_linterna_cuando_hacen_falta():
    v = ventanas.Ventana("A", datetime(2026, 10, 6, 17), datetime(2026, 10, 6, 18),
                         45, 0.5, 28, 1, 50)
    assert {"capa de lluvia", "linterna", "agua"} <= gemma.imprescindibles(v, CINTA)


# Tarjeta y calendario -----------------------------------------------------

def test_formato_de_fecha_y_hora_en_espanol():
    assert tarjeta.dia_es(datetime(2026, 10, 7)) == "mié 7 oct"
    assert tarjeta.hora_es(datetime(2026, 10, 7, 6)) == "6:00 a. m."
    assert tarjeta.hora_es(datetime(2026, 10, 7, 12)) == "12:00 p. m."


def test_la_tarjeta_avisa_si_la_ventana_no_es_seca_aunque_el_modelo_lo_suavice():
    v = ventanas.Ventana("A", datetime(2026, 10, 7, 18), datetime(2026, 10, 7, 19),
                         53, 0.0, 33, 0, 43)
    eleccion = gemma.Eleccion("A", "No se esperan precipitaciones, " * 5, ("agua",), True)
    prono = pronostico.Pronostico([], AHORA, desde_copia=True, motivo="modo sin conexión")
    texto = tarjeta.texto(METRO, v, eleccion, prono)
    assert "Ojo: no es una ventana seca de verdad (53 % de lluvia)." in texto
    assert "Sin señal (modo sin conexión)" in texto
    assert max(len(linea) for linea in texto.splitlines()) <= tarjeta.ANCHO + 4


def test_ics_en_utc_con_aviso_media_hora_antes():
    v = candidatas()[0]
    eleccion = gemma.Eleccion(v.letra, "Temprano; antes del calor, y seco.", ("agua",), True)
    contenido = tarjeta.ics(METRO, v, eleccion, AHORA)
    inicio_utc = (v.inicio + timedelta(hours=5)).strftime("%Y%m%dT%H%M%SZ")
    assert f"DTSTART:{inicio_utc}" in contenido
    assert "TRIGGER:-PT30M" in contenido
    assert "Temprano\\; antes del calor\\, y seco." in contenido
    assert contenido.endswith("END:VCALENDAR\r\n")


# Sin señal ----------------------------------------------------------------

def test_sin_senal_usa_la_ultima_copia(tmp_path):
    def sin_red(*_):
        raise URLError("sin señal")

    with pytest.raises(pronostico.SinPronostico):
        pronostico.obtener(METRO, 2, AHORA, carpeta=tmp_path, descargador=sin_red)

    pronostico.obtener(METRO, 2, AHORA, carpeta=tmp_path, descargador=lambda *_: octubre())
    prono = pronostico.obtener(METRO, 2, AHORA + timedelta(hours=3), carpeta=tmp_path,
                               descargador=sin_red)
    assert prono.desde_copia
    assert prono.descargado == AHORA
    assert len(prono.horas) == 48


def test_comando_completo_sin_conexion_y_sin_ia(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datos").mkdir()
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    datos = octubre(3, desde=hoy + timedelta(days=1)) | {"_descargado": "2026-10-06T05:00"}
    (tmp_path / "datos" / "metropolitano.json").write_text(json.dumps(datos))

    salida_ics = tmp_path / "salir.ics"
    assert main(["--sin-conexion", "--sin-ia", "--ics", str(salida_ics)]) == 0
    texto = capsys.readouterr().out
    assert "Parque Natural Metropolitano" in texto
    assert "regla fija" in texto
    assert "Sin señal" in texto
    assert salida_ics.read_text().startswith("BEGIN:VCALENDAR")
