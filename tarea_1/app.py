"""Exploración de noticias y clasificación de titulares con el modelo entrenado."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
LABEL_NAMES = {"politica": "Política", "economia": "Economía", "deportes": "Deportes",
               "ciencia_tecnologia": "Ciencia y tecnología"}
COLORS = {"Política": "#496E8D", "Economía": "#708A66", "Deportes": "#C69C5C", "Ciencia y tecnología": "#9177A6"}

st.set_page_config(page_title="Del titular al tema | La República", page_icon="📰", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1200px; padding-top: 2.6rem;}
h1 {font-family: Georgia, serif; letter-spacing: -1.2px; text-align: center;}
[data-testid="stMetric"] {background: rgba(128,128,128,.12); border: 1px solid rgba(128,128,128,.20); border-radius: 10px; padding: 18px;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def read_news(modified):
    return pd.read_csv(ROOT / "datos/noticias.csv", keep_default_na=False)


def read_json(name):
    path = ROOT / "resultados" / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


@st.cache_resource
def load_classifier(modified):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(ROOT / "modelo", local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(ROOT / "modelo", local_files_only=True, use_safetensors=True)
    model.to("cpu").eval()
    torch.set_num_threads(4)
    return tokenizer, model


st.caption("PYTHON INTERMEDIO · TAREA 1 · LA REPÚBLICA")
st.title("¿Qué nos cuenta un titular?")
st.write("Explora noticias de La República y prueba un clasificador que distingue política, economía, deportes y ciencia o tecnología.")

data_path = ROOT / "datos/noticias.csv"
if not data_path.exists():
    st.info("La recolección está en preparación. Las noticias aparecerán al completar esta etapa.")
    st.stop()
data = read_news(data_path.stat().st_mtime_ns)
final = read_json("evaluacion_test.json")
audit = read_json("auditoria.json")
summary_path = ROOT / "datos/resumen_recoleccion.json"
summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}

st.sidebar.header("Explorar la muestra")
media = st.sidebar.multiselect("Medio", sorted(data.medio.unique()), default=sorted(data.medio.unique()))
categories = st.sidebar.multiselect("Categorías", list(LABEL_NAMES), default=list(LABEL_NAMES), format_func=LABEL_NAMES.get)
filtered = data[data.medio.isin(media) & data.etiqueta.isin(categories)].copy()
st.sidebar.caption(f"{len(filtered)} de {len(data)} noticias seleccionadas")
st.sidebar.caption("La muestra se construyó con cuotas por tema; su equilibrio no representa la frecuencia natural de publicación del diario.")

col1, col2, col3 = st.columns(3)
col1.metric("Noticias recolectadas", f"{len(data):,}")
f1 = final.get("transformer", {}).get("f1_macro")
col2.metric("F1 macro · test reservado", f"{f1:.3f}" if f1 is not None else "Pendiente")
agreement = audit.get("porcentaje") if audit.get("estado") == "completa" else None
col3.metric("Acuerdo LLM–humano · 20 casos", f"{agreement:.0f}%" if agreement is not None else "Pendiente")

explore, classify, methodology = st.tabs(["Noticias", "Probar un titular", "Cómo se hizo"])

with explore:
    st.subheader("Cuatro temas, una muestra para explorar")
    if filtered.empty:
        st.info("Selecciona al menos un medio y una categoría para ver noticias.")
    else:
        counts = filtered.etiqueta.value_counts().rename_axis("codigo").reset_index(name="Noticias")
        counts["Categoría"] = counts.codigo.map(LABEL_NAMES)
        fig = px.bar(counts, x="Categoría", y="Noticias", color="Categoría", text_auto=True,
                     color_discrete_map=COLORS, template="plotly_white",
                     title=f"{len(filtered)} titulares en las categorías seleccionadas")
        fig.update_layout(showlegend=False, margin=dict(l=5, r=5, t=60, b=5), height=350)
        st.plotly_chart(fig, width='stretch')
    table = filtered[["titular", "bajada", "etiqueta", "medio", "fecha", "url"]].copy()
    table.etiqueta = table.etiqueta.map(LABEL_NAMES)
    st.dataframe(table, hide_index=True, width='stretch',
                 column_config={"titular": st.column_config.TextColumn("Titular", width="large"),
                                "bajada": st.column_config.TextColumn("Bajada", width="large"),
                                "etiqueta": "Categoría", "medio": "Medio", "fecha": "Publicación",
                                "url": st.column_config.LinkColumn("Noticia", display_text="Leer")})
    st.download_button("Descargar selección en CSV", filtered.to_csv(index=False).encode("utf-8-sig"),
                       file_name="noticias_seleccionadas.csv", mime="text/csv")

with classify:
    st.subheader("Escribe un titular nuevo")
    st.write("El modelo elige uno de los cuatro temas a partir del titular, sin consultar la sección del diario.")
    headline = st.text_area("Titular", placeholder="Escribe o pega aquí el titular que quieras clasificar", max_chars=2000)
    model_path = ROOT / "modelo/model.safetensors"
    ready = model_path.exists() and (ROOT / "modelo/config.json").exists()
    if not ready:
        st.info("Faltan los pesos del modelo en este equipo. Sigue la sección de entrenamiento del README para activar el probador.")
    if st.button("Clasificar titular", type="primary", disabled=not ready):
        text = headline.strip()
        if not text:
            st.warning("Escribe un titular antes de clasificar.")
        else:
            import torch
            with st.spinner("Leyendo el titular…"):
                tokenizer, model = load_classifier(model_path.stat().st_mtime_ns)
                encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
                with torch.inference_mode():
                    probabilities = model(**encoded).logits.float().softmax(dim=-1)[0]
                index = int(probabilities.argmax())
                label = model.config.id2label[index]
                st.success(LABEL_NAMES.get(label, label))
                st.metric("Probabilidad estimada", f"{float(probabilities[index]):.1%}")
                all_scores = pd.DataFrame({"Categoría": [LABEL_NAMES.get(model.config.id2label[i], model.config.id2label[i]) for i in range(4)],
                                           "Probabilidad": probabilities.tolist()}).sort_values("Probabilidad", ascending=False)
                st.dataframe(all_scores, hide_index=True, width='stretch',
                             column_config={"Probabilidad": st.column_config.ProgressColumn(format="%.3f", min_value=0, max_value=1)})
                st.caption("Probabilidades estimadas entre las cuatro categorías; no se ha realizado calibración de confianza.")

with methodology:
    st.subheader("De noticias reales a un clasificador")
    st.write("La referencia se construye a partir de las secciones del diario. Un LLM genera etiquetas separadas para entrenar un Transformer. La evaluación usa noticias reservadas que no participan en el ajuste del modelo.")
    st.write("Partición estratificada: 70% entrenamiento, 15% validación y 15% test. Semilla: 42. La auditoría consiste en una revisión humana de 20 titulares elegidos al azar fuera del test.")
    st.write("El estudiante descartó dos casos de entrenamiento por quedar fuera de los cuatro temas. Se reemplazaron por noticias de la misma categoría; validación y test conservaron sus titulares originales. Los dos descartes cuentan como desacuerdos en la auditoría.")
    if summary:
        st.caption(f"Publicaciones: {summary.get('fecha_min', '')} a {summary.get('fecha_max', '')} · Descarga: {summary.get('fecha_descarga', '')}")
    st.write("**Alcance:** un solo medio y una muestra por cuotas. Las etiquetas editoriales pueden mezclar temas; el resultado mide acuerdo con esa referencia y puede variar en otros medios o períodos.")
    st.markdown("[Ver el código, los datos y los notebooks](https://github.com/bocchienjoyer/python_intermedio/tree/main/tarea_1)")
