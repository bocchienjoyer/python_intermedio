# ¿Podemos clasificar titulares peruanos por su tema?

Tarea 1 individual de Python Intermedio. Fuente elegida: **La República**.

Consigna: [2026_Tarea_1, issue #188](https://github.com/d2cml-ai/Data-Science-Python/issues/188).

## Estado del trabajo

Inicio: 17 de octubre de 2026 (Perú, UTC-5). Se prepara el piloto y la recolección.
Los resultados, métricas y hallazgos se incorporarán después de ejecutarlos; todavía no hay un modelo entrenado.

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

