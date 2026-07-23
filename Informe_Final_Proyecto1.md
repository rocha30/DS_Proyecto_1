---
title: "Proyecto 1 — Obtención y Limpieza de los Datos"
subtitle: "Establecimientos educativos de Guatemala (MINEDUC) — CC3066 Data Science, Universidad del Valle de Guatemala"
date: "23 de julio de 2026"
---

# Proyecto 1. Obtención y Limpieza de los Datos

**Curso:** CC3066 — Data Science, Semestre II 2026
**Universidad del Valle de Guatemala, Facultad de Ingeniería, Departamento de Ciencias de la Computación**

**Integrantes:** Mario Rocha (23501), Juan Francisco Martínez (23617), Jonathan Zacarías (231104), Luis Pedro Lira (23669)

**Repositorio:** <https://github.com/rocha30/DS_Proyecto_1.git>

**Entregables incluidos en el repositorio:**

- Código de obtención (`scraping/`) y limpieza (`DPL/limpieza.py`, `DPL/duplicados_parciales.py`, `DPL/validacion.py`), y notebook de diagnóstico (`DPL/diagnostico.ipynb`).
- Datos crudos (`data/crudo/`, `data/dataset.csv`) y datos limpios (`data/dataset_limpio.csv`).
- Libro de códigos en markdown (`DPL/libro_codigos.md`) y en PDF (`DPL/libro_codigos.pdf`).
- Este documento (`Informe_Final_Proyecto1.md`), con el proceso completo: diagnóstico, plan de limpieza, limpieza aplicada, duplicados, validación e informe de calidad antes/después.

---

## 1. Obtención de los datos

**Fuente:** Sistema de consulta pública de establecimientos educativos del Ministerio de Educación de Guatemala (MINEDUC), `http://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/`.

**Método:** web scraping con Playwright (Chromium). El sitio es un formulario ASP.NET WebForms protegido por Incapsula, que bloquea peticiones `POST` sin un navegador real, por lo que no se pudo usar `requests`. Se automatizó una búsqueda por cada uno de los 23 valores del dropdown de Departamento (los 22 departamentos oficiales de Guatemala más `CIUDAD CAPITAL` como entrada administrativa separada del propio formulario), dejando el resto de filtros (Municipio, Nivel, Sector, Plan, Modalidad) en `TODOS` para no perder registros por una interpretación restrictiva del alcance "hasta diversificado" pedido en el enunciado — el filtro de nivel se aplicó después, en la limpieza (ver §4).

**Resultado:** 23 archivos CSV crudos (uno por departamento) en `data/crudo/`, unidos en `data/dataset.csv` con `pd.concat` sin pérdida ni duplicación de filas.

**Fecha de extracción:** 21 de julio de 2026.

---

## 2. Diagnóstico del estado inicial (datos crudos)

Análisis completo con código y tablas en `DPL/diagnostico.ipynb`; resumen razonado en `CheckPoint.md` (Parte 1). Resultados clave:

### 2.1 Registros y variables

**94,533 registros, 17 variables** en el conjunto crudo unido (23 CSV departamentales).

### 2.2 Tipo de dato

Las 17 columnas se infieren como texto (`str`) — correcto en todos los casos: `CODIGO`/`DISTRITO` tienen guiones y ceros a la izquierda (perderían información como entero), `TELEFONO` no es una magnitud numérica, y el resto es texto/categórico. **No se encontraron variables con tipo de dato incorrecto** en el crudo.

### 2.3 Valores faltantes por variable

| Variable | # faltantes reales | % | # faltantes disfrazados adicionales |
|---|---|---|---|
| DIRECTOR | 27,739 | 29.34% | 2,057 (`"----"`, `"S/D"`, etc.) |
| TELEFONO | 27,514 | 29.11% | 133 (`"S/D"`) |
| SUPERVISOR | 10,702 | 11.32% | 0 |
| DISTRITO | 10,694 | 11.31% | 0 |
| DIRECCION | 863 | 0.91% | 22 |
| ESTABLECIMIENTO | 15 | 0.02% | 0 |
| Resto (11 variables) | 0 | 0% | 0 |

Tokens de faltante disfrazado buscados: cadenas vacías, `"-"`/`"--"`/`"---"` (guiones de largo variable), `"."`, `".."`, `"?"`, `"N/A"`, `"NA"`, `"NULL"`, `"None"`, `"S/D"`, `"SD"`, `"SIN DATO(S)"`, `"NO APLICA"`, `"N.A."`.

