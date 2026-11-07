# Ejecución integrada

### Solicitud de ejecución preparada por Codex

En esta carpeta aislada, ejecuta informes/pregunta.md. Usa efectivamente al menos dos herramientas del MCP BCRP y lee las Skills del proyecto en .agents/skills antes de ejecutar los scripts ENAHO. Genera el gráfico BCRP con scripts/graficar_bcrp.py y el informe. No delegues ni busques resultados en otras carpetas. Mantén los microdatos localmente y muestra solo resultados agregados. No afirmes revisión humana.

### Codex

Leeré `informes/pregunta.md` y las tres skills de ENAHO antes de ejecutar los scripts. También consultaré el MCP BCRP para generar el gráfico y el informe con resultados agregados.

### Codex

El MCP devolvió los doce meses y el gráfico de inflación ya está generado. La limpieza ENAHO pasó los controles y el mapa cubre las 25 unidades territoriales. Estoy contrastando las cifras que citaré con las tablas agregadas.

### Codex

Generé el [informe final](../../informes/informe_final.md), el [gráfico de inflación del BCRP](../../figuras/inflacion_lima_2024.png), el [gráfico de pobreza por área](../../figuras/pobreza_area_2024.png) y el [mapa departamental](../../mapas/pobreza_departamento.png).

- La inflación interanual de Lima Metropolitana bajó de **3,02 % en enero a 1,97 % en diciembre**, una caída de **1,06 puntos porcentuales**.
- La pobreza monetaria fue de **39,44 % en el área rural** y **24,74 % en la urbana**, una brecha de **14,71 puntos porcentuales**.
- Cajamarca registró la tasa departamental más alta (**44,99 %**) e Ica la más baja (**5,91 %**).

Usé `buscar_series`, `serie` y `resumen` del MCP BCRP. ENAHO pasó los controles de limpieza y los microdatos permanecieron en la carpeta local. El [cotejo de cifras realizado por Codex](../../informes/verificacion_cifras.md) y el [registro de ejecución](ejecucion.jsonl) quedaron guardados por separado.
