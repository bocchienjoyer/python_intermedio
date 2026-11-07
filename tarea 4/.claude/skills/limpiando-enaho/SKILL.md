---
name: limpiando-enaho
description: Procesa y valida los módulos 02 y 34 de ENAHO 2024 para estimar pobreza ponderada.
---

# limpiando-enaho

Aplicar las reglas de [procesamiento y validación](reference.md).

Desde la raíz del proyecto, ejecutar `uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024`. Revisar `salidas/validacion.txt` y usar `salidas/indicadores.csv` para citar las tasas nacionales y sus ponderadores.