**Total de celdas faltantes (reales + disfrazadas) en el crudo: 79,739 de 1,607,061 celdas (4.96%). Variables con al menos un faltante: 6 de 17.**

### 2.4 Valores únicos

`CODIGO` es único en las 94,533 filas (llave candidata). Variables categóricas sin variantes de mayúsculas/espacios escondiendo duplicados de categoría (verificado: `nunique()` no cambia al normalizar `strip().upper()`). Detalle completo por variable en `CheckPoint.md` §4.

### 2.5 Registros duplicados exactos

**0 duplicados de fila exacta, 0 duplicados por `CODIGO`.** Se encontraron **9,530 pares** con mismo `ESTABLECIMIENTO`+`DIRECCION` pero distinto `CODIGO` — no son errores por sí solos (un mismo plantel físico puede tener varios códigos por nivel/jornada/plan distintos); se dejaron para revisión, no se dedujeron en la limpieza.

### 2.6 Valores fuera de dominio o inconsistentes

`DEPARTAMENTO`: sin valores fuera del catálogo de 23 entradas del dropdown (22 departamentos + `CIUDAD CAPITAL`, que geográficamente es el mismo departamento de Guatemala — ver §4). `DISTRITO`: formato mixto, 79 valores incompletos (`"01-"`, `"17-"`, …). `NIVEL`: incluye `UNIVERSIDAD` (1) y `ADMINISTRATIVOS` (2), fuera del alcance pedagógico "hasta diversificado" porque se consultó Nivel=`TODOS` durante el scraping.

### 2.7 Formatos inconsistentes

| Variable | Problema | # afectados |
|---|---|---|
| ESTABLECIMIENTO | Espacios internos dobles o más | 4,676 |
| DIRECCION | Espacios internos dobles o más | 2,163 |
| SUPERVISOR | Espacios internos dobles o más | 370 |
| DIRECTOR | Espacios internos dobles o más | 9,507 |
| DIRECTOR | Placeholders de guiones de largo variable (`"----"`, etc.) | ~2,057 |
| TELEFONO | Multivalor en una celda (`,`/`;`/`/`/`Y`) | hasta 268 |
| TELEFONO | Longitud dominante 8 dígitos; resto con guiones/otros formatos | 66,091 de 8 dígitos vs. el resto |
| DISTRITO | Dos esquemas válidos (`AA-BB-CCCC`, `AA-BBB`) + 79 incompletos | 28,849 + 79 |

**6 variables con formato inconsistente en el crudo: ESTABLECIMIENTO, DIRECCION, SUPERVISOR, DIRECTOR, TELEFONO, DISTRITO.**

### 2.8 Síntesis de problemas de calidad

1. Faltantes altos en `DIRECTOR` (~29%) y `TELEFONO` (~29%) — dato incompleto en origen, no error de scraping.
2. Faltantes disfrazados en varias columnas que `isnull()` no detecta.
3. `DISTRITO` y `SUPERVISOR` co-ausentes en las mismas filas — patrón estructural (estables sin distrito/supervisor asignado).
4. `DISTRITO` con formatos heterogéneos, no validable con un solo regex.
5. `CIUDAD CAPITAL` vs `GUATEMALA`: misma geografía administrativa partida en el dropdown de scraping.
6. Tildes inconsistentes entre `DEPARTAMENTO` (sin tildes) y `DEPARTAMENTAL` (con tildes).
7. Espacios dobles en 4 variables de texto libre.
8. `TELEFONO` multivalor en una misma celda.
9. Niveles `UNIVERSIDAD`/`ADMINISTRATIVOS` fuera del alcance pedagógico del proyecto.
10. Sin duplicados de fila ni de `CODIGO`.
11. Sin basura HTML en ninguna celda — el parseo del scraper quedó limpio.
12. Mismo nombre+dirección con varios códigos (9,530 pares) — esperado por niveles/jornadas/planes distintos.

---

## 3. Plan de limpieza

Para cada variable se documentó, **antes** de tocar el código: problema(s) encontrado(s), regla de corrección y por qué debería funcionar, y riesgos de la transformación. Tabla completa (17/17 variables) en `CheckPoint.md`, Parte 2. Resumen de las decisiones más delicadas:

