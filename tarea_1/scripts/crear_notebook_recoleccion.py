"""Construye el notebook de recolección a partir de resultados reales."""

import json
from pathlib import Path
import textwrap

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
summary = json.loads((ROOT / "datos/resumen_recoleccion.json").read_text(encoding="utf-8"))
cells = []


def md(value):
    cells.append(nbf.v4.new_markdown_cell(textwrap.dedent(value).strip()))


def code(value):
    cells.append(nbf.v4.new_code_cell(textwrap.dedent(value).strip()))


md(f"""
    # ¿Cómo se distribuyen los titulares de La República entre cuatro temas?

    **Fecha de descarga:** {summary['fecha_descarga']}. **Opción A:** La República.

    **URLs base:** https://larepublica.pe/robots.txt, https://larepublica.pe/rss/politica.xml,
    https://larepublica.pe/rss/economia.xml, https://larepublica.pe/rss/deportes.xml,
    https://larepublica.pe/rss/ciencia.xml; sitemaps y secciones públicas de política, economía,
    deportes, ciencia y tecnología. Los enlaces relacionados del propio medio amplían el período.

    Meta: 400 noticias reales (~100 por categoría). La muestra tiene cuotas y depende de los enlaces
    accesibles: no estima la proporción natural de temas publicada por el periódico.
""")
md("""
    ## 1. Configuración y reproducción

    El recolector en `src/recoleccion.py` consulta `robots.txt` con Protego (incluye comodines),
    identifica su User-Agent, hace solicitudes secuenciales con pausas de 1,5–2 segundos,
    como máximo un reintento y guarda XML/HTML y metadatos en `datos/raw/`.
    No usa páginas restringidas de archivo ni construye rutas de paginación.

    `RECOLECTAR = False` permite analizar el CSV entregado sin volver a consultar el sitio.
    Cambiarlo a `True` ejecuta la recolección; la caché evita descargar otra vez las mismas URLs.
    Para una nueva fecha de extracción usar una carpeta de datos nueva y conservar la anterior.
""")
code("""
    from pathlib import Path
    import json
    import os
    import platform
    import pandas as pd
    import plotly.express as px
    import plotly.io as pio
    from IPython.display import display
    from src.recoleccion import collect, COLUMNS, CATEGORIES, SECTION_MAP, section_key

    ROOT = Path.cwd()
    assert (ROOT / 'datos').exists(), 'Ejecutar el notebook desde tarea_1/'
    # Edge permite que Kaleido genere una imagen junto a la figura interactiva.
    edge = Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe'
    if edge.exists():
        os.environ.setdefault('BROWSER_PATH', str(edge))
    pio.renderers.default = 'plotly_mimetype+png'
    pio.templates.default = 'plotly_white'
    print('Python:', platform.python_version())
    RECOLECTAR = False
    if RECOLECTAR:
        df, resumen = collect(per_category=100)
    else:
        df = pd.read_csv(ROOT / 'datos/noticias.csv', keep_default_na=False)
        resumen = json.loads((ROOT / 'datos/resumen_recoleccion.json').read_text(encoding='utf-8'))
    display(pd.DataFrame({'indicador': ['Noticias finales', 'Enlaces candidatos únicos', 'URLs finales con HTTP 200'],
                          'valor': [len(df), resumen['candidatos_unicos'], resumen['url_verificadas_http_200']]}))
    display(pd.DataFrame(list(resumen['fuentes'].items()), columns=['fuente', 'entradas_descubiertas']))
""")
md("""
    ## 2. Limpieza, equivalencias y descartes

    La categoría de referencia procede de la sección de origen. Ciencia y tecnología se agrupan
    en `ciencia_tecnologia`; no se crea una quinta clase. Se conserva el nombre original de sección.
    La tabla incluye la ruta para desambiguar nombres de subsección que podrían repetirse.

    Se eliminan URLs repetidas durante el descubrimiento y titulares vacíos, duplicados o casi
    idénticos (similitud de caracteres ≥ 0,95). La bajada procede de RSS o metadatos HTML, nunca
    de generación artificial. Los errores y descartes se guardan con motivo; los candidatos que no
    se descargan porque la cuota ya está completa no se presentan como noticias recolectadas.
""")
code("""
    mapeo = pd.read_csv('datos/mapeo_secciones.csv', keep_default_na=False)
    display(mapeo)
    print('Regla explícita por ruta:', SECTION_MAP)
    descartes = pd.read_csv('datos/descartes.csv', keep_default_na=False)
    descubrimiento = pd.read_csv('datos/descartes_descubrimiento.csv', keep_default_na=False)
    print('Descartes durante extracción:', len(descartes))
    display(descartes.groupby('motivo').size().rename('cantidad').reset_index())
    print('Duplicados/fuera de alcance detectados en descubrimiento:', len(descubrimiento))
    display(descubrimiento.groupby('motivo').size().rename('cantidad').reset_index())
    controles = pd.DataFrame({
        'control': ['Siete columnas exactas', '350 o más noticias', 'Cuatro categorías oficiales',
                    'Sin URLs duplicadas', 'Sin titulares vacíos', 'Sin bajadas vacías', 'Mapeo consistente con ruta'],
        'cumple': [list(df.columns) == COLUMNS, len(df) >= 350, set(df.etiqueta) == set(CATEGORIES),
                   not df.url.duplicated().any(), df.titular.str.strip().ne('').all(),
                   df.bajada.str.strip().ne('').all(),
                   df.apply(lambda r: SECTION_MAP.get(section_key(r.url)) == r.etiqueta, axis=1).all()]})
    display(controles)
    assert controles.cumple.all(), 'Revisar controles fallidos antes de modelar'
""")
md("""
    ## 3. Análisis exploratorio con Plotly Express

    Las figuras conservan su salida interactiva y una imagen estática para la lectura en GitHub.
    Los títulos se calculan a partir de los datos. La distribución por categoría refleja una decisión
    de muestreo por cuotas, no una conclusión sobre la agenda editorial del medio.
""")
code("""
    por_categoria = df.etiqueta.value_counts().reindex(CATEGORIES).rename_axis('categoria').reset_index(name='noticias')
    titulo = ('Las cuatro categorías aportan ' + str(int(por_categoria.noticias.iloc[0])) + ' noticias cada una'
              if por_categoria.noticias.nunique() == 1 else 'La muestra tiene diferencias de tamaño entre categorías')
    fig = px.bar(por_categoria, x='categoria', y='noticias', color='categoria',
                 title=titulo, text_auto=True, labels={'categoria': 'Categoría', 'noticias': 'Noticias'})
    fig.update_layout(showlegend=False)
    fig.show()
""")
code("""
    por_fecha = df.groupby('fecha').size().rename('noticias').reset_index().sort_values('fecha')
    pico = por_fecha.loc[por_fecha.noticias.idxmax()]
    fig = px.bar(por_fecha, x='fecha', y='noticias',
                 title=f"El {pico['fecha']} concentra {int(pico['noticias'])} de {len(df)} titulares de la muestra",
                 labels={'fecha': 'Fecha de publicación (Perú)', 'noticias': 'Noticias'})
    fig.show()
    print('Período de publicación:', df.fecha.min(), 'a', df.fecha.max())
""")
code("""
    longitud = df.titular.str.len()
    fig = px.histogram(x=longitud, nbins=25,
                       title=f'La mitad de los titulares tiene hasta {longitud.median():.0f} caracteres',
                       labels={'x': 'Caracteres del titular', 'y': 'Cantidad de noticias'})
    fig.update_layout(yaxis_title='Cantidad de noticias')
    fig.show()
    display(longitud.describe().rename('caracteres').to_frame())
""")
md("""
    ## 4. Validación de los extremos

    Los ejemplos permiten comprobar si los valores extremos del histograma son titulares reales
    y no errores de extracción. Se muestran sus enlaces y longitudes exactas.
""")
code("""
    extremos = df.assign(caracteres=df.titular.str.len())
    print('Cinco titulares más cortos:')
    display(extremos.nsmallest(5, 'caracteres')[['titular', 'caracteres', 'etiqueta', 'url']])
    print('Cinco titulares más largos:')
    display(extremos.nlargest(5, 'caracteres')[['titular', 'caracteres', 'etiqueta', 'url']])
""")
md("""
    ## 5. Exportación y límites

    Se entregan exactamente las siete columnas requeridas. El archivo de candidatos, el registro
    de solicitudes y las tablas de limpieza conservan la trazabilidad fuera del CSV principal.

    Limitaciones: muestreo por cuotas/enlaces accesibles, un solo medio y etiquetas editoriales
    que pueden mezclar asuntos políticos y económicos. Las fechas y tamaños de las categorías
    dependen de la disponibilidad del sitio durante la descarga. Un enlace con HTTP 200 se
    verificó al recolectar; su disponibilidad futura puede cambiar.
""")
code("""
    df[COLUMNS].to_csv('datos/noticias.csv', index=False, encoding='utf-8')
    print('df.shape =', df.shape)
    display(df.head(5))
""")

notebook = nbf.v4.new_notebook(cells=cells)
notebook.metadata.kernelspec = {"display_name": "Python — Tarea 1", "language": "python", "name": "python3"}
notebook.metadata.language_info = {"name": "python"}
nbf.write(notebook, ROOT / "01_recoleccion.ipynb")
print(ROOT / "01_recoleccion.ipynb")
