# Tarea 2: voces y documentos peruanos

¿Pueden convertirse documentos escaneados y entrevistas en audio en un archivo de texto estructurado y buscable?

Trabajo individual de Jose Pablo Navarro Nateros (@bocchienjoyer).

Estado: estructura inicial. Corpus, procesamiento, evaluación y dashboard aún no implementados.

## Corpus, fuentes y licencias

Por registrar: fuentes, licencias, atribución y fechas de extracción de cada documento y audio.

## Método y evaluación

Por desarrollar: OCR, ASR con VAD y diarización, limpieza, seudonimización y revisión humana; CER y WER sobre diez documentos y diez clips con referencias manuales, comparación de modelos y auditoría de veinte extracciones LLM.

## Hallazgos analíticos

Por completar con dos hallazgos sustentados en los resultados.

## Limitaciones técnicas

Por completar con dos limitaciones observadas.

## Ejecución local

Con la aplicación implementada y las dependencias fijadas, ejecutar desde `tarea_2/`:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt` contendrá únicamente las dependencias exactas de la aplicación. Las versiones y entornos de procesamiento se documentarán en los notebooks.

## Dashboard público

Enlace de Streamlit Community Cloud por incorporar tras el despliegue obligatorio.