| Variable | Problema | Regla | Riesgo aceptado |
|---|---|---|---|
| DEPARTAMENTO | `CIUDAD CAPITAL` separado de `GUATEMALA` en el dropdown, mismo departamento real | Fusionar `CIUDAD CAPITAL` → `GUATEMALA` | Se pierde la distinción "capital vs. resto de Guatemala" a nivel de esta columna — mitigado porque `MUNICIPIO` (`ZONA 1`…`ZONA 25`) y `DEPARTAMENTAL` (`GUATEMALA NORTE/SUR/ORIENTE/OCCIDENTE`) preservan esa granularidad |
| NIVEL | Incluye `UNIVERSIDAD`(1) y `ADMINISTRATIVOS`(2), fuera del alcance "hasta diversificado" | Eliminar esas 3 filas | Pérdida de 3 registros (<0.01%) — debe quedar explícito que el dataset limpio no cubre esos niveles |
| TELEFONO | Multivalor en una celda, formatos mixtos | Tomar el primer candidato de exactamente 8 dígitos; si ninguno califica, `NaN` | Se descartan teléfonos adicionales de la misma celda — pérdida de información aceptada a cambio de una columna comparable |
| DIRECTOR / DIRECCION / ESTABLECIMIENTO / SUPERVISOR | Nulos disfrazados (guiones, `S/D`, `SIN DATO`, etc.), espacios dobles | Normalizar a `NaN` los tokens de "sin dato"; colapsar espacios múltiples. **No se corrige ortografía ni contenido lingüístico real** | Ninguno relevante — son artefactos de formato, no contenido |
| DISTRITO | Dos esquemas válidos + 79 incompletos | Validar contra ambos regex; incompletos → `NaN` | Se pierden 79 valores parciales sin intentar reconstruirlos — aceptable (<0.1%), debe quedar explícito que no se intentó imputar |

**Regla general del proyecto:** no se corrige la ortografía de nombres de establecimientos ni direcciones — el texto debe quedar tal como está, solo se normaliza formato (espacios, mayúsculas, encoding).

**Revisado y confirmado con el equipo (2026-07-21):** las 3 decisiones más delicadas (fusión de `CIUDAD CAPITAL`, filtro de `NIVEL`, regla de teléfono) fueron implementadas directamente en código por un integrante del equipo; se revisaron y el equipo las dio por definitivas.

---

## 4. Limpieza aplicada

Implementada en `DPL/limpieza.py`, dividida en dos bloques de trabajo (estructura geográfica/identificación, y catálogos/contacto). Corre con `python limpieza.py` desde `DPL/` (venv `Proyecto1`).

### 4.1 Registro de transformaciones

| Variable | Problema detectado | Transformación | Registros afectados | Justificación |
|---|---|---|---|---|
| CODIGO | Ninguno (0 fuera de formato) | Validación de formato `##-##-####-##` (defensiva, sin corrección) | 0 | Confirma que el crudo ya cumplía el estándar |
| DEPARTAMENTO | `CIUDAD CAPITAL` separado de `GUATEMALA` | `strip().upper()` + unificación `CIUDAD CAPITAL`→`GUATEMALA` | 7,594 | `DEPARTAMENTAL` ya repartía ambas etiquetas en las mismas 4 direcciones — confirma que MINEDUC las trata como la misma unidad geográfica |
| DEPARTAMENTAL | Ninguno (tildes correctas) | `strip().upper()`, se preservan tildes oficiales | 0 | Es la única variable con tildes correctas del catálogo; quitarlas perdería información |
| MUNICIPIO | Ninguno grave | `strip().upper()` + colapsar espacios múltiples | 0 | Normalización preventiva |
| DISTRITO | 79 incompletos, formatos mixtos | Nulos disfrazados → `NaN`; incompletos (no matchean los 2 regex válidos) → `NaN` | 79 | Un distrito truncado no es recuperable sin la fuente original |
| SUPERVISOR | Nulos disfrazados | `strip().upper()` + colapsar espacios; nulos disfrazados → `NaN` (**antes** de mayúsculas, ver §4.3) | 370 espacios dobles corregidos | Mismo patrón estructural que `DISTRITO` |
| ESTABLECIMIENTO | 4,676 espacios dobles | `strip().upper()` + colapsar espacios (nulos disfrazados → `NaN` antes de mayúsculas) | 4,676 | Artefacto de captura, no parte del nombre real |
| DIRECCION | 887 nulos disfrazados (24 + 863 originales, + guiones largos), 2,163 espacios dobles | Nulos disfrazados (incl. `"-"`, `"--"`, `"---"`) → `NaN` antes de mayúsculas; colapsar espacios | 24 disfrazados + 2,163 espacios dobles | Artefactos de formato; no se expanden abreviaturas ni se corrige ortografía |
| DIRECTOR | 29,796 faltantes (reales+disfrazados), 9,507 espacios dobles | Placeholders (guiones de largo variable, `"SIN DATO(S)"`, `"NO APLICA"`, encoding roto) → `NaN` antes de mayúsculas; colapsar espacios | 2,321 celdas de texto convertidas a `NaN` + 9,507 espacios dobles | Guiones/tokens son evidentemente "sin dato" del sistema fuente, no nombres reales |
| TELEFONO | Multivalor, formatos mixtos | `S/D`/vacío → `NaN`; de celdas con separadores, primer candidato de 8 dígitos; si ninguno, `NaN` | 853 celdas sin candidato válido → `NaN` | 8 dígitos es el formato dominante y válido para Guatemala |
| NIVEL, SECTOR, AREA, STATUS, MODALIDAD, JORNADA, PLAN | `NIVEL` fuera de alcance (3 filas); `AREA`="SIN ESPECIFICAR" (8) | `strip().upper()`; eliminar filas de `NIVEL` fuera de alcance; `AREA`="SIN ESPECIFICAR"→`NaN` | 3 filas eliminadas + 8 celdas de `AREA` → `NaN` | El enunciado pide datos "hasta diversificado"; "SIN ESPECIFICAR" es un faltante disfrazado |

