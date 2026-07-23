---
title: "Libro de Códigos — Establecimientos Educativos de Guatemala (MINEDUC)"
subtitle: "Proyecto 1 — CC3066 Data Science, Universidad del Valle de Guatemala"
date: "23 de julio de 2026"
geometry: margin=2.5cm
fontsize: 11pt
---

# 1. Descripción general del dataset

**Fuente:** Sistema de consulta pública de establecimientos educativos del Ministerio de Educación de Guatemala (MINEDUC), `http://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/`.

**Método de obtención:** web scraping con Playwright (Chromium). El sitio es un formulario ASP.NET WebForms clásico protegido por Incapsula, que bloquea peticiones `POST` hechas sin un navegador real; por eso no se usó `requests`. Se automatizó una búsqueda por cada uno de los 23 valores del dropdown de Departamento (los 22 departamentos oficiales de Guatemala, más `CIUDAD CAPITAL` como entrada administrativa separada en el propio formulario), con el resto de filtros (Municipio, Nivel, Sector, Plan, Modalidad) en `TODOS`.

**Cobertura:** todos los niveles educativos disponibles en el sistema (parvulario, preprimaria, primaria, básico, diversificado), sin restringir por nivel, para no perder registros por una interpretación restrictiva del alcance "hasta diversificado".

**Tamaño:**

| Etapa | Registros | Variables |
|---|---|---|
| Crudo (23 CSV unidos, sin limpiar) | 94,533 | 17 |
| Limpio (`data/dataset_limpio.csv`) | 94,530 | 17 |

La diferencia de 3 registros corresponde a establecimientos de nivel `UNIVERSIDAD` (1) y `ADMINISTRATIVOS` (2), fuera del alcance pedagógico del proyecto (ver variable `NIVEL` más abajo).

**Llave primaria:** `CODIGO` — identificador único de establecimiento, sin duplicados en las 94,530 filas.

**Unidad de observación:** una fila representa una combinación de establecimiento + nivel + jornada + plan (un mismo plantel físico puede aparecer en varias filas con distinto `CODIGO` si ofrece varios niveles, jornadas o planes).

**Fecha de extracción:** 21 de julio de 2026 (scraping ejecutado sobre el sistema de consulta pública de MINEDUC).

**Versión del conjunto limpio:** v1.1 — `data/dataset_limpio.csv` regenerado el 23 de julio de 2026 tras corregir un bug de `limpieza.py` que dejaba el texto literal `"NAN"` en vez de un valor faltante real en `SUPERVISOR`, `DIRECCION` y `ESTABLECIMIENTO` (ver §3, notas de cada variable, y `CheckPoint.md`). La v1.0 (21 de julio) tenía ese defecto; no debe usarse.

**Variables derivadas:** ninguna — el dataset limpio conserva las mismas 17 variables del crudo, sin columnas calculadas.

---

# 2. Cómo cargar el dataset

```python
import pandas as pd

df = pd.read_csv("data/dataset_limpio.csv", encoding="utf-8-sig", dtype=str)
```

**Importante:** cargar siempre con `dtype=str` (o al menos `dtype={"CODIGO": str, "DISTRITO": str, "TELEFONO": str}`). Tras la limpieza, `TELEFONO` quedó compuesta únicamente por dígitos (sin guiones); si se lee sin fijar el tipo, pandas infiere `float64` y corrompe los valores (`22324443` → `22324443.0`). `CODIGO` y `DISTRITO` no tienen este riesgo porque conservan guiones, pero se recomienda forzar `str` en las tres por consistencia.

---

# 3. Diccionario de variables

Para cada variable: significado, tipo, regla de limpieza aplicada (si hubo) y dominio observado en el dataset limpio. El detalle completo del diagnóstico y la justificación de cada regla está en `CheckPoint.md`.

## CODIGO

- **Significado:** identificador único de establecimiento asignado por MINEDUC.
- **Tipo:** texto, formato fijo `##-##-####-##` (departamento-municipio-secuencial-nivel/jornada, según codificación interna de MINEDUC).
- **Faltantes:** 0.
- **Valores únicos:** 94,530 (uno por fila — llave primaria).
- **Limpieza aplicada:** `strip()` + validación de formato contra el patrón `##-##-####-##`. No requirió corrección; 0 códigos fuera de formato en el crudo.

## DISTRITO

