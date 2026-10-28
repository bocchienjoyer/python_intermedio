# Obras que esperan

**Autor:** Jose Pablo Navarro Nateros (@bocchienjoyer).

**Pregunta:** ¿Qué caracteriza a las obras públicas paralizadas en el Perú y qué patrones presentan aquellas con mayor avance físico?

Se analiza el inventario de Contraloría con corte al **30 de junio de 2026**: 2.262 obras. El análisis describe su ubicación, tipo, avance y causas reportadas, con atención a las obras que superan el 90 % de avance físico. La paralización posterga la entrega o mejora de infraestructura. El registro no permite medir por sí solo la disponibilidad efectiva de servicios ni los daños sufridos por la población.

**[Explorar el dashboard público](https://obras-que-esperan-peru.fancyperch2.chatgpt.site)**

## Resultados

- **281 obras (12,4 %) superan el 90 % de avance físico y figuran paralizadas.** El umbral es estrictamente mayor que 90 % y hasta 100 %, conforme al rango utilizado en el anexo. Tres obras con exactamente 90 % pertenecen al rango anterior.
- **169 de esas 281 obras (60,1 %) no tienen asignación positiva de PIM 2026 en el registro.** Esta es una condición presupuestaria a la fecha de corte: no demuestra la causa de paralización ni descarta otras fuentes o asignaciones posteriores.
- **136 de las 281 obras de mayor avance (48,4 %) corresponden a vivienda, construcción y saneamiento o a transportes y comunicaciones.** Son 79 y 57 obras, respectivamente. Las categorías incluyen distintos tipos de infraestructura; no representan exclusivamente sistemas de agua ni carreteras.

De las 281 obras, 23 reportan 100 % de avance. Se conservan porque forman parte del inventario oficial. Al excluirlas, quedan 258 obras con avance mayor que 90 % y menor que 100 %, de las cuales 154 (59,7 %) no registran PIM positivo. El patrón presupuestario persiste en esta comprobación.

## Fuentes y metodología

La fuente principal es el [informe de Contraloría y sus anexos](https://www.gob.pe/institucion/contraloria/informes-publicaciones/8489152-informe-de-obras-paralizadas-en-el-territorio-nacional-a-junio-de-2026), publicado el 17 de agosto de 2026. Los originales descargados y sus enlaces, fechas de recuperación y hashes SHA-256 se conservan en `datos/originales/`. El Anexo 1 contiene los registros analizados; el Anexo 2 documenta servicios de control y no se incorpora a los cálculos de obras.

La unidad de análisis es **una obra identificada por código INFOBRAS**. Se normalizan espacios y se convierten valores numéricos sin inventar datos. «No declarado» y CUI igual a cero se tratan como ausencias. Los ceros monetarios se conservan como valores reportados. Se validan identificadores únicos, límites del avance, correspondencia del rango superior y coherencia entre PIM y su indicador de disponibilidad.

Las frecuencias y porcentajes utilizan denominadores explícitos. El PIM es una asignación presupuestaria modificada, no gasto ejecutado. Los costos de obra de INFOBRAS y los costos de inversión de Invierte.pe miden conceptos diferentes: su cociente **no es un sobrecosto**. Una inversión CUI puede agrupar varias obras, por lo que no se suman costos de inversión ni PIM repetidos para producir indicadores monetarios.

La interpretación se apoya en capacidad estatal, continuidad de la inversión y rendición de cuentas. El [Banco Mundial (2025, capítulo 4)](https://documents1.worldbank.org/curated/en/099030325150510528/pdf/P177645-b964994f-03e4-4ce8-aa59-7642a26b538e.pdf) discute problemas de preparación y continuidad presupuestaria. [Bancalari (2024)](https://ifs.org.uk/publications/unintended-consequences-infrastructure-development) muestra costos sanitarios y de seguridad durante la implementación de alcantarillado en Perú entre 2005 y 2015. Esa evidencia motiva la relevancia social del tema; los efectos de aquel estudio no se atribuyen a las obras del inventario de 2026.

## Limitaciones

- Se observa un inventario a una fecha determinada. La situación de una obra puede haber cambiado después. Los años de inicio no indican cuántos años estuvo paralizada.
- Hay 54 obras sin avance declarado y 23 con 100 % reportado. Un avance alto no demuestra operatividad ni facilidad para culminar la obra.
- Las causas proceden de lo declarado por las entidades. No son una auditoría causal independiente ni una prueba de corrupción.
- Las comparaciones describen obras paralizadas. No estiman el riesgo de paralización de todas las obras de un territorio o entidad.
- No se dispone de una medición uniforme de personas afectadas, tráfico, interrupciones de servicios o rentabilidad social. Tampoco de costos iniciales y finales comparables para calcular sobrecostos.

## Reproducción

Requiere Python 3.11 o posterior. Desde la raíz del repositorio:

```console
python -m pip install -r tarea_3/requirements.txt
python tarea_3/scripts/obtener_datos.py
python tarea_3/scripts/procesar_datos.py
python tarea_3/scripts/analizar_datos.py
python tarea_3/scripts/preparar_web.py
python -m http.server 8000 --directory tarea_3/web
```

Abrir `http://localhost:8000`. Si ya se dispone de los originales, procesamiento y análisis reproducen las tablas sin conexión. La preparación web descarga la cartografía del MEF únicamente si no está presente. `datos/procesados/calidad.json` registra controles de calidad y `resumen.json` los resultados principales.

El dashboard incluye cuatro indicadores, mapa departamental, gráficos por tipo, avance y causa, cuatro filtros, búsqueda y descarga CSV de la selección. La cartografía procede del servicio del MEF, atribuido al INEI en sus metadatos, y se utiliza con fines referenciales. Las geometrías y su fuente se conservan en `web/data/`.

## Uso de inteligencia artificial

Se utilizó IA para explorar bibliografía, desarrollar el código y apoyar la redacción. Los resultados publicados se calculan a partir de archivos oficiales y se contrastan con el informe y los controles de calidad. Las interpretaciones se limitan a lo que permiten los datos.
