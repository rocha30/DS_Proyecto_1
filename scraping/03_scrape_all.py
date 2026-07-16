"""
Paso 1-2 — Scraping real: descarga un CSV crudo por departamento desde
BUSCAESTABLECIMIENTO_GE (MINEDUC).

Hallazgos previos que justifican este diseño (ver 00_discover_form.py,
01_test_search.py, 02_explore_playwright.py):

- El sitio está detrás de Incapsula: los POST "crudos" hechos con `requests`
  son ignorados silenciosamente (el servidor responde con la página por
  defecto en vez de procesar el postback). Por eso se usa Playwright
  (navegador real), que sí resuelve el challenge de Incapsula.
- El <select> de Departamento dispara un postback (onchange) que puebla
  en cascada el <select> de Municipio. El value 'TODOS' de Municipio queda
  seleccionado por defecto tras el cascade, así que no hace falta tocarlo.
- Nivel, Sector, Plan y Modalidad ya vienen en 'TODOS' por defecto.
- La tabla de resultados (id='_ctl0_ContentPlaceHolder1_dgResultado') no
  tiene paginación: devuelve todas las filas encontradas en una sola tabla
  (probado con GUATEMALA, ~9800 filas, sin truncar).
- Estructura de la tabla: primera <td> de cada fila está vacía (columna de
  ícono/selección), seguida de 17 columnas con nombre: CODIGO, DISTRITO,
  DEPARTAMENTO, MUNICIPIO, ESTABLECIMIENTO, DIRECCION, TELEFONO,
  SUPERVISOR, DIRECTOR, NIVEL, SECTOR, AREA, STATUS, MODALIDAD, JORNADA,
  PLAN, DEPARTAMENTAL.
- El dropdown de Departamento trae 23 valores (22 departamentos oficiales
  + 'CIUDAD CAPITAL' como entrada administrativa separada de 'GUATEMALA').
  Se scrapea cada value tal cual aparece en el dropdown; la unión/decisión
  sobre Ciudad Capital vs Guatemala se resuelve en el paso de limpieza, no
  aquí (este script solo guarda datos crudos, uno por value).

Esto guarda **datos crudos** (sin ninguna limpieza) en data_crudo/,
un CSV por value de departamento, tal como lo pide el plan del proyecto.
"""

import csv
import re
import time
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "http://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "crudo"

SEL_DEPARTAMENTO = "#_ctl0_ContentPlaceHolder1_cmbDepartamento"
SEL_CONSULTAR = "#_ctl0_ContentPlaceHolder1_IbtnConsultar"
TABLE_ID = "_ctl0_ContentPlaceHolder1_dgResultado"

PAUSA_ENTRE_DEPARTAMENTOS_SEG = 2
MAX_INTENTOS = 3


def slug(texto):
    texto = texto.strip().lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def obtener_departamentos(page):
    """Lee value+texto de cada <option> del combo de departamento (excluye placeholder)."""
    opciones = page.eval_on_selector_all(
        f"{SEL_DEPARTAMENTO} option",
        "opts => opts.map(o => ({value: o.value, texto: o.textContent}))",
    )
    return [o for o in opciones if o["value"] != "SELECCIONE UNO"]


def extraer_tabla(html):
    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table", {"id": TABLE_ID})
    if tabla is None:
        return None, None

    filas = tabla.find_all("tr")
    if not filas:
        return None, None

    encabezado = [c.get_text(strip=True) for c in filas[0].find_all(["td", "th"])][1:]
    datos = []
    for fila in filas[1:]:
        celdas = [c.get_text(strip=True) for c in fila.find_all("td")][1:]
        if any(celdas):
            datos.append(celdas)
    return encabezado, datos


def scrapear_departamento(page, value, texto):
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
            page.select_option(SEL_DEPARTAMENTO, value=value)
            page.wait_for_load_state("networkidle", timeout=60000)
            page.click(SEL_CONSULTAR)
            page.wait_for_load_state("networkidle", timeout=60000)

            html = page.content()
            encabezado, datos = extraer_tabla(html)
            if encabezado is None:
                raise RuntimeError("No se encontró la tabla de resultados en el HTML.")
            return encabezado, datos
        except Exception as exc:
            print(f"  [intento {intento}/{MAX_INTENTOS}] error en '{texto}': {exc}")
            if intento == MAX_INTENTOS:
                raise
            time.sleep(3)


def main():
    OUT_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        departamentos = obtener_departamentos(page)

        print(f"Departamentos a scrapear: {len(departamentos)}\n")

        for i, dep in enumerate(departamentos, start=1):
            value, texto = dep["value"], dep["texto"]
            print(f"[{i}/{len(departamentos)}] {texto} (value='{value}')")

            encabezado, datos = scrapear_departamento(page, value, texto)

            nombre_archivo = f"{value}_{slug(texto)}.csv"
            ruta = OUT_DIR / nombre_archivo
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(encabezado)
                writer.writerows(datos)

            print(f"  -> {len(datos)} filas guardadas en {ruta}")

            if i < len(departamentos):
                time.sleep(PAUSA_ENTRE_DEPARTAMENTOS_SEG)

        browser.close()

    print("\nListo. CSVs crudos en:", OUT_DIR.resolve())


if __name__ == "__main__":
    main()
