# ¿Podemos clasificar titulares peruanos por su tema?

Tarea 1 individual de Python Intermedio. Fuente elegida: **La República**.

Consigna: [2026_Tarea_1, issue #188](https://github.com/d2cml-ai/Data-Science-Python/issues/188).

## Estado del trabajo

Inicio: 17 de octubre de 2026 (Perú, UTC-5). **Piloto completado: 40 noticias reales, 10 por categoría**, con las siete columnas y enlaces comprobados (HTTP 200). Se amplía la muestra a 100 noticias por categoría.
Los resultados de modelado y hallazgos finales se incorporarán después de ejecutarlos; todavía no hay un modelo entrenado.

El RSS ofrece un conjunto reciente reducido; el descubrimiento se amplía con las secciones HTML y noticias relacionadas enlazadas por el medio. Se conserva la procedencia de cada enlace y no se utilizan rutas restringidas de paginación.

## Reproducir la recolección

Entorno local preparado con Python 3.13.5. Desde la raíz del repositorio, crear un entorno virtual e instalar `tarea_1/requirements.txt`. Luego:

```text
python tarea_1/src/recoleccion.py --piloto --por-categoria 10
python tarea_1/src/recoleccion.py --por-categoria 100
```

La caché está en `tarea_1/datos/raw/`. Los HTML completos comprimidos se conservan localmente y no se versionan; los RSS, metadatos y registros sí permiten revisar la procedencia. El recolector puede reutilizar la caché con `--offline`.

## Método previsto

1. Recolectar aproximadamente 400 noticias reales: política, economía, deportes y ciencia/tecnología.
2. Normalizar las secciones, conservar los datos crudos y documentar descartes.
3. Separar train/validación/test (70/15/15, semilla 42) antes de ajustar modelos.
4. Comparar zero-shot, etiquetas LLM y un Transformer entrenado.
5. Auditar humanamente 20 etiquetas y mostrar los resultados reales en Streamlit.

La categoría derivada de la sección se mantiene separada de la predicción LLM. La entrada de todos los clasificadores será el titular, igual que en la app.

## Bitácora

- [Parte 1: Recolección y Limpieza](https://github.com/bocchienjoyer/python_intermedio/issues/1)
- [Parte 2: Modelado y Clasificación](https://github.com/bocchienjoyer/python_intermedio/issues/2)
- [Parte 3: Dashboard y Despliegue](https://github.com/bocchienjoyer/python_intermedio/issues/3)

## Acceso respetuoso a la fuente

El recolector comprueba `robots.txt`, usa un User-Agent descriptivo, espera 1,5–2 segundos entre solicitudes y realiza como máximo un reintento por solicitud fallida. Conserva las respuestas y un registro de solicitudes para evitar descargas repetidas.

Los pesos y las claves no se suben a GitHub. Los CSV obligatorios y las salidas de los notebooks sí se conservan.