### 4.2 Duplicados

**Exactos:** 0 duplicados de fila y 0 por `CODIGO` (confirmado también sobre el conjunto limpio).

**Parciales (similitud de cadenas):** implementado en `DPL/duplicados_parciales.py` con RapidFuzz (`token_sort_ratio`), bloqueo por (`DEPARTAMENTO`,`MUNICIPIO`) para acotar comparaciones, excluyendo los 9,530 pares ya contados como exactos. Con umbral final nombre >= 95 y dirección >= 90 (calibrado revisando muestras): **15,751 pares, agrupados en 4,018 grupos** (13,738 registros):

- **3,362 grupos** con nombre propio — candidatos de mayor confianza; el patrón dominante es el mismo plantel con varios niveles y una diferencia mínima de puntuación en la dirección (ej. `"3A AVENIDA"` vs `"3A. AVENIDA"`).
- **656 grupos** con nombre genérico tipo sigla (`EORM`, `EODP`, etc.) — marcados aparte porque cientos de escuelas rurales distintas comparten ese nombre oficial abreviado; no implican que sean el mismo plantel.

**Ningún registro fue eliminado ni fusionado automáticamente** — el reporte completo (`data/posibles_duplicados_parciales_grupos.csv`) queda para revisión manual, según pide el enunciado.

### 4.3 Bug encontrado y corregido durante la limpieza

Al escribir las pruebas de validación (§5) se detectó que en `limpiar_supervisor`, `limpiar_direccion` y `limpiar_establecimiento` el `.str.upper()` se aplicaba **antes** de comparar contra los tokens de nulo (en minúscula); como `str(NaN).upper() == "NAN"`, la comparación nunca coincidía y esas tres columnas guardaban el texto literal `"NAN"` en vez de un valor faltante real — **10,701 casos en SUPERVISOR, 863 en DIRECCION, 15 en ESTABLECIMIENTO**. Se corrigió el orden (mapear nulos antes de pasar a mayúsculas) y se regeneró `dataset_limpio.csv`. De paso se completaron los tokens de nulo disfrazado que faltaban en `DIRECCION` (guiones largos) y `DIRECTOR` (`"SIN DATO(S)"`, `"NO APLICA"`).

---

## 5. Pruebas de validación del conjunto limpio

Implementadas en `DPL/validacion.py` (`python validacion.py`). Cada prueba imprime PASA/FALLA y termina con exit code 1 si alguna prueba dura falla.

| Prueba | Resultado |
|---|---|
| Sin registros duplicados exactos | PASA |
| Sin duplicados por CODIGO | PASA |
| Sin espacios al inicio/final en texto | PASA |
| TELEFONO en formato consistente (8 dígitos o NaN) | PASA |
| CODIGO cumple `##-##-####-##` | PASA |
| DISTRITO cumple uno de los 2 formatos válidos, o NaN | PASA |
| DEPARTAMENTO pertenece al catálogo de 22 departamentos | PASA |
| NIVEL sin categorías fuera de alcance | PASA |
| AREA sin "SIN ESPECIFICAR" | PASA |
| Sin categorías duplicadas por diferencias de escritura | PASA |
| Sin nulos disfrazados conocidos | PASA |
| *(advertencia, no cuenta para el resultado)* TELEFONO no se corrompe sin `dtype=str` | ADVERTENCIA conocida (ver §6.1) |

**Resultado: 11/11 pruebas pasan.** Esta suite fue la que encontró el bug descrito en §4.3.

---

