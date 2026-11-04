# Comparación con y sin MCP y Skills

## Diseño del experimento

Las diez preguntas y sus tolerancias se fijan antes de ejecutar Codex. Cada pregunta se ejecuta en una sesión nueva en cada modo, con el mismo modelo, esfuerzo de razonamiento bajo, permisos y texto de solicitud. La comparación mide el acceso al conjunto de MCP, Skills y datos del proyecto.

- **Modo A**. Directorio aislado sin MCP, Skills, microdatos ni salidas del proyecto.
- **Modo B**. Copia del proyecto con MCP, Skills y datos de entrada. Se excluyen la clave de evaluación y las salidas generadas antes de la sesión.

Registrar las herramientas disponibles en cada entorno y las utilizadas en cada ejecución. Calificar según los criterios de `preguntas.csv`. Las preguntas mixtas requieren exactitud en ambos indicadores y una interpretación compatible con sus ámbitos.

## Aciertos, errores y tiempos

## Conclusión
