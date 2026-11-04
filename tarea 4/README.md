# Tarea 4 · Agente de investigación socioeconómica

**Estudiante** — Jose Pablo Navarro Nateros (@bocchienjoyer)

El proyecto integra las series oficiales del BCRP y los microdatos ENAHO 2024 en Claude Code. El servidor MCP se encarga de las consultas macroeconómicas y las Skills coordinan la limpieza, los gráficos y el mapa de pobreza.

## Fuentes

- [INEI · ENAHO 2024, módulo 34](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip)
- [INEI · ENAHO 2024, módulo 02](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip)
- [Límites departamentales del Perú](https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson)
- [BCRP · Series estadísticas](https://estadisticas.bcrp.gob.pe/estadisticas/series/)

## Entorno y datos

Desde esta carpeta, instala las dependencias con `uv sync`. Descarga y extrae los dos módulos de ENAHO en `datos/` y guarda allí el GeoJSON departamental. Claude Code usa `.mcp.json` para localizar el servidor al abrir esta carpeta como proyecto.

## Archivos de trabajo

- [Servidor y pruebas MCP](mcp/)
- [Skills de ENAHO](.claude/skills/)
- [Validación e indicadores](salidas/)
- [Evaluación comparativa](evaluacion/)
- [Informe de investigación](informes/informe_final.md)
- [Evidencias de uso de IA](evidencias_ia/)
