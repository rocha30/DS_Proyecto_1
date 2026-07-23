
"""
Script de Limpieza — Proyecto 1
Este script ejecuta el proceso de limpieza y normalización de datos.

División del trabajo (Opción 2):
- Persona A: Estructura Geográfica e Identificación (Implementado en este script).
- Persona B: Catálogos e Información de Contacto (Marcos de función TODO pendientes).
"""

import re
import numpy as np
import pandas as pd

# Rutas de datos
INPUT_PATH = "../data/dataset.csv"
OUTPUT_PATH = "../data/dataset_limpio.csv"


# =====================================================================
# SECCIÓN 1: FUNCIONES DE LIMPIEZA — PERSONA A
# =====================================================================

def limpiar_codigo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida y limpia la columna CODIGO.
    Verifica que cumpla con el patrón estándar ##-##-####-##.
    """
    df = df.copy()
    df["CODIGO"] = df["CODIGO"].astype(str).str.strip()
    
    # Validación de formato
    patron = re.compile(r"^\d{2}-\d{2}-\d{4}-\d{2}$")
    validos = df["CODIGO"].str.fullmatch(patron.pattern)
    invalidos_n = (~validos).sum()
    
    if invalidos_n > 0:
        print(f"[ADVERTENCIA] Se encontraron {invalidos_n} códigos con formato inválido.")
    else:
        print("[OK] Todos los códigos tienen el formato estándar ##-##-####-##.")
        
    return df


def limpiar_departamento(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unifica la columna DEPARTAMENTO reemplazando 'CIUDAD CAPITAL' por 'GUATEMALA'.
    """
    df = df.copy()
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].astype(str).str.strip().str.upper()
    
    # Mapeo de unificación
    df["DEPARTAMENTO"] = df["DEPARTAMENTO"].replace("CIUDAD CAPITAL", "GUATEMALA")
    print("[OK] Unificación de DEPARTAMENTO completada (CIUDAD CAPITAL -> GUATEMALA).")
    return df


