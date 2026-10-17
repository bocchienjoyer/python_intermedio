# ¿Podemos clasificar titulares peruanos por su tema?

Tarea 1 individual de Python Intermedio. Fuente elegida: **La República**.

Consigna: [2026_Tarea_1, issue #188](https://github.com/d2cml-ai/Data-Science-Python/issues/188).

## Estado del trabajo

Inicio: 17 de octubre de 2026 (Perú, UTC-5). **Recolección completada: 400 noticias reales, 100 por categoría**, con las siete columnas y enlaces comprobados (respuesta final HTTP 200). El notebook `01_recoleccion.ipynb` está ejecutado con sus tres gráficos, controles y tablas.

El baseline zero-shot sobre 40 titulares de validación obtuvo **accuracy 0,675 y F1 macro 0,6696**. La partición congelada contiene 280 noticias para entrenamiento, 60 para validación y 60 para test, con proporciones iguales por categoría. El etiquetado LLM y la auditoría humana están en desarrollo; todavía no se ha evaluado el test.

El RSS ofrece un conjunto reciente reducido; el descubrimiento se amplía con las secciones HTML y noticias relacionadas enlazadas por el medio. Se conserva la procedencia de cada enlace y no se utilizan rutas restringidas de paginación.

## Reproducir la recolección

Entorno local preparado con Python 3.13.5. Desde la raíz del repositorio, crear un entorno virtual e instalar `tarea_1/requirements.txt`. Luego:

```text
python tarea_1/src/recoleccion.py --piloto --por-categoria 10
python tarea_1/src/recoleccion.py --por-categoria 100
```

La caché está en `tarea_1/datos/raw/`. Los respaldos XML y HTML completos se conservan localmente y no se versionan; el registro de solicitudes, el archivo de candidatos y las tablas de limpieza permiten revisar la procedencia. El recolector puede reutilizar la caché con `--offline`. La muestra final se acota a publicaciones desde el 1 de enero de 2026; se registra el descarte de enlaces históricos.

## Fuentes y fechas

Fuente única: La República. Descarga finalizada el **17 de octubre de 2026 a las 09:10 (UTC-5)**. Las publicaciones seleccionadas abarcan **11 de enero a 17 de octubre de 2026**. Se usan RSS, sitemaps, secciones y enlaces públicos relacionados; el descubrimiento contiene 2.269 URLs únicas, pero solo se presentan como noticias recolectadas las 400 seleccionadas y verificadas.

Se descartaron durante la extracción 98 artículos anteriores a 2026, 13 titulares casi duplicados, 3 titulares duplicados y 1 enlace inexistente (404). Las tablas separan esos descartes de las URLs repetidas encontradas al combinar fuentes.

## Dos hallazgos del análisis exploratorio

1. **El 14 de octubre de 2026 concentra 32 de las 400 noticias (8%)**, la mayor cantidad para una fecha en esta muestra. La concentración reciente depende de las fuentes de descubrimiento, no de un censo de publicaciones del medio.
2. **La mediana de longitud es 107 caracteres.** El histograma y los cinco titulares más cortos/largos permiten comprobar que los extremos corresponden a textos reales y no a errores de extracción.

El equilibrio de 100 noticias por categoría es una cuota de diseño: no demuestra que el diario publique los cuatro temas con igual frecuencia.

## Limitaciones técnicas

1. La muestra depende de enlaces accesibles, un único diario y cuotas por categoría; sus proporciones y período no representan toda la producción periodística peruana.
2. La referencia procede de secciones editoriales y puede contener noticias que mezclen política y economía u otros temas. El acuerdo del LLM con esa referencia no sustituye la auditoría humana; su confianza declarada tampoco está calibrada.

## Entorno y ejecución

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tarea_1/requirements.txt
```

Para usar GPU NVIDIA compatible, instalar PyTorch CUDA 12.6 en ese entorno antes de las demás dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu126
```

El notebook usa Plotly y Kaleido para conservar figura interactiva e imagen estática. Para regenerar las imágenes se necesita Chrome/Chromium o Microsoft Edge; el equipo de desarrollo usa Edge. Las figuras ya están incluidas en el notebook entregado.

La app se ejecutará desde `tarea_1/` con el entorno activo mediante `streamlit run app.py`. La reproducción de los pesos y los resultados de clasificación se documentarán al completar la siguiente etapa.

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

