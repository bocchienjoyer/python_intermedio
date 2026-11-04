---
name: graficando-enaho
description: Genera gráficos ponderados de pobreza por área, grupo demográfico y departamento.
---

# graficando-enaho

Si falta la base procesada, activar `limpiando-enaho`. Guardar las figuras en `figuras/` con título, período, unidades y fuente.

Desde la raíz del proyecto, ejecutar `uv run python .claude/skills/graficando-enaho/scripts/graficar.py --anio 2024 --por area`. Elegir `area`, `sexo`, `edad` o `departamento` según la pregunta. El script llama a la limpieza si faltan sus archivos.
