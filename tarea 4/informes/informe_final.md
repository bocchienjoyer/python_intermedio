# Inflación en Lima Metropolitana y pobreza monetaria en Perú, 2024

## Pregunta de investigación

¿Cómo evolucionó la inflación interanual de Lima Metropolitana a lo largo de 2024 y qué brechas de pobreza monetaria se observaron ese año entre áreas urbanas y rurales y entre departamentos del Perú?

## Hallazgos

1. **La inflación interanual de Lima Metropolitana bajó 1,06 puntos porcentuales entre enero y diciembre.** Pasó de 3,02 % a 1,97 %. Alcanzó su máximo en febrero (3,29 %) y su mínimo en septiembre (1,78 %). Repuntó hasta 2,27 % en noviembre y volvió a bajar en diciembre. El promedio de las doce tasas interanuales fue 2,35 %. [Serie oficial BCRP PN01273PM](https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2024-1/2024-12)
2. **La pobreza monetaria rural superó a la urbana en 14,71 puntos porcentuales.** El 39,44 % de los residentes habituales rurales y el 24,74 % de los urbanos vivían en hogares en situación de pobreza monetaria. La estimación nacional con el mismo ponderador fue 27,53 %. La brecha se calculó antes de redondear las tasas. [Tabla por área](../figuras/pobreza_area_2024.csv) · [Indicadores nacionales](../salidas/indicadores.csv)
3. **Entre las 25 unidades del mapa, Cajamarca e Ica registraron los extremos.** Cajamarca tuvo 44,99 % e Ica 5,91 %, una distancia de 39,08 puntos porcentuales. Loreto alcanzó 42,61 %. Callao (33,77 %) y el departamento de Lima (26,89 %) se estimaron por separado. [Tabla departamental](../mapas/pobreza_departamento.csv)

## Visualizaciones

- [Inflación interanual de Lima Metropolitana](../figuras/inflacion_lima_2024.png)
- [Pobreza monetaria por área urbana y rural](../figuras/pobreza_area_2024.png)
- [Mapa departamental de pobreza monetaria](../mapas/pobreza_departamento.png)

## Fuentes, método y alcance

El IPC general de Lima Metropolitana corresponde a la serie mensual `PN01273PM` del BCRP, consultada de enero a diciembre de 2024. La unidad es la variación porcentual del IPC respecto del mismo mes del año anterior. Se usaron las herramientas MCP `buscar_series`, `serie` y `resumen`. La consulta devolvió 12 de 12 meses. [Datos oficiales del BCRP](https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2024-1/2024-12)

Para ENAHO 2024 se usaron los módulos 02 y 34 del INEI. Se unieron los residentes habituales con la sumaria por hogar mediante una unión de muchos a uno, con llaves de texto y ceros iniciales. Se estimó la proporción de personas pobres, extremas y no extremas, usando `facpob07`. La validación confirmó 108 664 residentes, cero residentes sin hogar, cero filas perdidas o duplicadas, pesos positivos y finitos y códigos de pobreza completos. El contraste con la referencia nacional de 27,6 % pasó la tolerancia de 0,1 puntos porcentuales tanto para personas (27,52873 %) como para sumaria (27,57947 %, con `factor07 * mieperho`). El mapa unió el código departamental del ubigeo con `FIRST_IDDP` y registró cero unidades sin dato. [Validación ENAHO](../salidas/validacion.txt) · [Control del mapa](../mapas/pobreza_departamento.json)

El IPC describe Lima Metropolitana, mientras que ENAHO cubre el Perú y el mapa presenta al departamento de Lima como unidad territorial. Las estimaciones de pobreza son puntuales y se calcularon sin errores estándar del diseño muestral. La comparación es descriptiva y no permite atribuir las brechas de pobreza a la trayectoria del IPC.

## Registro de ejecución

Codex coordinó el MCP y las Skills en una sesión aislada. Los cuatro scripts de limpieza, gráfico ENAHO, mapa y gráfico BCRP finalizaron correctamente. [Bitácora de herramientas y Skills](../evidencias_ia/integracion/bitacora.json) · [Cotejo de cifras](verificacion_cifras.md)
