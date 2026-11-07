# Tarea 4 · Agente de investigación socioeconómica

**Estudiante** — Jose Pablo Navarro Nateros (@bocchienjoyer)

El agente analiza la evolución de la inflación interanual de Lima Metropolitana en 2024 y las brechas de pobreza monetaria entre áreas y departamentos del Perú en el mismo año. La ejecución y la evaluación se adaptaron a Codex.

## Arquitectura

Codex usa el [servidor MCP](mcp/server.py) para encontrar series (`buscar_series`), consultar valores (`serie`), resumirlos (`resumen`) y comparar series con períodos comunes (`comparar_series`). El servidor también ofrece el recurso `bcrp://serie/{codigo}` y el prompt `informe`.

Las tres [Skills de Codex](.agents/skills/) comparten los scripts en `.claude/skills/`. `limpiando-enaho` une y valida los módulos, `graficando-enaho` calcula tasas ponderadas y dibuja comparaciones, y `mapeando-enaho` une las tasas a los límites de las 25 unidades territoriales.

## Datos y entorno

Descarga los archivos en `datos/` conservando los nombres originales. Los ZIP se usan sin descomprimir y quedan fuera de Git.

- [INEI · ENAHO 2024, módulo 34, sumaria](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip)
- [INEI · ENAHO 2024, módulo 02, miembros](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip)
- [Límites departamentales · peru_departamental_simple.geojson](https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson)
- [BCRP · Series estadísticas oficiales](https://estadisticas.bcrp.gob.pe/estadisticas/series/)

Con Python 3.11 o superior y `uv` en la ruta de comandos, ejecuta desde esta carpeta:

```text
uv sync --frozen
uv run --frozen pytest -q
uv run --frozen python .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run --frozen python .claude/skills/graficando-enaho/scripts/graficar.py --anio 2024 --por area
uv run --frozen python .claude/skills/graficando-enaho/scripts/graficar.py --anio 2024 --por sexo
uv run --frozen python .claude/skills/graficando-enaho/scripts/graficar.py --anio 2024 --por departamento
uv run --frozen python .claude/skills/mapeando-enaho/scripts/mapear.py --anio 2024
uv run --frozen python scripts/graficar_bcrp.py
```

La suite contiene las ocho pruebas de referencia y dos para la comparación de series. La limpieza reproduce **108 664 residentes habituales**, **25 unidades territoriales** y una pobreza nacional de **27,58 %** con sumaria (`factor07 × mieperho`). Las tasas del gráfico por área y del mapa usan el factor individual `facpob07`. [Validación ENAHO](salidas/validacion.txt)

## Ejecución integrada

Inicia Codex en esta carpeta como proyecto de confianza. La configuración [.codex/config.toml](.codex/config.toml) conecta el servidor BCRP por entrada y salida estándar y Codex descubre las Skills en `.agents/skills/`. El archivo [.mcp.json](.mcp.json) conserva la configuración de Claude Code.

La [solicitud de investigación](informes/pregunta.md) reproduce el flujo. La ejecución registrada usó `buscar_series`, `serie` y `resumen`, leyó las tres Skills y produjo el [informe final](informes/informe_final.md), con el gráfico de inflación, el gráfico de pobreza por área y el mapa departamental. [Bitácora de integración](evidencias_ia/integracion/bitacora.json)

El IPC se refiere a Lima Metropolitana. Las estimaciones de ENAHO se refieren a la población y a las unidades geográficas definidas en cada cálculo. La comparación es descriptiva y las tasas de pobreza se presentan sin intervalos de confianza.

## Evaluación

Desde esta carpeta, con Codex CLI autenticado, ejecuta:

```text
uv run --frozen python evaluacion/ejecutar.py --modelo gpt-6.1-sol --registros ../../registros-tarea4
```

La ruta de registros debe estar fuera del repositorio y no contener una corrida anterior. Las diez preguntas se ejecutaron en sesiones separadas con las mismas tolerancias. Codex obtuvo **1/10** sin el paquete del proyecto y **10/10** con él. Los tiempos medios fueron **19,3 s** y **55,4 s**, respectivamente. [Preguntas](evaluacion/preguntas.csv) · [Resultados](evaluacion/resultados.csv) · [Comparación](evaluacion/comparacion.md)

## Evidencias de uso de IA

La [carpeta de evidencias](evidencias_ia/) reúne registros de la integración y de la evaluación.
