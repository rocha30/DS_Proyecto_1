
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
    df["SUPERVISOR"] = df["SUPERVISOR"].astype(str).str.strip().str.upper()
    df["SUPERVISOR"] = df["SUPERVISOR"].str.replace(r"\s+", " ", regex=True)
    
    # Mapear strings nulos a NaN
    df.loc[df["SUPERVISOR"].isin(["nan", "None", "", "S/D"]), "SUPERVISOR"] = np.nan
    print("[OK] Limpieza de columna SUPERVISOR completada.")
    return df


def limpiar_establecimiento(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza espacios múltiples dentro de la columna ESTABLECIMIENTO.
    REGLA: No corregir ortografía ni alterar el contenido lingüístico original.
    """
    df = df.copy()
    # Asegurar que sea texto
    df["ESTABLECIMIENTO"] = df["ESTABLECIMIENTO"].astype(str).str.strip().str.upper()
    # Estandarizar múltiples espacios consecutivos a uno solo
    df["ESTABLECIMIENTO"] = df["ESTABLECIMIENTO"].str.replace(r"\s+", " ", regex=True)
    print("[OK] Limpieza de columna ESTABLECIMIENTO completada.")
    return df


def limpiar_direccion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza espacios y mapea nulos disfrazados de la columna DIRECCION.
    REGLA: No corregir ortografía ni alterar el contenido lingüístico original.
    """
    df = df.copy()
    df["DIRECCION"] = df["DIRECCION"].astype(str).str.strip().str.upper()
    df["DIRECCION"] = df["DIRECCION"].str.replace(r"\s+", " ", regex=True)
    
    # Mapear nulos disfrazados
    df.loc[df["DIRECCION"].isin(["nan", "None", "", "S/D", "-", "."]), "DIRECCION"] = np.nan
    print("[OK] Limpieza de columna DIRECCION completada.")
    return df


# =====================================================================
# SECCIÓN 2: MARCOS DE TRABAJO (TODO) — PERSONA B
# =====================================================================

def limpiar_director(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO (Persona B):
    - Convertir placeholders de guiones ('----', '----------') o '.' a NaN.
    - Limpiar espacios sobrantes (.str.strip() y reemplazar espacios dobles).
    - Convertir a MAYÚSCULAS.
    """
    df = df.copy()
    # === IMPLEMENTAR AQUÍ ===
    print("[TODO] Persona B: Falta implementar limpieza de DIRECTOR. Por ahora se mantiene igual.")
    return df


def limpiar_telefono(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO (Persona B):
    - Convertir 'S/D' o vacíos a NaN.
    - Remover guiones y espacios intermedios.
    - Manejar los multivalores en celdas (extraer el primer número válido de 8 dígitos).
    """
    df = df.copy()
    # === IMPLEMENTAR AQUÍ ===
    print("[TODO] Persona B: Falta implementar limpieza de TELEFONO. Por ahora se mantiene igual.")
    return df


def limpiar_catalogos(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO (Persona B):
    - Limpiar variables categóricas: NIVEL, SECTOR, AREA, STATUS, MODALIDAD, JORNADA, PLAN.
    - Hacer .str.strip() y .str.upper().
    - Filtrar el dataset para remover registros de NIVEL que sean 'UNIVERSIDAD' o 'ADMINISTRATIVOS'.
    - Convertir 'SIN ESPECIFICAR' de la columna AREA a NaN (si corresponde).
    """
    df = df.copy()
    # === IMPLEMENTAR AQUÍ ===
    print("[TODO] Persona B: Falta implementar limpieza de CATÁLOGOS. Por ahora se mantiene igual.")
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
