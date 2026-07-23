"""
Detección de duplicados parciales — Proyecto 1

Busca pares de registros que probablemente correspondan al mismo
establecimiento físico pero que NO son duplicados exactos de fila
(ya se confirmó 0 duplicados exactos y 0 duplicados por CODIGO en el
diagnóstico). Se usa similitud de cadenas (RapidFuzz) sobre
ESTABLECIMIENTO y DIRECCION, en vez de comparar solo por igualdad
exacta de string.

No se elimina ni fusiona ningún registro automáticamente: el script
solo genera un reporte (`data/posibles_duplicados_parciales.csv`) para
revisión manual, como pide el enunciado.

Estrategia:
1. Bloqueo por (DEPARTAMENTO, MUNICIPIO) para no comparar 94,530^2 pares.
2. Dentro de cada bloque, calcular similitud de ESTABLECIMIENTO con
   rapidfuzz.process.cdist (token_sort_ratio, insensible a orden de
   palabras).
3. Quedarse con pares con score >= UMBRAL_NOMBRE que NO sean ya
   duplicados exactos de ESTABLECIMIENTO+DIRECCION (esos 9,530 pares ya
   están documentados en CheckPoint.md como mismo plantel con varios
   CODIGO por nivel/jornada/plan).
4. Para esos candidatos, calcular también similitud de DIRECCION y
   reportar ambos scores para que la revisión manual decida.
"""

import pandas as pd
from rapidfuzz import fuzz, process

INPUT_PATH = "../data/dataset_limpio.csv"
OUTPUT_PARES = "../data/posibles_duplicados_parciales_pares.csv"
OUTPUT_GRUPOS = "../data/posibles_duplicados_parciales_grupos.csv"

# Umbral amplio para generar candidatos por bloque (barato, sobre ESTABLECIMIENTO).
# El umbral fino (nombre + dirección) que decide qué pares cuentan como
# "posible duplicado" se aplica después, sobre ese universo de candidatos.
UMBRAL_NOMBRE = 90

# Umbrales finales para considerar un par como posible duplicado parcial real
# (no solo dos escuelas rurales que comparten palabras genéricas del nombre).
# Se calibraron revisando muestras: en (95, 90) los pares observados son en su
# mayoría el mismo plantel con variantes de puntuación en la dirección
# (p. ej. "3A AVENIDA" vs "3A. AVENIDA") o distinto NIVEL/JORNADA — el mismo
# patrón que los 9,530 pares de nombre+dirección exactos ya documentados en
# el diagnóstico, pero con una diferencia mínima de formato que impide el
# match por igualdad exacta.
UMBRAL_NOMBRE_FINAL = 95
UMBRAL_DIRECCION_FINAL = 90


def encontrar_pares_por_bloque(bloque: pd.DataFrame) -> list[dict]:
    """Compara todos los pares dentro de un bloque (mismo depto+municipio)."""
    nombres = bloque["ESTABLECIMIENTO"].tolist()
    n = len(nombres)
    if n < 2:
        return []

    matriz = process.cdist(nombres, nombres, scorer=fuzz.token_sort_ratio)

    pares = []
    for i in range(n):
        for j in range(i + 1, n):
            score_nombre = matriz[i, j]
            if score_nombre < UMBRAL_NOMBRE:
                continue

            fila_i = bloque.iloc[i]
            fila_j = bloque.iloc[j]

            nombre_identico = fila_i["ESTABLECIMIENTO"] == fila_j["ESTABLECIMIENTO"]
            direccion_i = fila_i["DIRECCION"] if pd.notna(fila_i["DIRECCION"]) else ""
            direccion_j = fila_j["DIRECCION"] if pd.notna(fila_j["DIRECCION"]) else ""
            direccion_identica = direccion_i == direccion_j and direccion_i != ""

            # Ya documentado en el diagnóstico (§5/§8-12): mismo nombre + misma
            # dirección exactos, distinto CODIGO -> no es el caso que buscamos aquí.
            if nombre_identico and direccion_identica:
                continue

            score_direccion = fuzz.token_sort_ratio(direccion_i, direccion_j) if direccion_i and direccion_j else 0

            pares.append({
                "CODIGO_1": fila_i["CODIGO"],
                "CODIGO_2": fila_j["CODIGO"],
                "DEPARTAMENTO": fila_i["DEPARTAMENTO"],
                "MUNICIPIO": fila_i["MUNICIPIO"],
                "ESTABLECIMIENTO_1": fila_i["ESTABLECIMIENTO"],
                "ESTABLECIMIENTO_2": fila_j["ESTABLECIMIENTO"],
                "score_nombre": round(score_nombre, 1),
                "DIRECCION_1": direccion_i,
                "DIRECCION_2": direccion_j,
                "score_direccion": round(score_direccion, 1),
                "NIVEL_1": fila_i["NIVEL"],
                "NIVEL_2": fila_j["NIVEL"],
            })

    return pares


