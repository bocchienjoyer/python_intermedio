# Tarea 1. Noticias peruanas, del titular al clasificador

**Estudiante:** Jose Pablo Navarro Nateros (@bocchienjoyer).

## Pregunta

¿Se pueden convertir titulares peruanos en un clasificador de noticias?

## Medio y fechas de extracción

Se eligió **La República (opción A)**. La descarga se realizó el 17 de octubre de 2026 usando
RSS, sitemaps, secciones públicas y enlaces relacionados. Las 400 noticias seleccionadas se
publicaron entre el 11 de enero y el 17 de octubre de 2026: 100 por cada categoría.

Se respetó `robots.txt`, con un User-Agent académico, pausas de 1,5–2 segundos y máximo un
reintento. Se registraron 117 descartes: 98 publicaciones anteriores a 2026, 16 titulares
duplicados o casi duplicados, un enlace 404 y dos casos descartados en la revisión humana.
Estos dos últimos eran de entrenamiento y se sustituyeron sin modificar validación ni test.

| Archivo | Contenido |
| --- | --- |
| [01_recoleccion.ipynb](01_recoleccion.ipynb) | Recolección, limpieza, equivalencias y tres gráficos Plotly. |
| [02_clasificacion.ipynb](02_clasificacion.ipynb) | Zero-shot, LLM, auditoría, entrenamiento y evaluación. |
| [app.py](app.py) | Dashboard con filtros, descarga CSV y clasificación en vivo. |
| `datos/noticias.csv` | 400 noticias con las siete columnas requeridas. |
| `datos/etiquetas_llm.csv` | Categoría, confianza, modelo y fecha del etiquetado LLM. |

Todo el código del procedimiento está dentro de los notebooks. Los respaldos de la descarga,
las respuestas originales del LLM y las particiones se conservan en `datos/raw/`.

## Resultados

Partición estratificada 70/15/15, semilla 42: 280 noticias de entrenamiento, 60 de validación
y 60 de test. DistilBERT se entrenó con las etiquetas de Qwen durante tres épocas, batch 8.
El mejor checkpoint se eligió por F1 macro de validación. El test usa la sección del diario
como referencia y no se empleó para ajustar los parámetros.

| Método | F1 macro en las mismas 60 noticias de test |
| --- | ---: |
| Zero-shot Recognai/BETO-XNLI | 0,7925 |
| Qwen2.5-1.5B-Instruct, solo titular | 0,7609 |
| DistilBERT multilingüe ajustado | **0,8198** |

El baseline inicial solicitado, sobre 40 titulares de validación, obtuvo F1 macro **0,6696**.
La auditoría humana obtuvo **13/20 acuerdos (65%)**; los dos descartes cuentan como desacuerdos.
La accuracy de DistilBERT en test fue **0,8167**. Los cuadernos muestran las salidas y la matriz
de confusión; `modelo/metricas.json` permite que la app presente esos mismos indicadores.

## Dos hallazgos

1. El 14 de octubre concentra 32 de las 400 noticias (8%), el máximo de una fecha en esta muestra.
2. La mediana de longitud de los titulares es 107 caracteres. El notebook muestra los cinco
   titulares más cortos y más largos para comprobar los extremos del histograma.

## Dos limitaciones

1. Se utiliza un solo medio y una muestra por cuotas y enlaces accesibles. Los 60 casos de test
   son pocos para generalizar el desempeño a otros medios, períodos o temas.
2. Las secciones editoriales mezclan asuntos, especialmente política y economía. El acuerdo
   humano del 65% revela ambigüedad y ruido en las etiquetas; las probabilidades no están calibradas.

## Cómo ejecutar en local

Desde la raíz del repositorio, con Python 3.13, crear el entorno e instalar las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r tarea_1/requirements.txt
```

En una copia nueva, **antes de iniciar la app**, abrir `tarea_1/02_clasificacion.ipynb` en
VS Code, seleccionar el entorno `.venv` como kernel y ejecutar todas las celdas. Esto genera
`modelo/model.safetensors`, cuyos pesos superan 500 MB y están excluidos de GitHub.
La primera ejecución necesita Internet para descargar los modelos base; el entrenamiento
admite CPU o GPU. No se necesita una API: se reutilizan las etiquetas LLM y sus respuestas válidas.

Con los pesos disponibles, iniciar la app desde la raíz del repositorio:

```powershell
cd tarea_1
streamlit run app.py
```

La app se abre en `http://localhost:8501`. Los gráficos de los notebooks incluyen una imagen
para su lectura en GitHub; para regenerarlas se necesita Chrome/Chromium o Microsoft Edge.
