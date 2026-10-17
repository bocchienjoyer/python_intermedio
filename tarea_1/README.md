# ¿Podemos clasificar titulares peruanos por su tema?

Tarea 1 individual de Python Intermedio. **Estudiante: Jose Pablo Navarro Nateros (@bocchienjoyer).**
Fuente: **La República, opción A**. [Consigna del curso](https://github.com/d2cml-ai/Data-Science-Python/issues/188).

Se recolectaron **400 noticias reales, 100 por categoría**, y se compararon zero-shot, Qwen local
y DistilBERT ajustado con etiquetas de Qwen. La app permite explorar las noticias y clasificar
un titular nuevo con el modelo entrenado.

## Datos, fuentes y fechas

Extracción inicial: **17 de octubre de 2026, 09:10 (UTC-5)**. Correcciones humanas: **09:31**.
Publicaciones: **11 de enero a 17 de octubre de 2026**. El CSV contiene exactamente
`titular,bajada,medio,seccion_original,url,fecha,etiqueta`.

Se consultan [robots.txt](https://larepublica.pe/robots.txt), los RSS oficiales de
[política](https://larepublica.pe/rss/politica.xml), [economía](https://larepublica.pe/rss/economia.xml),
[deportes](https://larepublica.pe/rss/deportes.xml) y [ciencia](https://larepublica.pe/rss/ciencia.xml),
sus sitemaps, secciones públicas y noticias relacionadas enlazadas por el medio. Se descubrieron
2.269 URLs únicas; solo se presentan como dataset las 400 noticias completas seleccionadas,
verificadas con HTTP 200 al descargarlas.

`datos/verificacion_urls.csv` documenta 399 enlaces directos y una redirección legítima del diario
a una noticia actualizada; los 400 destinos finales respondieron HTTP 200. Se conserva la URL
original para mantener la identidad de la noticia y las particiones congeladas.

Limpieza: 98 publicaciones anteriores a 2026, 13 titulares casi duplicados, 3 titulares duplicados,
1 enlace HTTP 404 y 2 descartes humanos: **117 descartes**. Se registran aparte 60 URLs repetidas
en el descubrimiento. Los candidatos no descargados al completar una cuota no se cuentan como
noticias recolectadas ni como descartes.

El estudiante revisó 20 titulares aleatorios de train/validación y descartó una noticia arqueológica
y un accidente por quedar fuera del alcance. Ambas eran de train: se sustituyeron por noticias
reales de su misma categoría. Se conservaron 400 filas, cuotas y los titulares originales de
validación/test. La auditoría permanece íntegra: los dos descartes cuentan como desacuerdos.
No se añadió una quinta categoría.

## Dos hallazgos del análisis exploratorio

1. **El 14 de octubre concentra 32 de las 400 noticias (8%)**, el máximo de una fecha en esta muestra.
   La concentración reciente depende de los enlaces disponibles; no es un censo del diario.
2. **La mediana de longitud es 107 caracteres.** El histograma y los cinco titulares más cortos/largos
   permiten verificar que los extremos corresponden a textos reales.

El equilibrio de 100 noticias por categoría es una cuota de diseño, no la frecuencia natural de
cada tema. Las tres figuras interactivas y sus imágenes para GitHub están en
[01_recoleccion.ipynb](01_recoleccion.ipynb).

## Clasificación y resultados

Split inicial estratificado **70/15/15**, `random_state=42`: 280 train, 60 validación y 60 test.
Los dos reemplazos humanos solo modificaron train, manteniendo 70/15/15 noticias por categoría.
Baseline inicial en 40 titulares de validación: **accuracy 0,675; F1 macro 0,6696**.

Qwen etiqueta las 400 noticias solo a partir del titular, sin sección ni referencia. Se entrenó
`distilbert/distilbert-base-multilingual-cased` con `HuggingFace Trainer`, tres épocas, batch 8,
longitud máxima 128 y learning rate 2e-5. Train usa `etiqueta_llm`; validación/test usan la sección
editorial normalizada. El checkpoint se eligió por F1 macro de validación (mejor **0,8029**)
antes de abrir test. No se ajustaron parámetros después de evaluar test.

Comparación sobre **las mismas 60 noticias de test**:

| Método | Accuracy | F1 macro |
| --- | ---: | ---: |
| Zero-shot Recognai/BETO-XNLI | 0,8000 | 0,7925 |
| Qwen2.5-1.5B-Instruct local | 0,7667 | 0,7609 |
| DistilBERT ajustado | **0,8167** | **0,8198** |

Auditoría humana: **13/20 = 65%** de acuerdo con Qwen. Se respetan las decisiones reales del
estudiante, aunque difieran de las secciones del diario. La confianza de Qwen normalmente es
declarada; en 4 casos finales se utilizó una elección restringida y su probabilidad entre cuatro
opciones. Esas confianzas no están calibradas ni son directamente comparables entre estrategias.

La app usa DistilBERT: en este test obtuvo el mayor F1 y menor latencia de inferencia GPU
(7,1 ms/titular frente a 15,7 ms del zero-shot, por lotes y sin carga). La app funciona en CPU;
esas cifras no representan su latencia web. Qwen evita pagos por API, pero requiere más memoria
y generación de texto por consulta. [02_clasificacion.ipynb](02_clasificacion.ipynb) incluye las
métricas recalculadas, matriz de confusión Seaborn, errores por categoría y comparación.

## Dos limitaciones técnicas

1. Un único medio, cuotas y enlaces accesibles limitan la representatividad temporal y temática.
   Solo hay 60 casos de test (15 por categoría); las diferencias son pequeñas y no se afirma
   significancia estadística ni generalización a otros medios.
2. Las secciones editoriales mezclan política/economía y consumo/tecnología. No son un etiquetado
   humano exhaustivo. El acuerdo humano de 65% revela ambigüedad y ruido de supervisión;
   ninguna probabilidad presentada está calibrada para expresar certeza real.

## Entorno y ejecución local

Entorno comprobado: Python **3.13.5** en Windows, con versiones fijadas en `requirements.txt`.
Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tarea_1/requirements.txt
.\.venv\Scripts\python.exe tarea_1/src/modelado.py --paso entrenar
.\.venv\Scripts\python.exe -m streamlit run tarea_1/app.py
```

El entrenamiento utiliza los CSV entregados y descarga el modelo base público si falta en caché.
Genera pesos en `tarea_1/modelo/`, sin API ni regeneración de etiquetas Qwen. **En este equipo los
pesos ya están entrenados: basta el último comando.** Los pesos grandes se excluyen de GitHub;
una copia nueva debe entrenar para activar el probador. La configuración y el tokenizador ligeros
sí se versionan. Se admite CPU; la duración depende del equipo.

Para GPU NVIDIA compatible, instalar PyTorch CUDA 12.6 **antes** de las otras dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu126
```

Alternativamente, con el entorno activado:

```powershell
.\.venv\Scripts\Activate.ps1
cd tarea_1
streamlit run app.py
```

Se abre en `http://localhost:8501`: filtros por medio/categoría, total, F1 de test, acuerdo humano,
Plotly, tabla, descarga CSV y clasificación en vivo. El despliegue público es opcional.

Prueba funcional automatizada desde la raíz (UTF-8 explícito en Windows):

```powershell
.\.venv\Scripts\python.exe -X utf8 tarea_1/scripts/verificar_app.py
.\.venv\Scripts\python.exe -m pip check
```

Se probaron filtros, estados sin resultados, titular vacío e inferencia real en CPU. La descarga
desde el navegador se contrastó con el dataset: 400 filas y siete columnas idénticas.

### Reproducir las etapas completas

Desde la raíz, con el entorno activo:

```powershell
python tarea_1/src/recoleccion.py --por-categoria 100
python tarea_1/src/modelado.py --paso descargar
python tarea_1/src/modelado.py --paso particiones
python tarea_1/src/modelado.py --paso baseline
python tarea_1/src/modelado.py --paso llm
python tarea_1/src/modelado.py --paso auditoria
python tarea_1/src/modelado.py --paso entrenar
python tarea_1/src/modelado.py --paso evaluar
python tarea_1/scripts/ejecutar_notebook.py tarea_1/01_recoleccion.ipynb
python tarea_1/scripts/ejecutar_notebook.py tarea_1/02_clasificacion.ipynb
```

**Para reproducir el experimento entregado, conservar los CSV y saltar el primer comando.**
Recolectar de nuevo puede cambiar el sitio: hacerlo en una copia separada y crear nuevas
particiones/auditoría para ese experimento. La huella SHA-256 protege las particiones existentes
contra sobrescrituras accidentales. La revisión humana no se automatiza.

Los notebooks verifican datos y recalculan métricas desde las predicciones guardadas; sus banderas
permiten repetir etapas costosas. Ya contienen sus salidas ejecutadas. Para regenerar imágenes
Plotly/Kaleido se necesita Chrome/Chromium o Microsoft Edge (usado en este equipo). No hace falta
instalar un navegador para leer las figuras incluidas.

## Trazabilidad y acceso respetuoso

- `src/recoleccion.py`: requests + BeautifulSoup, Protego para robots, User-Agent descriptivo,
  pausa secuencial de 1,5–2 segundos y máximo un reintento. No construye paginación restringida.
- `datos/raw/`: XML/HTML crudos locales, robots y registro de solicitudes. Los respaldos XML/HTML
  completos y sus cachés no se suben a Git; se entregan las URLs, metadatos y registros.
- `candidatos.csv`, `mapeo_secciones.csv`, `descartes*.csv`: procedencia y limpieza.
- `noticias_antes_auditoria.csv`, `correcciones_auditoria.csv`, `particiones.csv`: revisión y splits.
- `resultados/`: revisiones fijas de modelos, prompts, respuestas reales, normalización,
  auditoría, historial de entrenamiento y predicciones de test.
- `modelo/`: configuración/tokenizador; pesos y checkpoints ignorados. No se usan claves API.

## Bitácora de GitHub

- [Parte 1: Recolección y Limpieza](https://github.com/bocchienjoyer/python_intermedio/issues/1)
- [Parte 2: Modelado y Clasificación](https://github.com/bocchienjoyer/python_intermedio/issues/2)
- [Parte 3: Dashboard y Despliegue](https://github.com/bocchienjoyer/python_intermedio/issues/3)

Inicio real: **17 de octubre de 2026**. Los commits documentan etapas reales. Una revisión adicional
el 18 permitiría registrar trabajo en otro día; no se alteran fechas del historial.

El texto de entrega está preparado en `entrega_borrador.txt`; su publicación en el issue del curso
queda a cargo del estudiante. La ejecución local y la descarga CSV se comprobaron en navegador.
