# Cotejo de cifras

Cotejo realizado por Codex con las respuestas del MCP y los archivos agregados de esta ejecución.

## BCRP

Se cotejaron los valores mensuales de `serie` con los meses y cifras que devolvió `resumen` para el inicio, máximo, mínimo y cierre de 2024. Se confirmó la cobertura de los doce meses consecutivos. [Serie oficial PN01273PM](https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2024-1/2024-12)

| Mes | `serie` | `resumen` |
| --- | ---: | ---: |
| 2024-01 | 3,02392 % | 3,02392 % |
| 2024-02 | 3,29407 % | 3,29407 % |
| 2024-09 | 1,77501 % | 1,77501 % |
| 2024-12 | 1,96630 % | 1,96630 % |

## ENAHO

Se recalculó cada tasa como 100 × población pobre expandida ÷ población total expandida. Las cinco cifras coinciden con las tasas de los CSV a cinco decimales. [Tabla por área](../figuras/pobreza_area_2024.csv) · [Tabla departamental](../mapas/pobreza_departamento.csv)

| Unidad | Tasa recalculada |
| --- | ---: |
| Rural | 39,44168 % |
| Urbana | 24,73524 % |
| Cajamarca | 44,99496 % |
| Ica | 5,91394 % |
| Loreto | 42,60510 % |

La diferencia absoluta entre la estimación nacional de personas (27,52873 %) y la referencia (27,6 %) fue 0,07127 puntos porcentuales. [Control nacional](../salidas/validacion.txt)

## Cotejo manual

El 7 de noviembre de 2026 cotejé tres cifras del informe con la tabla del BCRP y las salidas de ENAHO. Las tres coinciden a dos decimales.

| Indicador | Procedimiento | Valor cotejado | Valor en el informe |
| --- | --- | ---: | ---: |
| Inflación interanual de Lima Metropolitana, diciembre de 2024 | Lectura de la fila Dic2024 en la serie PN01273PM | 1,97 % | 1,97 % |
| Pobreza monetaria rural, ENAHO 2024 | Población pobre expandida ÷ población total expandida × 100 | 39,44168 % | 39,44 % |
| Pobreza monetaria urbana, ENAHO 2024 | Población pobre expandida ÷ población total expandida × 100 | 24,73524 % | 24,74 % |

[Tabla del BCRP](https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/grafico/) · [Tasas de ENAHO por área](../figuras/pobreza_area_2024.csv)
