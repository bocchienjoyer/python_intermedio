"""Construye un cuaderno con los resultados reales y comprobaciones reproducibles."""

from pathlib import Path
import textwrap
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(value):
    cells.append(nbf.v4.new_markdown_cell(textwrap.dedent(value).strip()))


def code(value):
    cells.append(nbf.v4.new_code_cell(textwrap.dedent(value).strip()))


md("""
    # Del titular al clasificador: supervisión débil y evaluación reservada

    **Estudiante:** Jose Pablo Navarro Nateros (@bocchienjoyer). **Fecha:** 17 de octubre de 2026.
    **Medio:** La República (opción A). Entrada de los tres métodos: únicamente el titular.

    El LLM produce etiquetas de entrenamiento. Las secciones del diario constituyen una referencia
    independiente para validación/test, aunque pueden mezclar temas. El test se abrió una sola vez,
    después de cerrar el prompt, los hiperparámetros y la auditoría humana.

    Este cuaderno ejecuta las verificaciones y recalcula las métricas desde las predicciones guardadas.
    Las descargas, generación y entrenamiento se ejecutaron en `src/modelado.py`; sus registros reales
    se conservan en `resultados/`. Las banderas siguientes permiten repetir etapas costosas de forma
    explícita. No se necesita descargar modelos para leer o verificar las salidas entregadas.
""")
code("""
    from pathlib import Path
    import json
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from IPython.display import display
    from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split
    from src.modelado import LABELS, BASELINE, LLM, ENCODER, PROMPT, prepare_splits, metrics

    ROOT = Path.cwd()
    assert (ROOT / 'datos/noticias.csv').exists(), 'Ejecutar desde tarea_1/'
    def read_json(name):
        return json.loads((ROOT / 'resultados' / name).read_text(encoding='utf-8'))
    pd.set_option('display.max_colwidth', None)
    data = prepare_splits()
    display(data.groupby(['particion', 'etiqueta']).size().unstack('etiqueta'))
    display(pd.Series(read_json('revisiones_modelos.json'), name='revision_fijada').to_frame())
    assert len(data) == 400
""")
md("""
    ## 1. Baseline zero-shot en 40 titulares de validación

    Se usa `pipeline('zero-shot-classification')` con Recognai/BETO-XNLI, etiquetas candidatas
    en español y plantilla `Este titular trata sobre {}.`. Se seleccionaron diez noticias de cada
    categoría de **validación**, con semilla 42. Esta medición inicial no utiliza test.
    La comparación justa entre los tres métodos se presenta al final sobre el mismo test de 60.
""")
code("""
    REPETIR_BASELINE = False
    if REPETIR_BASELINE:
        from src.modelado import baseline
        baseline()
    base = pd.read_csv('resultados/baseline_40.csv')
    assert len(base) == 40 and set(base.url).issubset(set(data.query("particion == 'validacion'").url))
    assert base.etiqueta.value_counts().eq(10).all()
    base_metrics = metrics(base.etiqueta, base.prediccion)
    display(pd.DataFrame([{'muestra': '40 titulares de validación', **base_metrics}]))
    assert np.isclose(base_metrics['f1_macro'], read_json('baseline_40.json')['f1_macro'])
""")
md("""
    ## 2. Etiquetado completo con Qwen local

    Qwen2.5-1.5B-Instruct recibe un prompt estructurado, sin sección, URL ni etiqueta editorial.
    Genera JSON con categoría y confianza. Se normalizan equivalencias léxicas explícitas
    (por ejemplo, `política` → `politica` y `futbol` → `deportes`), sin consultar la referencia.
    Ante formato/categoría inválidos se solicita reparación; los casos persistentes usan una
    elección restringida entre cuatro letras con el mismo modelo y el mismo titular.

    Se conservan los intentos originales en `respuestas_llm.jsonl` y el mapeo en
    `normalizacion_llm.csv`. La confianza normalmente es declarada por Qwen; en la elección
    restringida es la probabilidad normalizada entre cuatro opciones. **No está calibrada y no
    es comparable directamente entre ambas estrategias.** No se usa como métrica de calidad.
""")
code("""
    print(PROMPT)
    REPETIR_LLM = False
    if REPETIR_LLM:
        from src.modelado import llm_labels
        llm_labels()  # Reutiliza respuestas válidas; borrar la caché solo en un experimento nuevo.
    weak = pd.read_csv('datos/etiquetas_llm.csv', keep_default_na=False)
    assert list(weak.columns) == ['titular', 'etiqueta_llm', 'confianza', 'modelo_llm', 'fecha']
    assert len(weak) == 400 and not weak.titular.duplicated().any()
    assert weak.etiqueta_llm.isin(LABELS).all() and weak.confianza.between(0, 1).all()
    assert set(weak.titular) == set(data.titular)
    print('CSV LLM:', weak.shape)
    display(pd.Series(read_json('llm.json'), name='valor').to_frame())
    display(data.query("particion == 'train'")[['titular']].head().merge(weak, on='titular'))
""")
md("""
    ### Auditoría humana: 20 casos aleatorios fuera del test

    Jose Pablo revisó los titulares sin ver la predicción del LLM. Su primera respuesta tenía
    un número repetido; se alineó por el orden y las explicaciones. Confirmó después tres decisiones:
    AFP = economía, SERFOR = economía y arqueología = descartar. El accidente del alcalde también
    se descartó. Se respetan sus elecciones temáticas incluso cuando difieren de la sección editorial.

    El acuerdo es **13/20 = 65%**. Los dos descartes cuentan como desacuerdos porque el LLM
    siempre elige entre cuatro categorías; `descartar` es una decisión de limpieza, no una quinta clase.
    La muestra original se conserva íntegra, sin reemplazar casos para mejorar el porcentaje.
    Este resultado pequeño no estima con precisión la calidad en toda la población de noticias.
""")
code("""
    from src.modelado import audit_report
    audit_metadata = audit_report()
    audit = pd.read_csv('resultados/auditoria_comparada.csv', keep_default_na=False)
    display(audit[['caso', 'titular', 'etiqueta_humana', 'decision_humana', 'etiqueta_llm', 'acuerdo']])
    assert len(audit) == 20 and audit_metadata['estado'] == 'completa'
    assert int(audit.acuerdo.sum()) == audit_metadata['acuerdos'] == 13
    print(f"Acuerdo LLM–humano: {audit_metadata['acuerdos']}/20 = {audit_metadata['porcentaje']:.0f}%")
    assert not set(audit.url).intersection(data.query("particion == 'test'").url)
""")
md("""
    ## 3. Partición 70/15/15, estratificada y reproducible

    El split inicial se realizó antes de modelar con `train_test_split`, `stratify` y
    `random_state=42`. Los dos casos descartados por el humano pertenecían a **train** y se
    sustituyeron por noticias de la misma categoría. No se movieron noticias de validación/test.
    Se mantienen 70/15/15 noticias por categoría, y las 40 del baseline inicial siguen en validación.
    Las copias anteriores a la auditoría permiten verificar el sorteo original exactamente.
""")
code("""
    original = pd.read_csv('datos/noticias_antes_auditoria.csv')
    initial_train, holdout = train_test_split(original.index, test_size=0.30,
                                             stratify=original.etiqueta, random_state=42)
    initial_val, initial_test = train_test_split(holdout, test_size=0.50,
                                                stratify=original.loc[holdout, 'etiqueta'], random_state=42)
    assert set(original.loc[initial_val, 'url']) == set(data.query("particion == 'validacion'").url)
    assert set(original.loc[initial_test, 'url']) == set(data.query("particion == 'test'").url)
    corrections = pd.read_csv('datos/correcciones_auditoria.csv')
    train_urls = set(original.loc[initial_train, 'url']) - set(corrections.url_descartada) | set(corrections.url_reemplazo)
    assert train_urls == set(data.query("particion == 'train'").url)
    display(corrections[['caso', 'particion', 'titular_descartado', 'titular_reemplazo']])
    display(data.groupby(['particion', 'etiqueta']).size().unstack('etiqueta'))
    sample_original = original[original.index.isin(set(initial_train) | set(initial_val))].sample(20, random_state=42)
    assert set(sample_original.url) == set(audit.url), 'La auditoría debe conservar su muestra aleatoria original'
    display(pd.Series(read_json('particiones.json'), name='valor').to_frame())
""")
md("""
    ## 4. Fine-tuning real con Hugging Face Trainer

    DistilBERT multilingüe recibe las **etiquetas LLM de train**. Validación utiliza las etiquetas de
    sección independientes. Tres épocas, batch 8, longitud máxima 128, learning rate 2e-5, semilla 42,
    evaluación y guardado por época; el mejor checkpoint se elige por **F1 macro de validación**.
    Se usó GPU NVIDIA RTX 3050 de 4 GB, FP16 y gradient checkpointing. El código también admite CPU.

    El entrenamiento se ejecutó y guardó modelo/tokenizador en `modelo/`. Sus pesos grandes quedan
    excluidos de Git. `REENTRENAR` es False para conservar el experimento cerrado y sus resultados;
    en una copia nueva puede repetirse con los CSV entregados, sin volver a generar etiquetas LLM.
    Cambiar decisiones después de observar test requeriría un nuevo conjunto de evaluación.
""")
code("""
    REENTRENAR = False
    if REENTRENAR:
        from src.modelado import train
        train()
    training = read_json('entrenamiento.json')
    display(pd.Series({k: training[k] for k in ['modelo_base', 'revision', 'semilla', 'epocas',
            'batch', 'max_length', 'learning_rate', 'mejor_f1_validacion', 'segundos', 'device',
            'etiqueta_train', 'etiqueta_validacion']}, name='valor').to_frame())
    history = pd.DataFrame(training['historial'])
    epochs = history[history.eval_f1_macro.notna()][['epoch', 'eval_loss', 'eval_accuracy', 'eval_f1_macro']]
    display(epochs)
    assert training['epocas'] == 3 and training['batch'] == 8 and len(epochs) == 3
    assert np.isclose(epochs.eval_f1_macro.max(), training['mejor_f1_validacion'])
    config = json.loads(Path('modelo/config.json').read_text(encoding='utf-8'))
    display(pd.Series(config['id2label'], name='categoria').to_frame())
    print('Pesos locales disponibles:', Path('modelo/model.safetensors').exists())
    print('Una copia nueva puede regenerarlos con: python src/modelado.py --paso entrenar')
""")
md("""
    ## 5. Evaluación final en las 60 noticias de test

    Las decisiones se cerraron antes de abrir test. Las predicciones se obtuvieron con los modelos
    reales, sin entrenar ni escoger checkpoint usando test. Se recalculan accuracy, F1 macro y
    matriz de confusión a partir de `predicciones_test.csv`. La referencia es la sección del diario,
    no una etiqueta humana exhaustiva ni la etiqueta producida por el LLM.
""")
code("""
    test = pd.read_csv('resultados/predicciones_test.csv', keep_default_na=False)
    final = read_json('evaluacion_test.json')
    assert len(test) == 60 and set(test.url) == set(data.query("particion == 'test'").url)
    assert not set(test.url).intersection(data.query("particion == 'train'").url)
    fine_metrics = metrics(test.etiqueta, test.transformer)
    display(pd.DataFrame([{'metodo': 'Transformer fine-tuned', **fine_metrics, 'n_test': len(test)}]))
    assert np.isclose(fine_metrics['f1_macro'], final['transformer']['f1_macro'])
    report = pd.DataFrame(classification_report(test.etiqueta, test.transformer, labels=LABELS,
                                               output_dict=True, zero_division=0)).T
    display(report)
    cm = confusion_matrix(test.etiqueta, test.transformer, labels=LABELS)
    fig, ax = plt.subplots(figsize=(8, 5.8))
    names = ['Política', 'Economía', 'Deportes', 'Ciencia / tecnología']
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=names, yticklabels=names, ax=ax, cbar=False)
    ax.set(title='Economía concentra cuatro confusiones hacia política en test',
           xlabel='Categoría predicha', ylabel='Sección de referencia')
    plt.xticks(rotation=20, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()
    errors = test[test.etiqueta != test.transformer]
    display(errors[['titular', 'etiqueta', 'transformer']])
""")
md("""
    ### Reflexión por categoría

    - **Deportes:** mejor F1 (0,889), con 12/15 aciertos. Tres errores pasan a política: declaraciones
      de entrenadores/personajes y una reflexión sobre Alejandro Olmedo contienen nombres y citas
      que pueden parecer discurso político, sin una competición como núcleo explícito.
    - **Economía:** menor F1 (0,733). Cuatro titulares pasan a política: AFP, gasto de Defensa,
      feriados y un decreto sobre tercerización. Las decisiones de autoridades mezclan el lenguaje
      económico con el institucional, como también ocurrió en la revisión humana.
    - **Política:** recupera las 15 noticias (recall 1,00), pero recibe siete falsos positivos;
      su precisión baja a 0,682. El clasificador tiende a asignar política a titulares con autoridades,
      declaraciones o medidas estatales aunque la sección de origen sea otra.
    - **Ciencia/tecnología:** F1 0,846; cuatro errores hacia economía incluyen Cyber Wow, billeteras
      digitales, almacenamiento sin gastar y una demostración empresarial de 5G. Los textos de
      consumo tecnológico comparten vocabulario de dinero y empresas con economía.

    Son interpretaciones de los errores observados, no causas demostradas. Hay solo 15 casos por
    categoría y posible ruido editorial: este test no acredita el mismo desempeño en otros medios.
""")
md("""
    ## 6. Comparación sobre el mismo test y decisión de uso

    El baseline de 40 se reporta por separado para cumplir el diagnóstico inicial. Para comparar
    métodos se usa aquí el mismo test de 60 titulares y la misma referencia de sección.
""")
code("""
    comparison = pd.DataFrame([{'metodo': name, 'n_test': len(test), **metrics(test.etiqueta, test[column])}
                   for name, column in [('zero_shot', 'zero_shot'), ('llm', 'etiqueta_llm'), ('transformer', 'transformer')]])
    display(comparison)
    print('Latencia GPU de inferencia, excluye carga del modelo:')
    display(pd.DataFrame([
        {'metodo': 'zero_shot', 'ms_por_titular': 1000 * final['latencia_zero_shot_s_por_titular']},
        {'metodo': 'transformer', 'ms_por_titular': 1000 * final['latencia_transformer_s_por_titular']}]))
    print(f"Entrega: F1 Macro: {fine_metrics['f1_macro']:.4f} | Zero-shot (40 validación): {base_metrics['f1_macro']:.4f} | Acuerdo LLM-Humano: 13/20")
""")
md("""
    **Decisión:** la app usa el Transformer ajustado: obtuvo F1 macro 0,820 frente a 0,792 del
    zero-shot y 0,761 del LLM en este test, y realizó la inferencia GPU en unos 7,1 ms por titular
    frente a 15,7 ms del zero-shot. Estas mediciones son por lotes, excluyen carga y no equivalen
    a la latencia de una solicitud web en CPU. La app ejecuta el modelo en CPU para facilitar su uso.

    Qwen local evita pagos por API y genera supervisión, pero tiene 1,5 mil millones de parámetros
    y decodifica texto: requiere más memoria y trabajo por consulta. DistilBERT reutiliza ese
    esfuerzo en un clasificador de cuatro salidas. La diferencia de F1 en solo 60 casos es pequeña;
    no se afirma significancia estadística. Para producción convendría ampliar la evaluación humana,
    revisar la frontera política/economía y calibrar probabilidades con un conjunto independiente.

    **Reproducción:** las revisiones de los tres modelos, prompts, particiones, respuestas crudas,
    configuración, registros de entrenamiento y predicciones están versionados. Los pesos se
    regeneran con `python src/modelado.py --paso entrenar`; el README detalla la secuencia completa.
""")

notebook = nbf.v4.new_notebook(cells=cells)
notebook.metadata.kernelspec = {'display_name': 'Python — Tarea 1', 'language': 'python', 'name': 'python3'}
notebook.metadata.language_info = {'name': 'python'}
nbf.write(notebook, ROOT / '02_clasificacion.ipynb')
print(ROOT / '02_clasificacion.ipynb')
