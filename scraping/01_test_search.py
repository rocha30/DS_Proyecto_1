"""
Paso 0b — Prueba de flujo completo de postback para UN departamento.

Objetivo: confirmar
  1) que el cascade Departamento -> Municipio funciona reenviando el
     __EVENTTARGET de cmbDepartamento con el value elegido, y
  2) cómo luce el HTML de resultados (tabla GridView) y si hay paginación,
antes de escribir el scraper real que recorra los 22 departamentos.

No guarda CSV todavía, solo guarda HTML intermedio para inspección manual.
"""

import requests
from bs4 import BeautifulSoup

URL = "http://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# Sacatepéquez: departamento chico, bueno para probar rápido.
DEPARTAMENTO_PRUEBA = "03"

ASPNET_HIDDEN = ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION")


def extraer_hidden(soup):
    campos = {}
    for name in ASPNET_HIDDEN:
        tag = soup.find("input", {"name": name})
        campos[name] = tag.get("value", "") if tag else ""
    return campos


def base_payload(hidden):
    return {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        **hidden,
        "_ctl0:ContentPlaceHolder1:cmbDepartamento": "SELECCIONE UNO",
        "_ctl0:ContentPlaceHolder1:cmbMunicipio": "",
        "_ctl0:ContentPlaceHolder1:cmbNivel": "TODOS",
        "_ctl0:ContentPlaceHolder1:cmbSector": "TODOS",
        "_ctl0:ContentPlaceHolder1:ddlplan": "TODOS",
        "_ctl0:ContentPlaceHolder1:ddlModalidad": "TODOS",
        "_ctl0:ContentPlaceHolder1:txtCodEstab": "",
        "_ctl0:ContentPlaceHolder1:txtNomEstab": "",
        "_ctl0:ContentPlaceHolder1:txtDirecEstab": "",
    }


def main():
    session = requests.Session()

    # 1) GET inicial
    resp = session.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = extraer_hidden(soup)

    # 2) POST de cascada: seleccionar Departamento -> dispara postback
    #    que puebla cmbMunicipio.
    payload = base_payload(hidden)
    payload["__EVENTTARGET"] = "_ctl0$ContentPlaceHolder1$cmbDepartamento"
    payload["_ctl0:ContentPlaceHolder1:cmbDepartamento"] = DEPARTAMENTO_PRUEBA

    resp2 = session.post(URL, headers=HEADERS, data=payload, timeout=30)
    resp2.raise_for_status()
    resp2.encoding = resp2.apparent_encoding
    soup2 = BeautifulSoup(resp2.text, "html.parser")

    municipio_sel = soup2.find(
        "select", {"name": "_ctl0:ContentPlaceHolder1:cmbMunicipio"}
    )
    print("=" * 80)
    print(f"MUNICIPIOS para departamento value='{DEPARTAMENTO_PRUEBA}'")
    print("=" * 80)
    if municipio_sel:
        opciones = municipio_sel.find_all("option")
        for opt in opciones:
            print(f"  value='{opt.get('value', '')}'  texto='{opt.get_text(strip=True)}'")
    else:
        print("cmbMunicipio no encontrado en la respuesta del postback.")
    print()

    with open("test_cascade_municipio.html", "w", encoding="utf-8") as f:
        f.write(resp2.text)
    print("HTML del postback de cascada guardado en: test_cascade_municipio.html\n")

    # 3) POST de búsqueda: click en IbtnConsultar (botón imagen) dejando
    #    Municipio = TODOS (si existe esa opción) para traer todo el depto.
    hidden2 = extraer_hidden(soup2)
    payload3 = base_payload(hidden2)
    payload3["_ctl0:ContentPlaceHolder1:cmbDepartamento"] = DEPARTAMENTO_PRUEBA

    if municipio_sel:
        valores_municipio = {opt.get("value", "") for opt in municipio_sel.find_all("option")}
        if "TODOS" in valores_municipio:
            payload3["_ctl0:ContentPlaceHolder1:cmbMunicipio"] = "TODOS"
        else:
            primer_valor = next(iter(valores_municipio), "")
            payload3["_ctl0:ContentPlaceHolder1:cmbMunicipio"] = primer_valor
            print(f"Aviso: no hay opción 'TODOS' en municipio, "
                  f"usando primer value encontrado: '{primer_valor}'\n")

    # Botón imagen: ASP.NET espera coordenadas .x/.y en vez de __EVENTTARGET.
    payload3["_ctl0:ContentPlaceHolder1:IbtnConsultar.x"] = "10"
    payload3["_ctl0:ContentPlaceHolder1:IbtnConsultar.y"] = "10"

    resp3 = session.post(URL, headers=HEADERS, data=payload3, timeout=30)
    resp3.raise_for_status()
    resp3.encoding = resp3.apparent_encoding

    with open("test_resultados.html", "w", encoding="utf-8") as f:
        f.write(resp3.text)
    print("HTML de resultados guardado en: test_resultados.html")

    soup3 = BeautifulSoup(resp3.text, "html.parser")
    tablas = soup3.find_all("table")
    print(f"\nNúmero de <table> en la respuesta de resultados: {len(tablas)}")
    for i, tabla in enumerate(tablas):
        filas = tabla.find_all("tr")
        print(f"  tabla[{i}] id='{tabla.get('id')}' filas={len(filas)}")


if __name__ == "__main__":
    main()
