# Comparación con y sin MCP y Skills

## Diseño

Se ejecutaron las mismas diez preguntas en veinte sesiones independientes de Codex CLI con el modelo `gpt-6.1-sol`, razonamiento bajo y la misma solicitud para ambos modos. Las referencias, tolerancias y criterios se fijaron en [preguntas.csv](preguntas.csv) antes de observar las respuestas.

- **Modo A.** Directorio temporal vacío sin el MCP, las Skills, los microdatos ni las salidas del proyecto.
- **Modo B.** Directorio temporal con el MCP del BCRP, las tres Skills, los scripts y los datos de entrada. Se excluyeron las respuestas esperadas y las salidas calculadas de antemano.

Ambos modos conservaron las herramientas generales de Codex, como la terminal y la búsqueda web. Se ignoró la configuración personal. El modo B añadió el MCP y las Skills del proyecto. Cada pregunta empezó en un directorio nuevo. El tiempo se midió desde el inicio de Codex CLI hasta el fin de la respuesta, incluidos el arranque de herramientas y las consultas realizadas durante la sesión.

## Aciertos y tiempos

| Modo | Correctas | Incorrectas con cifra | Sin cifras suficientes | Tiempo medio |
| --- | ---: | ---: | ---: | ---: |
| A · Sin MCP ni Skills del proyecto | 1/10 | 0 | 9 | 19,3 s |
| B · Con MCP y Skills del proyecto | 10/10 | 0 | 0 | 55,4 s |

B01 fue correcta en ambos modos. En el modo A se verificó con una publicación del INEI encontrada mediante búsqueda web. Mejoraron B02, B03, B04, E01, E02, E03, E04, M01 y M02. Ninguna pregunta empeoró.

En las nueve respuestas sin cifras suficientes, el modo A señaló la falta de fuentes en el directorio. Varias explicaron el método sin calcular el indicador. El modo B consultó el MCP en las cuatro preguntas BCRP y las dos mixtas. En las cuatro preguntas ENAHO y las dos mixtas, el registro muestra la lectura de `limpiando-enaho` y el uso de la terminal para el procesamiento. Ambas respuestas mixtas distinguieron los ámbitos de los indicadores. [Respuestas y tiempos por pregunta](resultados.csv)

## Interpretación

En este conjunto, el entorno con herramientas y datos del proyecto produjo nueve respuestas correctas adicionales. El tiempo medio aumentó 36,1 segundos. El contraste mide la disponibilidad conjunta del MCP, las Skills y los datos de entrada. Con una sesión por pregunta y modo, los resultados describen esta corrida y no separan el aporte individual de cada componente.