def limpiar_departamental(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia espacios en la columna DEPARTAMENTAL manteniendo las tildes oficiales.
    """
    df = df.copy()
    df["DEPARTAMENTAL"] = df["DEPARTAMENTAL"].astype(str).str.strip().str.upper()
    print("[OK] Limpieza de columna DEPARTAMENTAL completada.")
    return df


def limpiar_municipio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza espacios y caso de la columna MUNICIPIO.
    """
    df = df.copy()
    df["MUNICIPIO"] = df["MUNICIPIO"].astype(str).str.strip().str.upper()
    # Eliminar múltiples espacios consecutivos
    df["MUNICIPIO"] = df["MUNICIPIO"].str.replace(r"\s+", " ", regex=True)
    print("[OK] Limpieza de columna MUNICIPIO completada.")
    return df


def limpiar_distrito(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida y limpia la columna DISTRITO.
    Estandariza los distritos incompletos o inválidos a NaN.
    Patrones válidos: ##-##-#### o ##-###.
    """
    df = df.copy()
    
    # Asegurar que sea str o NaN
    df["DISTRITO"] = df["DISTRITO"].astype(str).str.strip()
    
    # Manejar nulos iniciales de pandas
    df.loc[df["DISTRITO"].isin(["nan", "None", "", "S/D"]), "DISTRITO"] = np.nan
    
    no_nulos = df["DISTRITO"].notna()
    
    # Patrones válidos
    pat_a = re.compile(r"^\d{2}-\d{2}-\d{4}$")
    pat_b = re.compile(r"^\d{2}-\d{3}$")
    
    validos = df.loc[no_nulos, "DISTRITO"].str.fullmatch(pat_a.pattern) | \
              df.loc[no_nulos, "DISTRITO"].str.fullmatch(pat_b.pattern)
              
    # Identificar registros no válidos
    invalidos_indices = df.loc[no_nulos][~validos].index
    
    if len(invalidos_indices) > 0:
        print(f"[INFO] Convirtiendo {len(invalidos_indices)} distritos con formato incompleto a NaN (ej: 01-, 17-).")
        df.loc[invalidos_indices, "DISTRITO"] = np.nan
        
    print("[OK] Limpieza de columna DISTRITO completada.")
    return df


def limpiar_supervisor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza espacios del nombre de SUPERVISOR y mapea vacíos a NaN.
    """
    df = df.copy()
    df["SUPERVISOR"] = df["SUPERVISOR"].astype(str).str.strip()

    # Mapear strings nulos a NaN ANTES de pasar a mayúsculas: str(NaN) es "nan"
    # en minúscula, y .str.upper() lo convertiría en el texto literal "NAN" que
    # ya no calzaría con esta comparación si se hiciera después.
    df.loc[df["SUPERVISOR"].isin(["nan", "None", "", "S/D"]), "SUPERVISOR"] = np.nan

    no_nulos = df["SUPERVISOR"].notna()
    df.loc[no_nulos, "SUPERVISOR"] = df.loc[no_nulos, "SUPERVISOR"] \
        .str.upper().str.replace(r"\s+", " ", regex=True)
    print("[OK] Limpieza de columna SUPERVISOR completada.")
    return df


def limpiar_establecimiento(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza espacios múltiples dentro de la columna ESTABLECIMIENTO.
    REGLA: No corregir ortografía ni alterar el contenido lingüístico original.
    """
    df = df.copy()
    df["ESTABLECIMIENTO"] = df["ESTABLECIMIENTO"].astype(str).str.strip()

    # Mapear nulos disfrazados a NaN ANTES de pasar a mayúsculas (ver nota en
    # limpiar_supervisor: str(NaN).upper() == "NAN" ya no calza con "nan").
    df.loc[df["ESTABLECIMIENTO"].isin(["nan", "None", "", "S/D"]), "ESTABLECIMIENTO"] = np.nan

    no_nulos = df["ESTABLECIMIENTO"].notna()
    df.loc[no_nulos, "ESTABLECIMIENTO"] = df.loc[no_nulos, "ESTABLECIMIENTO"] \
        .str.upper().str.replace(r"\s+", " ", regex=True)
    print("[OK] Limpieza de columna ESTABLECIMIENTO completada.")
    return df


def limpiar_direccion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza espacios y mapea nulos disfrazados de la columna DIRECCION.
    REGLA: No corregir ortografía ni alterar el contenido lingüístico original.
    """
    df = df.copy()
    df["DIRECCION"] = df["DIRECCION"].astype(str).str.strip()

    # Mapear nulos disfrazados a NaN ANTES de pasar a mayúsculas (ver nota en
    # limpiar_supervisor: str(NaN).upper() == "NAN" ya no calza con "nan"),
    # incluyendo guiones de largo variable ("-", "--", "---", ...).
    patron_guiones = re.compile(r"^-+$")
    es_nulo_disfrazado = df["DIRECCION"].isin(["nan", "None", "", "S/D", "."]) | \
        df["DIRECCION"].str.fullmatch(patron_guiones.pattern)
    df.loc[es_nulo_disfrazado, "DIRECCION"] = np.nan

    no_nulos = df["DIRECCION"].notna()
    df.loc[no_nulos, "DIRECCION"] = df.loc[no_nulos, "DIRECCION"] \
        .str.upper().str.replace(r"\s+", " ", regex=True)
    print("[OK] Limpieza de columna DIRECCION completada.")
    return df


# =====================================================================
# SECCIÓN 2: MARCOS DE TRABAJO (TODO) — PERSONA B
# =====================================================================

def limpiar_director(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte placeholders (guiones, puntos, 'S/D', vacíos) de DIRECTOR a NaN.
    Para nombres válidos: normaliza espacios y convierte a MAYÚSCULAS.
    """
    df = df.copy()
    df["DIRECTOR"] = df["DIRECTOR"].astype(str).str.strip()

    # Placeholders: strings hechos únicamente de guiones/puntos/comas/ceros/espacios,
    # caracteres de encoding roto (U+FFFD), tokens conocidos de "sin dato", o nulos disfrazados
    patron_placeholder = re.compile(r"^[-.,\s0]+$")
    patron_encoding_roto = re.compile(r"^�+$")
    tokens_sin_dato = ["nan", "None", "", "S/D", "SIN DATO", "SIN DATOS", "NO APLICA"]
    es_placeholder = df["DIRECTOR"].str.upper().isin([t.upper() for t in tokens_sin_dato]) | \
        df["DIRECTOR"].str.fullmatch(patron_placeholder.pattern) | \
        df["DIRECTOR"].str.fullmatch(patron_encoding_roto.pattern)
    n_placeholders = es_placeholder.sum()
    df.loc[es_placeholder, "DIRECTOR"] = np.nan

    no_nulos = df["DIRECTOR"].notna()
    df.loc[no_nulos, "DIRECTOR"] = df.loc[no_nulos, "DIRECTOR"] \
        .str.upper().str.replace(r"\s+", " ", regex=True)

    print(f"[OK] Limpieza de columna DIRECTOR completada ({n_placeholders} placeholders convertidos a NaN).")
    return df


def limpiar_telefono(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte 'S/D'/vacíos a NaN. Para celdas con varios teléfonos separados
    por comas, punto y coma, slash o 'Y', toma el primero que tenga
    exactamente 8 dígitos tras remover guiones/espacios. Si ninguno califica,
    asigna NaN.
    """
    df = df.copy()
    df["TELEFONO"] = df["TELEFONO"].astype(str).str.strip()
    df.loc[df["TELEFONO"].isin(["nan", "None", "", "S/D"]), "TELEFONO"] = np.nan

    patron_separadores = re.compile(r"[,;/]|\bY\b")

    def extraer_ocho_digitos(valor):
        if pd.isna(valor):
            return np.nan
        candidatos = patron_separadores.split(valor)
        for candidato in candidatos:
            solo_digitos = re.sub(r"\D", "", candidato)
            if len(solo_digitos) == 8:
                return solo_digitos
        return np.nan

    n_multivalor = df["TELEFONO"].notna().sum()
    df["TELEFONO"] = df["TELEFONO"].apply(extraer_ocho_digitos)
    n_validos = df["TELEFONO"].notna().sum()

    print(f"[OK] Limpieza de columna TELEFONO completada "
          f"({n_validos} de {n_multivalor} celdas no nulas resultaron en un teléfono de 8 dígitos válido).")
    return df


def limpiar_catalogos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza las variables de catálogo: NIVEL, SECTOR, AREA, STATUS,
    MODALIDAD, JORNADA, PLAN. Filtra registros de NIVEL fuera del alcance
    del proyecto (UNIVERSIDAD, ADMINISTRATIVOS) y mapea AREA='SIN ESPECIFICAR'
    a NaN.
    """
    df = df.copy()
    columnas_catalogo = ["NIVEL", "SECTOR", "AREA", "STATUS", "MODALIDAD", "JORNADA", "PLAN"]
    for columna in columnas_catalogo:
        df[columna] = df[columna].astype(str).str.strip().str.upper()

    registros_antes = df.shape[0]
    fuera_de_alcance = ["UNIVERSIDAD", "ADMINISTRATIVOS"]
    df = df[~df["NIVEL"].isin(fuera_de_alcance)].copy()
    print(f"[INFO] Se removieron {registros_antes - df.shape[0]} registros de NIVEL fuera de alcance "
          f"({', '.join(fuera_de_alcance)}).")

    n_sin_especificar = (df["AREA"] == "SIN ESPECIFICAR").sum()
    df.loc[df["AREA"] == "SIN ESPECIFICAR", "AREA"] = np.nan

    print(f"[OK] Limpieza de columnas de CATÁLOGOS completada "
          f"({n_sin_especificar} registros de AREA='SIN ESPECIFICAR' convertidos a NaN).")
    return df


# =====================================================================
# PIPELINE PRINCIPAL Y EXPORTACIÓN
# =====================================================================

def ejecutar_pipeline():
    print(f"Cargando dataset crudo desde: {INPUT_PATH}...")
    try:
        df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    except FileNotFoundError:
        # Intento de respaldo si corre desde otra ruta
        df = pd.read_csv("data/dataset.csv", encoding="utf-8-sig")
        
    print(f"Registros crudos iniciales: {df.shape[0]}")
    
    # 1. Aplicar Limpieza Persona A
    df = limpiar_codigo(df)
    df = limpiar_departamento(df)
    df = limpiar_departamental(df)
    df = limpiar_municipio(df)
    df = limpiar_distrito(df)
    df = limpiar_supervisor(df)
    df = limpiar_establecimiento(df)
    df = limpiar_direccion(df)
    
    # 2. Aplicar Limpieza Persona B (TODO)
    df = limpiar_director(df)
    df = limpiar_telefono(df)
    df = limpiar_catalogos(df)
    
    # Guardar resultado parcial
    print(f"Registros después de limpieza (Persona A aplicada): {df.shape[0]}")
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"Dataset guardado en: {OUTPUT_PATH}")


if __name__ == "__main__":
    ejecutar_pipeline()