class UnionFind:
    """Estructura simple para agrupar CODIGOs conectados por algún par candidato."""

    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def agrupar_pares(pares_finales: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte pares en grupos (componentes conexas): si A~B y B~C, los tres
    quedan en el mismo grupo. Es más representativo que contar pares, porque
    un mismo plantel con 5 niveles genera 10 pares pero es 1 solo grupo real.
    """
    uf = UnionFind()
    for _, r in pares_finales.iterrows():
        uf.union(r["CODIGO_1"], r["CODIGO_2"])

    codigo_a_establecimiento = df.set_index("CODIGO")["ESTABLECIMIENTO"]
    codigo_a_nivel = df.set_index("CODIGO")["NIVEL"]

    miembros_por_grupo = {}
    for codigo in uf.parent:
        raiz = uf.find(codigo)
        miembros_por_grupo.setdefault(raiz, []).append(codigo)

    filas = []
    for i, (_, miembros) in enumerate(sorted(miembros_por_grupo.items()), start=1):
        nombre_rep = codigo_a_establecimiento.get(miembros[0], "")
        filas.append({
            "grupo_id": i,
            "n_registros": len(miembros),
            "codigos": ", ".join(sorted(miembros)),
            "establecimiento_representativo": nombre_rep,
            "niveles": ", ".join(sorted(set(codigo_a_nivel.get(c, "") for c in miembros))),
            # Siglas genéricas (EORM = "Escuela Oficial Rural Mixta", etc.) se repiten
            # como nombre oficial de cientos de escuelas rurales distintas: que dos
            # registros compartan ese nombre corto no implica que sean el mismo
            # plantel. Se marcan para que la revisión manual les baje prioridad.
            "nombre_generico_sospechoso": len(nombre_rep) <= 6,
        })

    return pd.DataFrame(filas).sort_values("n_registros", ascending=False)


def main():
    print(f"Cargando dataset limpio desde: {INPUT_PATH}...")
    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig", dtype=str)
    print(f"Registros: {df.shape[0]}")

    todos_los_pares = []
    bloques = df.groupby(["DEPARTAMENTO", "MUNICIPIO"], dropna=False)
    print(f"Comparando dentro de {bloques.ngroups} bloques (DEPARTAMENTO, MUNICIPIO)...")

    for _, bloque in bloques:
        todos_los_pares.extend(encontrar_pares_por_bloque(bloque))

    pares = pd.DataFrame(todos_los_pares)
    print(f"[INFO] {len(pares)} pares candidatos con score ESTABLECIMIENTO >= {UMBRAL_NOMBRE} "
          f"(universo amplio, solo en memoria — no se guarda, es intermedio).")

    pares_finales = pares[
        (pares["score_nombre"] >= UMBRAL_NOMBRE_FINAL) &
        (pares["score_direccion"] >= UMBRAL_DIRECCION_FINAL)
    ].sort_values(["score_nombre", "score_direccion"], ascending=False)
    pares_finales.to_csv(OUTPUT_PARES, index=False, encoding="utf-8-sig")

    grupos = agrupar_pares(pares_finales, df)
    grupos.to_csv(OUTPUT_GRUPOS, index=False, encoding="utf-8-sig")

    n_genericos = grupos["nombre_generico_sospechoso"].sum()
    n_confiables = len(grupos) - n_genericos

    print(f"[OK] {len(pares_finales)} pares cumplen el umbral final "
          f"(nombre >= {UMBRAL_NOMBRE_FINAL} y dirección >= {UMBRAL_DIRECCION_FINAL}), "
          f"agrupados en {len(grupos)} posibles duplicados parciales "
          f"({grupos['n_registros'].sum()} registros involucrados).")
    print(f"  - {n_confiables} grupos con nombre propio (candidatos de mayor confianza).")
    print(f"  - {n_genericos} grupos con nombre genérico tipo sigla (EORM, EODP, etc.) — "
          f"probablemente escuelas distintas que comparten nombre oficial genérico, no duplicados reales.")
    print(f"Reporte de grupos guardado en: {OUTPUT_GRUPOS}")
    print("Ningún registro fue eliminado ni fusionado automáticamente — esto es solo un reporte para revisión manual.")


if __name__ == "__main__":
    main()