- **Significado:** código del distrito escolar administrativo al que pertenece el establecimiento.
- **Tipo:** texto, dos formatos válidos observados: `##-##-####` y `##-###`.
- **Faltantes:** 10,772 (11.40%). Coincide casi exactamente con los faltantes de `SUPERVISOR` (patrón estructural: establecimientos sin distrito asignado tampoco tienen supervisor asignado).
- **Valores únicos:** 2,270.
- **Limpieza aplicada:** nulos disfrazados (`"S/D"`, vacío, `"None"`) → `NaN`. Valores que no calzan con ninguno de los dos formatos válidos (79 casos, ej. `"01-"`, `"17-"`, códigos truncados) se convirtieron a `NaN` en vez de intentar reconstruirlos.

## DEPARTAMENTO

- **Significado:** departamento del establecimiento, según la dirección departamental de MINEDUC a la que reporta.
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 22 — los 22 departamentos oficiales de Guatemala.
- **Limpieza aplicada:** `strip().upper()` + fusión de `CIUDAD CAPITAL` en `GUATEMALA` (el formulario de MINEDUC las trata como entradas separadas del dropdown, pero geográficamente Ciudad Capital es parte del departamento de Guatemala). La granularidad que se pierde con esta fusión se conserva en `MUNICIPIO` (valores `ZONA 1`…`ZONA 25`, exclusivos de la antigua Ciudad Capital) y en `DEPARTAMENTAL` (`GUATEMALA NORTE/SUR/ORIENTE/OCCIDENTE`). Decisión revisada y confirmada con el equipo.
- **Valores:** `ALTA VERAPAZ`, `BAJA VERAPAZ`, `CHIMALTENANGO`, `CHIQUIMULA`, `EL PROGRESO`, `ESCUINTLA`, `GUATEMALA`, `HUEHUETENANGO`, `IZABAL`, `JALAPA`, `JUTIAPA`, `PETEN`, `QUETZALTENANGO`, `QUICHE`, `RETALHULEU`, `SACATEPEQUEZ`, `SAN MARCOS`, `SANTA ROSA`, `SOLOLA`, `SUCHITEPEQUEZ`, `TOTONICAPAN`, `ZACAPA`.

## MUNICIPIO

- **Significado:** municipio del establecimiento. Bajo `GUATEMALA` (antigua Ciudad Capital), en vez de municipio usa zonas de la ciudad capital.
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 357 (incluye municipios de los 22 departamentos + `ZONA 1`…`ZONA 25`).
- **Limpieza aplicada:** `strip().upper()` + colapsar espacios internos múltiples a uno solo.

## ESTABLECIMIENTO

- **Significado:** nombre oficial del centro educativo.
- **Tipo:** texto libre.
- **Faltantes:** 15 (0.02%).
- **Valores únicos:** 21,553.
- **Limpieza aplicada:** nulos disfrazados (`"S/D"`, vacío) → `NaN`, **antes** de pasar a mayúsculas; luego `strip().upper()` + colapsar espacios internos dobles (4,676 registros afectados en el crudo). **No se corrigió ortografía ni contenido lingüístico del nombre** — regla explícita del proyecto, porque el nombre real de la institución lo va a usar alguien más en informes.

## DIRECCION

- **Significado:** dirección física del establecimiento.
- **Tipo:** texto libre.
- **Faltantes:** 887 (0.94%).
- **Valores únicos:** 43,872.
- **Limpieza aplicada:** nulos disfrazados (`"S/D"`, `"."`, vacío, y guiones de largo variable `"-"`/`"--"`/`"---"`) → `NaN`, **antes** de pasar a mayúsculas; luego `strip().upper()` + colapsar espacios dobles (2,163 registros en el crudo). No se expandieron abreviaturas (`"AV."` se deja como está) ni se corrigió ortografía.

## TELEFONO

- **Significado:** número de teléfono de contacto del establecimiento.
- **Tipo:** texto, 8 dígitos (formato estándar de telefonía fija/móvil en Guatemala) o `NaN`.
- **Faltantes:** 28,364 (30.01%).
- **Valores únicos:** 36,170.
- **Limpieza aplicada:** nulos disfrazados (`"S/D"`, vacío) → `NaN`. Para celdas con varios teléfonos separados por `,`/`;`/`/`/`Y` (hasta 268 casos en el crudo), se extrae el **primer candidato que tenga exactamente 8 dígitos** tras remover guiones y espacios; si ninguno califica, `NaN`. Se descartan los teléfonos adicionales de la misma celda — se prioriza tener una columna limpia y comparable sobre conservar todos los números.
- **Advertencia:** ver sección 2 sobre el riesgo de `dtype` al cargar esta columna.

## SUPERVISOR

