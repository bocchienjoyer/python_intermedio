---
name: mapeando-enaho
description: Genera un mapa departamental de pobreza monetaria con ENAHO 2024.
---

# mapeando-enaho

Si falta la base procesada, activar `limpiando-enaho`. Unir `ubigeo[:2]` con `FIRST_IDDP`, verificar 25 unidades con Lima y Callao separados y guardar el mapa en `mapas/`.

Desde la raíz del proyecto, ejecutar `uv run python .claude/skills/mapeando-enaho/scripts/mapear.py --anio 2024`. El script llama a la limpieza si faltan sus archivos y registra las diferencias con la referencia de sumaria en el CSV del mapa.
