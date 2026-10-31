# Obras que esperan

**Autor:** Jose Pablo Navarro Nateros (@bocchienjoyer).

**Pregunta:** ¿Qué caracteriza a las obras públicas paralizadas en el Perú y qué patrones presentan aquellas con mayor avance físico?

Una obra paralizada retrasa el acceso de la población a nuevos o mejores servicios públicos. Este proyecto explora ubicación, avance físico, presupuesto y causas reportadas de las **2.262 obras** del inventario de Contraloría al **30 de junio de 2026**, con atención a las de mayor avance.

**[Explorar el dashboard público](https://obras-que-esperan-peru.fancyperch2.chatgpt.site) · [Reel de divulgación — 56,9 segundos](reel/reel.mp4)**

<details>
<summary>Dos vistas del dashboard</summary>

![Portada del dashboard Obras que esperan](reel/recursos/dashboard_general.png)

![Mapa de obras paralizadas y distribución por tipo de infraestructura](reel/recursos/dashboard_exploracion.png)

</details>

## Resultados

**281 obras (12,4 %) superan el 90 % de avance físico y figuran paralizadas. De ellas, 155 no registran presupuesto asignado para 2026.** Tres hallazgos amplían ese panorama:

- **23 obras reportan 100 % de avance y siguen clasificadas como paralizadas.** Es una discrepancia que requiere seguimiento; el registro no permite determinar si están operativas ni qué falta para culminar cada caso.
- **58 de las obras de mayor avance se iniciaron en 2015 o antes.** La antigüedad se refiere al inicio reportado, no a años de paralización continua.
- **76 señalan incumplimiento de contrato**, el motivo de paralización más reportado entre las obras de mayor avance. Son declaraciones de las entidades, no una identificación causal independiente.

## Fuentes y metodología

La fuente principal es el [informe de Contraloría y sus anexos](https://www.gob.pe/institucion/contraloria/informes-publicaciones/8489152-informe-de-obras-paralizadas-en-el-territorio-nacional-a-junio-de-2026), publicado el 17 de agosto de 2026. Los originales descargados y sus enlaces, fechas de recuperación y hashes SHA-256 se conservan en `datos/originales/`. El Anexo 1 contiene los registros analizados; el Anexo 2 documenta servicios de control y no se incorpora a los cálculos de obras.

La unidad de análisis es **una obra identificada por código INFOBRAS**. Se normalizan espacios y se convierten valores numéricos sin inventar datos. «No declarado» y CUI igual a cero se tratan como ausencias. Los ceros monetarios se conservan como valores reportados. Se validan identificadores únicos, límites del avance, correspondencia del rango superior y coherencia entre PIM y su indicador de disponibilidad.

El **PIM (Presupuesto Institucional Modificado)** es el presupuesto autorizado para el año y actualizado al corte. No mide gasto ejecutado ni el costo de terminar una obra. La situación presupuestaria y el motivo de paralización son variables distintas.

<details>
<summary>Identificación presupuestaria, umbral de avance y comprobaciones</summary>

Se incluyen avances estrictamente mayores que 90 % y hasta 100 %, conforme al rango del anexo. Tres obras con exactamente 90 % pertenecen al intervalo anterior.

De las 281 obras, 267 tienen código de inversión (CUI): 155 sin asignación registrada (58,1 %) y 112 con asignación. Otras 14 no tienen CUI; no se confunde falta de identificación con presupuesto cero confirmado. La tabla 12 de la fuente agrupa ambos casos bajo NO PIM. Se conserva el cero original y se añade `estado_presupuesto` para distinguirlos. Las 134 obras sin CUI del inventario completo permanecen en la base.

Al excluir las 23 con avance completo, 144 de 248 identificables no registran asignación (58,1 %). El resultado es similar al del grupo completo. En todo el inventario identificable la proporción es 64,8 %: no se presenta el grupo de mayor avance como relativamente peor financiado.

Los costos de obra de INFOBRAS y los costos de inversión de Invierte.pe no son comparables para calcular sobrecostos. Una inversión puede agrupar varias obras; no se suman costos de inversión ni PIM repetidos.

</details>

La interpretación se apoya en la **continuidad de la inversión pública**. La [OCDE (2025)](https://www.oecd.org/en/publications/2025/09/oecd-economic-surveys-peru-2025_d9bfa904/full-report/achieving-strong-growth-and-safeguarding-fiscal-sustainability_000545c6.html) señala que no asegurar financiamiento entre años genera demoras e ineficiencias en el Perú. El [Banco Mundial (2025, capítulo 4, párrafos 185 y 189–192)](https://documents1.worldbank.org/curated/en/099030325150510528/pdf/P177645-b964994f-03e4-4ce8-aa59-7642a26b538e.pdf) identifica dificultades para proteger recursos de proyectos en marcha frente a proyectos nuevos. Si faltan recursos para terminar trabajos indispensables, la población puede seguir esperando el servicio. Este mecanismo general no demuestra la causa de cada paralización.

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

El dashboard incluye cuatro indicadores, mapa departamental y gráficos por tipo, avance y causa. Cinco filtros permiten explorar departamento, tipo, avance, presupuesto y año de inicio. La consulta final busca por nombre, entidad o código INFOBRAS y permite descargar la selección en CSV. La cartografía procede del servicio del MEF, atribuido al INEI en sus metadatos, y se utiliza con fines referenciales; se conserva con su fuente en `web/data/`.

El material audiovisual utiliza Python 3.12 en un entorno separado:

```console
python -m pip install -r tarea_3/reel/requirements.txt
python tarea_3/scripts/generar_reel.py
```

Sin narración, este comando reproduce `reel/vista_previa.mp4`, de 60 segundos, con la pista «Divider», de Chris Zabriskie, bajo licencia CC BY 4.0, y aviso visible de ausencia de voz. La síntesis utiliza otro entorno con `reel/requirements_voz.txt` y una referencia de voz propia mantenida fuera de la carpeta pública. Los créditos y enlaces de licencia están en `reel/recursos/creditos.md`.

Para sintetizar la narración, la referencia de 15–25 segundos y su transcripción exacta se ubican en una carpeta privada. Desde el entorno de voz:

```console
python -m pip install -r tarea_3/reel/requirements_voz.txt
python tarea_3/scripts/generar_narracion.py --referencia .cache/tarea3-voz/referencia.wav --transcripcion .cache/tarea3-voz/referencia.txt --salida .cache/tarea3-voz/salida
```

El modelo Base Qwen3-TTS 0.6B se descarga en la caché privada. Se sintetiza por oraciones y se reutilizan los fragmentos que coinciden en texto, referencia y parámetros. Se obtienen audio, tiempos por escena y subtítulos con el texto pronunciado. Desde el entorno de montaje:

```console
python tarea_3/scripts/generar_reel.py --narracion .cache/tarea3-voz/salida/narracion.wav --tiempos .cache/tarea3-voz/salida/tiempos_escenas.json --subtitulos .cache/tarea3-voz/salida/subtitulos.srt
```

El montaje exige 45–75 segundos y tiempos consecutivos para escenas y subtítulos. La voz recibe ecualización, compresión y control de picos para mejorar su presencia, y la música se atenúa durante el habla. La pronunciación y la sincronización se revisan escuchando el resultado. El video incorpora dos capturas del dashboard; sus imágenes originales están en `reel/recursos/dashboard_general.png` y `reel/recursos/dashboard_exploracion.png`.

## Uso de inteligencia artificial

Se utilizó IA para explorar bibliografía, desarrollar el código y apoyar la redacción. La narración se generó con Qwen3-TTS Base 0.6B a partir de una grabación de voz propia de 19,84 segundos, conservada en privado. Las cifras pronunciadas se contrastaron mediante transcripción automática. Los resultados del análisis se calculan a partir de archivos oficiales y se contrastan con el informe y los controles de calidad. Las interpretaciones se limitan a lo que permiten los datos.