## 6. Informe de calidad: antes vs. después

| Métrica | Antes (crudo) | Después (limpio) |
|---|---|---|
| Registros | 94,533 | 94,530 (−3 por filtro de `NIVEL` fuera de alcance, ver §4.1) |
| Variables | 17 | 17 (sin variables derivadas creadas ni columnas eliminadas) |
| Valores faltantes (celdas, reales + disfrazados) | 79,739 (4.96%) | 80,806 (5.03%, todos NaN reales — el leve aumento refleja nulos disfrazados que antes no eran detectables y ahora quedan explícitos, no nueva pérdida de datos) |
| Variables con al menos un NA | 6 de 17 | 7 de 17 (`AREA` gana NaN por el mapeo deliberado de `"SIN ESPECIFICAR"`) |
| Duplicados exactos | 0 | 0 |
| Posibles duplicados | 9,530 pares (mismo nombre+dirección exactos; sin análisis de similitud de cadenas) | 9,530 pares exactos + 4,018 grupos adicionales por similitud (13,738 registros) — ninguno eliminado/fusionado, todos documentados para revisión manual |
| Variables con formato inconsistente | 6 (`ESTABLECIMIENTO`, `DIRECCION`, `SUPERVISOR`, `DIRECTOR`, `TELEFONO`, `DISTRITO`) | 0 (validado por la suite de pruebas, §5) |
| Variables con tipo de dato incorrecto | 0 (pandas ya inferí­a correctamente `str` en las 17 columnas) | 0 — con la advertencia documentada de que `TELEFONO` se corrompe a `float64` si el CSV se recarga sin `dtype=str` (§6.1) |
| Categorías inconsistentes | 1 (`DEPARTAMENTO`: `CIUDAD CAPITAL` y `GUATEMALA` representaban la misma entidad geográfica) | 0 |
| Errores corregidos | — | **27,598** en total: 3 registros eliminados (`NIVEL` fuera de alcance) + 3,285 nulos disfrazados normalizados (79 `DISTRITO` + 24 `DIRECCION` + 2,321 `DIRECTOR` + 853 `TELEFONO` + 8 `AREA`) + 16,716 espacios dobles colapsados (4,676 `ESTABLECIMIENTO` + 2,163 `DIRECCION` + 370 `SUPERVISOR` + 9,507 `DIRECTOR`) + 7,594 unificaciones de categoría (`CIUDAD CAPITAL`→`GUATEMALA`) |

### 6.1 Limitación conocida y aceptada: `TELEFONO` y `dtype`

Tras la limpieza, `TELEFONO` quedó compuesta únicamente por dígitos (sin guiones). Si el CSV se recarga con `pd.read_csv` **sin** fijar `dtype`, pandas infiere la columna como `float64` y corrompe el valor (`22324443` → `22324443.0`). Se confirmó que ni siquiera `quoting=csv.QUOTE_NONNUMERIC` al guardar evita esto — pandas infiere el tipo por contenido al leer, sin importar las comillas. **Cargar siempre con `dtype=str`** (documentado también en el libro de códigos §2). No se cuenta como defecto de los datos, es una instrucción de uso obligatoria.

---

## 7. Generación del conjunto de datos limpio

`data/dataset_limpio.csv` — un solo archivo con la información de los 22 departamentos, 94,530 registros × 17 variables, estructura consistente, tipos de datos correctos, nombres de variable descriptivos, formato uniforme, y sin los errores detectados durante la validación (§5).

**Cargar siempre así:**

```python
import pandas as pd
df = pd.read_csv("data/dataset_limpio.csv", encoding="utf-8-sig", dtype=str)
```

---

## 8. Libro de códigos

Documento completo en `DPL/libro_codigos.md` (y su versión en PDF, `DPL/libro_codigos.pdf`), con descripción, tipo de dato, dominio, valores posibles y tratamiento aplicado para cada una de las 17 variables, más notas y limitaciones conocidas.

---

## 9. Reproducibilidad

Todo el proceso es reproducible desde cero:

1. `scraping/03_scrape_all.py` → genera `data/crudo/*.csv`.
2. Unión de los 23 CSV → `data/dataset.csv` (ver `DPL/diagnostico.ipynb`).
3. `python DPL/limpieza.py` → genera `data/dataset_limpio.csv`.
4. `python DPL/duplicados_parciales.py` → genera `data/posibles_duplicados_parciales_grupos.csv`.
5. `python DPL/validacion.py` → corre las 11 pruebas de calidad.

Entorno: venv `Proyecto1/` (pandas, rapidfuzz, playwright).
