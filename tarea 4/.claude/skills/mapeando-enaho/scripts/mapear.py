"""Mapa de pobreza de personas en los 25 departamentos: ENAHO 2024."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "scripts"))
from enaho_comun import agrupar_pobreza, cargar_base_validada, exigir, guardar_json, huella, iniciar_graficos, porcentaje

CODIGOS = {f"{i:02d}" for i in range(1, 26)}


def validar_codigos(serie: pd.Series, nombre: str) -> pd.Series:
    codigos = serie.astype("string")
    exigir(codigos.str.fullmatch(r"[0-9]{2}").fillna(False).all(), f"{nombre}: códigos sin dos caracteres o faltantes")
    exigir(len(codigos) == 25 and codigos.is_unique and set(codigos) == CODIGOS, f"{nombre}: se requieren los 25 códigos únicos, incluidos Lima 15 y Callao 07")
    return codigos


def unir_departamentos(geografia: gpd.GeoDataFrame, tasas: pd.DataFrame) -> gpd.GeoDataFrame:
    exigir({"FIRST_IDDP", "NOMBDEP", "geometry"}.issubset(geografia.columns), "El GeoJSON no contiene los campos requeridos")
    exigir({"departamento", "pobreza_pct"}.issubset(tasas.columns), "La tabla no contiene código y tasa de pobreza")
    geografia = geografia.copy()
    tasas = tasas.copy()
    geografia["FIRST_IDDP"] = validar_codigos(geografia.FIRST_IDDP, "GeoJSON")
    tasas["departamento"] = validar_codigos(tasas.departamento, "Tasas")
    exigir(geografia.crs is not None, "El GeoJSON no declara su sistema de coordenadas")
    exigir(geografia.geometry.notna().all() and (~geografia.geometry.is_empty).all() and geografia.is_valid.all(), "Hay geometrías faltantes, vacías o inválidas")
    exigir(tasas.pobreza_pct.between(0, 100).fillna(False).all(), "Tasas faltantes o fuera de 0–100 %")
    mapa = geografia.merge(tasas, how="left", left_on="FIRST_IDDP", right_on="departamento", validate="1:1", indicator=True)
    exigir(mapa._merge.eq("both").all() and mapa.pobreza_pct.notna().all(), "La unión dejó departamentos sin dato")
    return mapa.drop(columns="_merge").sort_values("departamento", ignore_index=True)


def nombre_legible(nombre: str) -> str:
    nombre = str(nombre).title()
    return {"Ancash": "Áncash", "Apurimac": "Apurímac", "Huanuco": "Huánuco", "Junin": "Junín", "San Martin": "San Martín", "Madre De Dios": "Madre de Dios"}.get(nombre, nombre)


def incorporar_referencia(tabla: pd.DataFrame, ruta: Path) -> pd.DataFrame:
    referencia = pd.read_csv(ruta, dtype={"ccdd": "string"})
    exigir({"ccdd", "pobreza_pct"}.issubset(referencia.columns), "Referencia departamental sin código o tasa")
    referencia["ccdd"] = validar_codigos(referencia.ccdd, "Referencia de sumaria")
    exigir(referencia.pobreza_pct.between(0, 100).fillna(False).all(), "Referencia de sumaria inválida")
    referencia = referencia[["ccdd", "pobreza_pct"]].rename(columns={"ccdd": "departamento", "pobreza_pct": "referencia_sumaria_pct"})
    tabla = tabla.merge(referencia, on="departamento", how="left", validate="1:1")
    exigir(tabla.referencia_sumaria_pct.notna().all(), "Referencia incompleta tras unir por código")
    tabla["diferencia_pp"] = tabla.pobreza_pct - tabla.referencia_sumaria_pct
    return tabla


def dibujar(mapa: gpd.GeoDataFrame, anio: int, raiz: Path):
    plt = iniciar_graficos(raiz)
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable

    mapa = mapa.to_crs(4326)
    vmax = max(10, math.ceil(float(mapa.pobreza_pct.max()) / 10) * 10)
    normalizacion = Normalize(vmin=0, vmax=vmax)
    with plt.rc_context({"font.family": "DejaVu Sans", "text.color": "#0F172A"}):
        fig = plt.figure(figsize=(12, 10), facecolor="white")
        fig.text(0.06, 0.95, "Pobreza monetaria por departamento", fontsize=24, weight="bold")
        fig.text(0.06, 0.91, f"Perú · {anio} · residentes habituales · 25 departamentos con dato", fontsize=12, color="#475569")
        ax = fig.add_axes([0.035, 0.175, 0.62, 0.69])
        mapa.plot(column="pobreza_pct", cmap="Blues", vmin=0, vmax=vmax, edgecolor="white", linewidth=0.75, ax=ax)
        ax.set_axis_off()
        for codigo in ["06", "16", "21", "11"]:
            fila = mapa.loc[mapa.departamento.eq(codigo)].iloc[0]
            punto = fila.geometry.representative_point()
            ax.text(punto.x, punto.y, f"{nombre_legible(fila.NOMBDEP)}\n{porcentaje(fila.pobreza_pct)}", fontsize=9.2, weight="bold", ha="center", va="center", color="#0F172A", bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.9})
        ax.annotate("N", xy=(0.1, 0.99), xytext=(0.1, 0.90), xycoords="axes fraction", ha="center", color="#475569", fontsize=10, arrowprops={"arrowstyle": "->", "color": "#475569", "lw": 1.1})

        panel = fig.add_axes([0.70, 0.52, 0.25, 0.32])
        panel.set_axis_off()
        orden = mapa.sort_values("pobreza_pct", ascending=False)
        panel.text(0, 0.96, "MAYOR POBREZA", fontsize=10, color="#64748B", weight="bold")
        for y, fila in zip([0.83, 0.71, 0.59], orden.head(3).itertuples()):
            panel.text(0, y, nombre_legible(fila.NOMBDEP), fontsize=12)
            panel.text(1, y, porcentaje(fila.pobreza_pct), ha="right", fontsize=12, weight="bold")
        panel.text(0, 0.38, "MENOR POBREZA", fontsize=10, color="#64748B", weight="bold")
        for y, fila in zip([0.25, 0.13, 0.01], orden.tail(3).sort_values("pobreza_pct").itertuples()):
            panel.text(0, y, nombre_legible(fila.NOMBDEP), fontsize=12)
            panel.text(1, y, porcentaje(fila.pobreza_pct), ha="right", fontsize=12, weight="bold")

        detalle = mapa.loc[mapa.departamento.isin(["07", "15"])]
        inset = fig.add_axes([0.72, 0.235, 0.23, 0.22], facecolor="#F8FAFC")
        detalle.plot(column="pobreza_pct", cmap="Blues", vmin=0, vmax=vmax, edgecolor="#334155", linewidth=0.8, ax=inset)
        callao = mapa.loc[mapa.departamento.eq("07")].iloc[0]
        x0, y0, x1, y1 = callao.geometry.bounds
        inset.set_xlim(x0 - 0.07, x1 + 0.10)
        inset.set_ylim(y0 - 0.07, y1 + 0.07)
        punto = callao.geometry.representative_point()
        inset.annotate("Callao", xy=(punto.x, punto.y), xytext=(0.58, 0.18), textcoords="axes fraction", fontsize=10, color="#0F172A", arrowprops={"arrowstyle": "-", "color": "#0F172A"}, bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 2})
        inset.text(0.77, 0.78, "Lima", transform=inset.transAxes, fontsize=10, ha="center", color="#0F172A", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 2})
        inset.set_xticks([])
        inset.set_yticks([])
        inset.set_xlabel("")
        inset.set_ylabel("")
        inset.set_title("Detalle: Lima y Callao", loc="left", fontsize=11, weight="bold", pad=12)
        for borde in inset.spines.values():
            borde.set_edgecolor("#CBD5E1")
        lima = mapa.loc[mapa.departamento.eq("15")].iloc[0]
        fig.text(0.70, 0.195, f"Lima {porcentaje(lima.pobreza_pct)} · Callao {porcentaje(callao.pobreza_pct)}", fontsize=10, color="#475569")

        cax = fig.add_axes([0.14, 0.13, 0.43, 0.018])
        colorbar = fig.colorbar(ScalarMappable(norm=normalizacion, cmap="Blues"), cax=cax, orientation="horizontal")
        colorbar.set_label("% de personas", fontsize=10, labelpad=6)
        colorbar.outline.set_visible(False)
        colorbar.ax.tick_params(labelsize=9, length=0, pad=5)
        fig.text(0.06, 0.054, "Fuente: INEI, ENAHO 2024", fontsize=10, weight="bold")
        fig.text(0.06, 0.028, "Peso: facpob07 · Límites departamentales: material del curso · Lima y Callao se estiman por separado", fontsize=9, color="#64748B")
    return fig, vmax


def ejecutar(raiz: Path, anio: int) -> pd.DataFrame:
    base, informe = cargar_base_validada(raiz, anio)
    ruta_geo = raiz / "datos/peru_departamental_simple.geojson"
    if not ruta_geo.is_file():
        raise FileNotFoundError("Falta datos/peru_departamental_simple.geojson; consulta el README")
    tasas = agrupar_pobreza(base, base.departamento).rename(columns={"grupo": "departamento"})
    mapa = unir_departamentos(gpd.read_file(ruta_geo), tasas)
    tabla = mapa[["departamento", "NOMBDEP", "n_personas", "poblacion_expandida", "poblacion_pobre", "pobreza_pct"]].copy()
    tabla = tabla.rename(columns={"NOMBDEP": "nombre_departamento"})
    tabla["nombre_departamento"] = tabla.nombre_departamento.map(nombre_legible)
    referencia = raiz / f"referencias/pobreza_departamento_{anio}.csv"
    if referencia.is_file():
        tabla = incorporar_referencia(tabla, referencia)
    salida = raiz / "mapas"
    salida.mkdir(parents=True, exist_ok=True)
    fig, vmax = dibujar(mapa, anio, raiz)
    try:
        fig.savefig(salida / "pobreza_departamento.png", dpi=200, facecolor="white")
    finally:
        iniciar_graficos(raiz).close(fig)
    tabla.to_csv(salida / "pobreza_departamento.csv", index=False, encoding="utf-8")
    guardar_json(salida / "pobreza_departamento.json", {
        "anio": anio, "universo": "residentes habituales", "peso": "facpob07",
        "base_sha256": informe["base"]["sha256"], "geojson_sha256": huella(ruta_geo),
        "referencia_sumaria_sha256": huella(referencia),
        "union": "departamento = ubigeo[:2] con FIRST_IDDP; 1:1",
        "departamentos": len(mapa), "sin_dato": int(mapa.pobreza_pct.isna().sum()),
        "lima_callao_separados": True, "paleta": "Blues", "vmin": 0, "vmax": vmax, "dpi": 200,
    })
    return tabla


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio", type=int, choices=[2024], required=True)
    args = parser.parse_args()
    try:
        tabla = ejecutar(RAIZ, args.anio)
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: mapas/pobreza_departamento.png; 25 departamentos; peso facpob07")
    for fila in tabla.sort_values("pobreza_pct", ascending=False).itertuples():
        print(f"  {fila.departamento} {fila.nombre_departamento}: {porcentaje(fila.pobreza_pct)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
