"""
Pruebas de validación del conjunto limpio — Proyecto 1

Verifica que `data/dataset_limpio.csv` cumple las reglas de calidad
establecidas en el plan de limpieza (CheckPoint.md, Parte 2). Cada
función es una prueba independiente que imprime PASA/FALLA con el
detalle de lo encontrado; al final se resume cuántas pasaron.

No corrige nada: si una prueba falla, es una señal de que algo cambió
en el pipeline de limpieza (`limpieza.py`) y hay que revisarlo, no un
lugar para parchar el dato.

Uso: python validacion.py
"""

import re
import sys

import pandas as pd

DATA_PATH = "../data/dataset_limpio.csv"

DEPARTAMENTOS_VALIDOS = {
    "ALTA VERAPAZ", "BAJA VERAPAZ", "CHIMALTENANGO", "CHIQUIMULA", "EL PROGRESO",
    "ESCUINTLA", "GUATEMALA", "HUEHUETENANGO", "IZABAL", "JALAPA", "JUTIAPA",
    "PETEN", "QUETZALTENANGO", "QUICHE", "RETALHULEU", "SACATEPEQUEZ",
    "SAN MARCOS", "SANTA ROSA", "SOLOLA", "SUCHITEPEQUEZ", "TOTONICAPAN", "ZACAPA",
}

NIVELES_FUERA_DE_ALCANCE = {"UNIVERSIDAD", "ADMINISTRATIVOS"}

COLUMNAS_TEXTO = [
    "CODIGO", "DISTRITO", "DEPARTAMENTO", "MUNICIPIO", "ESTABLECIMIENTO",
    "DIRECCION", "TELEFONO", "SUPERVISOR", "DIRECTOR", "NIVEL", "SECTOR",
    "AREA", "STATUS", "MODALIDAD", "JORNADA", "PLAN", "DEPARTAMENTAL",
]

COLUMNAS_CATEGORICAS = [
    "DEPARTAMENTO", "NIVEL", "SECTOR", "AREA", "STATUS", "MODALIDAD", "JORNADA", "PLAN",
]

resultados = []
advertencias = []


def prueba(nombre):
    """Decorador: registra el resultado (True/False, mensaje) de cada prueba.
    Cuenta para el pass/fail del exit code."""
    def wrapper(func):
        def ejecutar(df):
            try:
                ok, detalle = func(df)
            except Exception as e:
                ok, detalle = False, f"Error al ejecutar la prueba: {e}"
            resultados.append((nombre, ok, detalle))
            estado = "PASA" if ok else "FALLA"
            print(f"[{estado}] {nombre} — {detalle}")
        return ejecutar
    return wrapper


def advertencia(nombre):
    """Como `prueba`, pero para limitaciones conocidas y aceptadas: se reporta
    el resultado pero NO cuenta para el pass/fail ni el exit code."""
    def wrapper(func):
        def ejecutar(df):
            try:
                ok, detalle = func(df)
            except Exception as e:
                ok, detalle = False, f"Error al ejecutar la prueba: {e}"
            advertencias.append((nombre, ok, detalle))
            estado = "OK" if ok else "ADVERTENCIA (conocida)"
            print(f"[{estado}] {nombre} — {detalle}")
        return ejecutar
    return wrapper


@prueba("Sin registros duplicados exactos")
def test_sin_duplicados_exactos(df):
    n = df.duplicated().sum()
    return n == 0, f"{n} filas duplicadas exactas encontradas"


@prueba("Sin duplicados por CODIGO (llave primaria)")
def test_sin_duplicados_codigo(df):
    n = df.duplicated(subset=["CODIGO"]).sum()
    return n == 0, f"{n} valores de CODIGO repetidos"


@prueba("Sin espacios al inicio o final en columnas de texto")
def test_sin_espacios_extremos(df):
    columnas_con_problema = []
    for col in COLUMNAS_TEXTO:
        valores = df[col].dropna().astype(str)
        con_espacios = valores != valores.str.strip()
        if con_espacios.any():
            columnas_con_problema.append((col, int(con_espacios.sum())))
    ok = len(columnas_con_problema) == 0
    detalle = "ninguna columna con espacios extremos" if ok else f"columnas afectadas: {columnas_con_problema}"
    return ok, detalle


@prueba("TELEFONO en formato consistente (8 dígitos o NaN)")
def test_formato_telefono(df):
    no_nulos = df["TELEFONO"].dropna().astype(str)
    patron = re.compile(r"^\d{8}$")
    invalidos = (~no_nulos.str.fullmatch(patron.pattern)).sum()
    return invalidos == 0, f"{invalidos} valores de TELEFONO no nulos que no son exactamente 8 dígitos"


@prueba("CODIGO cumple el formato ##-##-####-##")
def test_formato_codigo(df):
    patron = re.compile(r"^\d{2}-\d{2}-\d{4}-\d{2}$")
    invalidos = (~df["CODIGO"].astype(str).str.fullmatch(patron.pattern)).sum()
    return invalidos == 0, f"{invalidos} valores de CODIGO fuera de formato"


@prueba("DISTRITO cumple alguno de los formatos válidos, o es NaN")
def test_formato_distrito(df):
    no_nulos = df["DISTRITO"].dropna().astype(str)
    pat_a = re.compile(r"^\d{2}-\d{2}-\d{4}$")
    pat_b = re.compile(r"^\d{2}-\d{3}$")
    validos = no_nulos.str.fullmatch(pat_a.pattern) | no_nulos.str.fullmatch(pat_b.pattern)
    invalidos = (~validos).sum()
    return invalidos == 0, f"{invalidos} valores de DISTRITO no nulos fuera de los formatos válidos"