- **Significado:** nombre del supervisor educativo del distrito al que pertenece el establecimiento.
- **Tipo:** texto libre.
- **Faltantes:** 10,701 (11.32%). Co-ausente con `DISTRITO` casi 1:1 (patrón estructural: sin distrito asignado, tampoco hay supervisor).
- **Valores únicos:** 1,631.
- **Limpieza aplicada:** nulos disfrazados (`"S/D"`, vacío) → `NaN`, **antes** de pasar a mayúsculas; luego `strip().upper()` + colapsar espacios dobles (370 registros en el crudo).

## DIRECTOR

- **Significado:** nombre del director del establecimiento.
- **Tipo:** texto libre.
- **Faltantes:** 30,059 (31.80%) — el porcentaje más alto de faltantes del dataset.
- **Valores únicos:** 35,804.
- **Limpieza aplicada:** placeholders de "sin dato" (cadenas hechas solo de guiones/puntos/comas/ceros/espacios de largo variable, caracteres de encoding roto `�`, y tokens `"SIN DATO"`/`"SIN DATOS"`/`"NO APLICA"`) → `NaN`, **antes** de pasar a mayúsculas. Valores reales: `strip().upper()` + colapsar espacios (9,507 registros con espacios dobles en el crudo). El faltante alto es fiel al dato de origen (MINEDUC no reporta director en ~3 de cada 10 establecimientos), no un artefacto de la limpieza.

## NIVEL

- **Significado:** nivel educativo que ofrece el establecimiento en esa fila.
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 8.
- **Limpieza aplicada:** `strip().upper()` + **se eliminaron 3 registros** con `NIVEL` en `{UNIVERSIDAD, ADMINISTRATIVOS}` (1 y 2 registros respectivamente), fuera del alcance "hasta diversificado" del proyecto. Aparecían en el crudo porque el scraping consultó Nivel=`TODOS`.
- **Valores:** `INICIAL`, `PARVULOS`, `PARVULOS Y PREP. BILINGUE`, `PREPRIMARIA BILINGUE`, `PRIMARIA`, `PRIMARIA DE ADULTOS`, `BASICO`, `DIVERSIFICADO`.

## SECTOR

- **Significado:** sector administrativo/financiero del establecimiento.
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 4.
- **Limpieza aplicada:** `strip().upper()`. Sin variantes de escritura en el crudo.
- **Valores:** `OFICIAL`, `PRIVADO`, `MUNICIPAL`, `COOPERATIVA`.

## AREA

- **Significado:** área geográfica (urbana o rural) donde se ubica el establecimiento.
- **Tipo:** texto categórico.
- **Faltantes:** 8 (0.01%).
- **Valores únicos:** 2.
- **Limpieza aplicada:** `strip().upper()` + el valor `"SIN ESPECIFICAR"` (8 registros en el crudo) se tradujo a `NaN`, por ser semánticamente un faltante disfrazado, no una tercera categoría real.
- **Valores:** `URBANA`, `RURAL`.

## STATUS

- **Significado:** estado operativo del establecimiento.
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 6.
- **Limpieza aplicada:** `strip().upper()`. Sin variantes de escritura en el crudo.
- **Valores:** `ABIERTA`, `CERRADA DEFINITIVAMENTE`, `CERRADA TEMPORALMENTE`, `TEMPORAL CONTRATO 021`, `TEMPORAL NOMBRAMIENTO`, `TEMPORAL TITULOS`.

## MODALIDAD

- **Significado:** modalidad lingüística de la enseñanza.
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 2.
- **Limpieza aplicada:** `strip().upper()`. Sin variantes de escritura en el crudo.
- **Valores:** `BILINGUE`, `MONOLINGUE`.

## JORNADA

- **Significado:** horario en el que opera el establecimiento.
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 6.
- **Limpieza aplicada:** `strip().upper()`. Sin variantes de escritura en el crudo.
- **Valores:** `MATUTINA`, `VESPERTINA`, `NOCTURNA`, `INTERMEDIA`, `DOBLE`, `SIN JORNADA`.

## PLAN

- **Significado:** plan de estudios (presencialidad/frecuencia) del establecimiento.
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 13.
- **Limpieza aplicada:** `strip().upper()`. Sin variantes de escritura en el crudo; incluye subtipos de `SEMIPRESENCIAL` como categorías propias (no se colapsaron entre sí, porque representan modalidades distintas, no errores de captura).
- **Valores:** `DIARIO(REGULAR)`, `A DISTANCIA`, `DOMINICAL`, `FIN DE SEMANA`, `INTERCALADO`, `IRREGULAR`, `MIXTO`, `SABATINO`, `SEMIPRESENCIAL`, `SEMIPRESENCIAL (DOS DÍAS A LA SEMANA)`, `SEMIPRESENCIAL (FIN DE SEMANA)`, `SEMIPRESENCIAL (UN DÍA A LA SEMANA)`, `VIRTUAL A DISTANCIA`.

