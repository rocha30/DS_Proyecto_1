"""
Paso 0c — Exploración con Playwright (navegador real) de un departamento
de prueba, para ver:
  1) si el cascade Departamento -> Municipio funciona en un navegador real
     (confirmando que el bloqueo anterior era de Incapsula sobre POSTs
     "crudos" hechos con requests),
  2) cómo luce la tabla de resultados y si hay paginación,
antes de escribir el scraper definitivo de los 22 departamentos.

Guarda capturas de pantalla y el HTML de resultados para inspección.
"""

from playwright.sync_api import sync_playwright

URL = "http://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/"
DEPARTAMENTO_PRUEBA = "SACATEPEQUEZ"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.screenshot(path="pw_01_inicial.png")

        # Seleccionar departamento -> dispara el postback de cascada.
        page.select_option(
            "#_ctl0_ContentPlaceHolder1_cmbDepartamento",
            label=DEPARTAMENTO_PRUEBA,
        )
        page.wait_for_load_state("networkidle")
        page.screenshot(path="pw_02_tras_departamento.png")

        municipio_opciones = page.eval_on_selector_all(
            "#_ctl0_ContentPlaceHolder1_cmbMunicipio option",
            "opts => opts.map(o => ({value: o.value, texto: o.textContent}))",
        )
        print("=" * 80)
        print(f"MUNICIPIOS tras seleccionar '{DEPARTAMENTO_PRUEBA}':")
        print("=" * 80)
        for opt in municipio_opciones:
            print(f"  value='{opt['value']}'  texto='{opt['texto']}'")
        print()

        # Dejar Nivel/Sector/Plan/Modalidad en TODOS (ya son default) y
        # click en el botón de buscar (IbtnConsultar).
        page.click("#_ctl0_ContentPlaceHolder1_IbtnConsultar")
        page.wait_for_load_state("networkidle")
        page.screenshot(path="pw_03_resultados.png", full_page=True)

        html = page.content()
        with open("pw_resultados.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML de resultados guardado en: pw_resultados.html")
        print("Capturas guardadas: pw_01_inicial.png, pw_02_tras_departamento.png, "
              "pw_03_resultados.png")

        browser.close()


if __name__ == "__main__":
    main()