@prueba("DEPARTAMENTO pertenece al catálogo de 22 departamentos")
def test_catalogo_departamento(df):
    encontrados = set(df["DEPARTAMENTO"].dropna().unique())
    fuera_de_catalogo = encontrados - DEPARTAMENTOS_VALIDOS
    return len(fuera_de_catalogo) == 0, f"valores fuera de catálogo: {fuera_de_catalogo or 'ninguno'}"


@prueba("NIVEL no incluye categorías fuera de alcance (UNIVERSIDAD, ADMINISTRATIVOS)")
def test_nivel_en_alcance(df):
    encontrados = set(df["NIVEL"].dropna().unique())
    fuera_de_alcance = encontrados & NIVELES_FUERA_DE_ALCANCE
    return len(fuera_de_alcance) == 0, f"categorías fuera de alcance encontradas: {fuera_de_alcance or 'ninguna'}"


@prueba("AREA no contiene 'SIN ESPECIFICAR' (debió mapearse a NaN)")
def test_area_sin_especificar(df):
    n = (df["AREA"] == "SIN ESPECIFICAR").sum()
    return n == 0, f"{n} registros con AREA='SIN ESPECIFICAR' sin convertir a NaN"


@advertencia("CODIGO/DISTRITO/TELEFONO no se corrompen si el CSV se carga sin dtype=str")
def test_tipos_de_dato(df):
    # Limitación conocida y aceptada (documentada en CheckPoint.md y en el libro
    # de códigos §2): TELEFONO queda compuesta solo de dígitos tras la limpieza,
    # así que pandas la infiere float64 si se recarga el CSV sin fijar dtype,
    # corrompiendo el valor (22324443 -> 22324443.0). Se confirmó que ni siquiera
    # `quoting=csv.QUOTE_NONNUMERIC` al guardar evita esto: pandas infiere el tipo
    # por contenido al leer, sin importar las comillas. No cuenta como falla de la
    # suite — es una advertencia para recordar cargar siempre con dtype=str.
    df_sin_dtype = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    columnas_identificador = ["CODIGO", "DISTRITO", "TELEFONO"]
    inferidas_como_numero = [col for col in columnas_identificador if df_sin_dtype[col].dtype != object]
    ok = len(inferidas_como_numero) == 0
    detalle = (
        "las tres siguen siendo texto sin forzar dtype"
        if ok else
        f"columnas que pandas infiere como numéricas si no se fija dtype=str: {inferidas_como_numero} "
        f"(cargar siempre con dtype=str, ver libro de códigos §2)"
    )
    return ok, detalle


@prueba("Sin categorías duplicadas por diferencias de escritura")
def test_sin_categorias_duplicadas_por_escritura(df):
    columnas_con_problema = []
    for col in COLUMNAS_CATEGORICAS:
        original = df[col].dropna().astype(str)
        normalizado = original.str.strip().str.upper()
        if original.nunique() != normalizado.nunique():
            columnas_con_problema.append(col)
    ok = len(columnas_con_problema) == 0
    detalle = "ningún colapso de categorías al normalizar" if ok else f"columnas con variantes: {columnas_con_problema}"
    return ok, detalle


@prueba("Sin nulos disfrazados conocidos (S/D, N/A, -, ., vacío) en columnas de texto")
def test_sin_nulos_disfrazados(df):
    tokens_nulos = {"", "-", "--", "---", ".", "..", "?", "N/A", "NA", "NULL",
                    "NONE", "S/D", "SD", "SIN DATO", "SIN DATOS", "NO APLICA", "N.A.", "NAN"}
    columnas_con_problema = []
    for col in COLUMNAS_TEXTO:
        valores = df[col].dropna().astype(str).str.strip().str.upper()
        n = valores.isin(tokens_nulos).sum()
        if n > 0:
            columnas_con_problema.append((col, int(n)))
    ok = len(columnas_con_problema) == 0
    detalle = "ningún nulo disfrazado sin normalizar" if ok else f"columnas afectadas: {columnas_con_problema}"
    return ok, detalle


def main():
    print(f"Cargando dataset limpio desde: {DATA_PATH} (dtype=str)...")
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig", dtype=str)
    print(f"Registros: {df.shape[0]}, Variables: {df.shape[1]}\n")

    pruebas = [
        test_sin_duplicados_exactos,
        test_sin_duplicados_codigo,
        test_sin_espacios_extremos,
        test_formato_telefono,
        test_formato_codigo,
        test_formato_distrito,
        test_catalogo_departamento,
        test_nivel_en_alcance,
        test_area_sin_especificar,
        test_tipos_de_dato,
        test_sin_categorias_duplicadas_por_escritura,
        test_sin_nulos_disfrazados,
    ]
    for test in pruebas:
        test(df)

    n_pasa = sum(1 for _, ok, _ in resultados if ok)
    n_total = len(resultados)
    print(f"\nResumen: {n_pasa}/{n_total} pruebas pasaron.")

    if advertencias:
        n_ok_adv = sum(1 for _, ok, _ in advertencias if ok)
        print(f"Advertencias (no cuentan para el resultado): {n_ok_adv}/{len(advertencias)} sin novedad.")

    if n_pasa != n_total:
        sys.exit(1)


if __name__ == "__main__":
    main()
