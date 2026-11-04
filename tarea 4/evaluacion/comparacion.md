# Comparación con y sin MCP y Skills

## Diseño del experimento

Las diez preguntas y sus tolerancias se fijan antes de ejecutar Claude Code. Cada pregunta se ejecuta en una sesión nueva en cada modo, con el mismo modelo y el mismo texto de solicitud.

- **Modo A**. Directorio aislado sin MCP, Skills, microdatos ni salidas del proyecto.
- **Modo B**. Copia del proyecto con MCP, Skills y datos de entrada. Se excluyen la clave de evaluación y las salidas generadas antes de la sesión.

Registrar las herramientas disponibles en cada entorno y las utilizadas en cada ejecución. Calificar según los criterios de `preguntas.csv`. Las preguntas mixtas requieren exactitud en ambos indicadores y una interpretación compatible con sus ámbitos.

## Aciertos, errores y tiempos

## Conclusión