## DEPARTAMENTAL

- **Significado:** dirección departamental de educación de MINEDUC a la que reporta el establecimiento (unidad administrativa, no siempre 1:1 con `DEPARTAMENTO`).
- **Tipo:** texto categórico.
- **Faltantes:** 0.
- **Valores únicos:** 26 (más que los 22 departamentos porque `GUATEMALA` se reparte en 4 direcciones — `NORTE`, `SUR`, `ORIENTE`, `OCCIDENTE` — y `QUICHE` en 2 — `QUICHÉ` y `QUICHÉ NORTE`).
- **Limpieza aplicada:** `strip().upper()`, **conservando las tildes oficiales** (`QUICHÉ`, `PETÉN`, `SACATEPÉQUEZ`, `SOLOLÁ`, `SUCHITEPÉQUEZ`, `TOTONICAPÁN`). A diferencia de `DEPARTAMENTO`, esta es la única variable de geografía administrativa que sí lleva tildes correctas — **no comparar por igualdad de string contra `DEPARTAMENTO` sin normalizar tildes antes**.
- **Valores:** `ALTA VERAPAZ`, `BAJA VERAPAZ`, `CHIMALTENANGO`, `CHIQUIMULA`, `EL PROGRESO`, `ESCUINTLA`, `GUATEMALA NORTE`, `GUATEMALA OCCIDENTE`, `GUATEMALA ORIENTE`, `GUATEMALA SUR`, `HUEHUETENANGO`, `IZABAL`, `JALAPA`, `JUTIAPA`, `PETÉN`, `QUETZALTENANGO`, `QUICHÉ`, `QUICHÉ NORTE`, `RETALHULEU`, `SACATEPÉQUEZ`, `SAN MARCOS`, `SANTA ROSA`, `SOLOLÁ`, `SUCHITEPÉQUEZ`, `TOTONICAPÁN`, `ZACAPA`.

---

# 4. Notas y limitaciones conocidas

1. **`ESTABLECIMIENTO`/`DIRECCION` con el mismo par de valores pero distinto `CODIGO`** (9,530 pares en el crudo): no es un error de duplicación — un mismo plantel físico puede tener varios códigos por nivel, jornada o plan distintos. No se colapsaron estas filas.
2. **Abreviaturas inconsistentes en `DIRECCION`** (ej. `"AV."` vs `"AVENIDA"`): no se normalizaron, porque hacerlo requeriría inferir la forma "correcta" sin certeza, alterando el contenido original.
3. **`TELEFONO` multi-valor**: cuando una celda traía varios números, solo se conservó uno (el primero de 8 dígitos). Si un análisis futuro necesita todos los teléfonos de un establecimiento, hay que volver al CSV crudo (`data/dataset.csv`), no al limpio.
4. **Filtrado de `NIVEL`**: el dataset limpio ya no incluye los 3 registros de `UNIVERSIDAD`/`ADMINISTRATIVOS` presentes en el crudo. Si se necesitara cobertura universitaria, hay que partir del crudo.
5. **Duplicados parciales (similitud de cadenas)**: además de los 9,530 pares de nombre+dirección exactos (punto 1), se corrió una búsqueda por similitud de cadenas (RapidFuzz, `DPL/duplicados_parciales.py`) que encontró **4,018 grupos adicionales** de posibles duplicados (13,738 registros): 3,362 con nombre propio (alta confianza) y 656 con nombre genérico tipo sigla (`EORM`, `EODP`, etc. — probablemente escuelas distintas que comparten nombre oficial abreviado, no duplicados reales). Reporte completo en `data/posibles_duplicados_parciales_grupos.csv`. **Ningún registro fue eliminado ni fusionado automáticamente.**
6. **Pruebas de validación automáticas** (`DPL/validacion.py`, 11/11 pasan) verifican que el conjunto limpio cumple las reglas de calidad de esta sección (formatos, catálogos, ausencia de nulos disfrazados, etc.). Fueron las que encontraron el bug corregido en la v1.1 (ver §1, "Versión del conjunto limpio").
7. **Trazabilidad completa**: el diagnóstico (código + salidas) está en `DPL/diagnostico.ipynb`; el plan de limpieza (regla, por qué y riesgos por variable), en `CheckPoint.md`. El reporte consolidado con diagnóstico, plan, limpieza, duplicados, validación e informe de calidad antes/después está en `Informe_Final_Proyecto1.md`. El código de limpieza ejecutable está en `DPL/limpieza.py`.
