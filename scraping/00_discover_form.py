"""
Paso 0 — Reconocimiento del formulario de BUSCAESTABLECIMIENTO_GE (MINEDUC).

Objetivo: obtener los nombres reales de los controles HTML (selects, inputs
ocultos, botones que disparan __doPostBack) antes de armar el scraper real.
No hace ninguna búsqueda todavía, solo GET a la página principal y parseo.
"""

import re

import requests
from bs4 import BeautifulSoup

URL = "http://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

HIDDEN_FIELDS = ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION",
                  "__EVENTTARGET", "__EVENTARGUMENT")


def get_form_html():
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    return resp.text


def print_hidden_fields(soup):
    print("=" * 80)
    print("CAMPOS OCULTOS (__VIEWSTATE, etc.)")
    print("=" * 80)
    for name in HIDDEN_FIELDS:
        tag = soup.find("input", {"name": name})
        if tag is None:
            print(f"{name}: NO ENCONTRADO")
            continue
        value = tag.get("value", "")
        preview = value if len(value) <= 60 else f"{value[:60]}... ({len(value)} chars)"
        print(f"{name}: {preview}")
    print()


def print_selects(soup):
    print("=" * 80)
    print("<select> ENCONTRADOS (dropdowns)")
    print("=" * 80)
    selects = soup.find_all("select")
    if not selects:
        print("No se encontraron <select> en la página.")
    for sel in selects:
        name = sel.get("name")
        sel_id = sel.get("id")
        print(f"\n--- select name='{name}' id='{sel_id}' ---")
        options = sel.find_all("option")
        for opt in options:
            value = opt.get("value", "")
            text = opt.get_text(strip=True)
            print(f"  value='{value}'  texto='{text}'")
    print()


def print_postback_controls(soup):
    print("=" * 80)
    print("ELEMENTOS CON __doPostBack (botones/links)")
    print("=" * 80)
    pattern = re.compile(r"__doPostBack\(\s*'([^']*)'\s*,\s*'([^']*)'\s*\)")
    found = False
    for tag in soup.find_all(["a", "input", "button"]):
        for attr in ("href", "onclick"):
            value = tag.get(attr)
            if value and "__doPostBack" in value:
                match = pattern.search(value)
                target = match.group(1) if match else "?"
                argument = match.group(2) if match else "?"
                found = True
                print(f"tag=<{tag.name}> {attr}='{value}'")
                print(f"  -> EVENTTARGET='{target}'  EVENTARGUMENT='{argument}'")
    if not found:
        print("No se encontraron llamadas a __doPostBack en href/onclick.")
    print()


def print_buttons_and_inputs(soup):
    print("=" * 80)
    print("BOTONES / INPUTS SUBMIT (candidatos a disparar la búsqueda)")
    print("=" * 80)
    for tag in soup.find_all("input", {"type": ["submit", "button", "image"]}):
        print(f"name='{tag.get('name')}' id='{tag.get('id')}' "
              f"type='{tag.get('type')}' value='{tag.get('value')}'")
    for tag in soup.find_all("button"):
        print(f"<button> name='{tag.get('name')}' id='{tag.get('id')}' "
              f"texto='{tag.get_text(strip=True)}'")
    print()


def save_raw_html(html, path="mineduc_form_raw.html"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML crudo guardado en: {path}")


def main():
    html = get_form_html()
    soup = BeautifulSoup(html, "html.parser")

    print_hidden_fields(soup)
    print_selects(soup)
    print_postback_controls(soup)
    print_buttons_and_inputs(soup)
    save_raw_html(html)


if __name__ == "__main__":
    main()
