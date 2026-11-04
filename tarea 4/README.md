# Tarea 4 · Agente de investigación socioeconómica

**Estudiante** — Jose Pablo Navarro Nateros (@bocchienjoyer)

El proyecto integra las series oficiales del BCRP y los microdatos ENAHO 2024 en Codex. El servidor MCP se encarga de las consultas macroeconómicas y las Skills coordinan la limpieza, los gráficos y el mapa de pobreza.

## Fuentes

- [INEI · ENAHO 2024, módulo 34](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip)
- [INEI · ENAHO 2024, módulo 02](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip)
- [Límites departamentales del Perú](https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson)
- [BCRP · Series estadísticas](https://estadisticas.bcrp.gob.pe/estadisticas/series/)

## Entorno y datos

Desde esta carpeta, instala las dependencias con `uv sync`. Guarda los dos ZIP de ENAHO con sus nombres originales en `datos/` y guarda allí el GeoJSON departamental. Codex usa `.codex/config.toml` para iniciar el MCP BCRP en esta carpeta de proyecto y descubre las Skills en `.agents/skills/`.

## Archivos de trabajo

- [Servidor y pruebas MCP](mcp/)
- [Skills de ENAHO](.claude/skills/)
- [Validación e indicadores](salidas/)
- [Evaluación comparativa](evaluacion/)
- [Informe de investigación](informes/informe_final.md)
- [Evidencias de uso de IA](evidencias_ia/)

## Reproducir ENAHO 2024

```text
uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run python .claude/skills/graficando-enaho/scripts/graficar.py --anio 2024 --por area
uv run python .claude/skills/graficando-enaho/scripts/graficar.py --anio 2024 --por sexo
uv run python .claude/skills/graficando-enaho/scripts/graficar.py --anio 2024 --por departamento
uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --anio 2024
```

La limpieza valida el universo de residentes y guarda sus controles en `salidas/validacion.txt`. Los gráficos y el mapa estiman tasas de personas con `facpob07`. El mapa contrasta esas tasas con el archivo de referencia departamental de la Sesión 16, calculado con sumaria y un ponderador distinto.
