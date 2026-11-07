"""Gráficos ponderados de pobreza por área, sexo o edad: ENAHO 2024."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "scripts"))
from enaho_comun import agrupar_pobreza, cargar_base_validada, exigir, guardar_json, iniciar_graficos, porcentaje

TITULOS = {"area": "área de residencia", "sexo": "sexo", "edad": "grupo de edad", "departamento": "departamento"}
EDADES = ["0–17 años", "18–29 años", "30–44 años", "45–59 años", "60 años o más"]


def crear_grupos(base: pd.DataFrame, por: str) -> pd.Series:
    if por == "area":
        return base.urbano.map({True: "Urbana", False: "Rural"})
    if por == "sexo":
        return base.p207.map({1: "Hombres", 2: "Mujeres"})
    if por == "departamento":
        return base.departamento
    exigir(por == "edad", "Comparación no implementada; usar area, sexo o edad")
    return pd.cut(base.p208a, bins=[-1, 17, 29, 44, 59, 120], labels=EDADES).astype("string")


def dibujar(tabla: pd.DataFrame, por: str, anio: int, raiz: Path):
    plt = iniciar_graficos(raiz)
    from matplotlib.ticker import PercentFormatter

    with plt.rc_context({"font.family": "DejaVu Sans", "text.color": "#0F172A", "axes.labelcolor": "#475569"}):
        fig, ax = plt.subplots(figsize=(9.6, max(5.6, 0.43 * len(tabla) + 2.6)))
        fig.subplots_adjust(left=0.21, right=0.93, top=0.73, bottom=0.23)
        fig.text(0.07, 0.91, f"Pobreza monetaria por {TITULOS[por]}", fontsize=20, weight="bold", ha="left")
        fig.text(0.07, 0.85, f"Perú · {anio} · residentes habituales", fontsize=12, color="#475569")
        barras = ax.barh(tabla.grupo, tabla.pobreza_pct, color="#2563A6", height=0.52)
        ax.invert_yaxis()
        ax.set_xlim(0, min(110, max(10, math.ceil(float(tabla.pobreza_pct.max()) / 10) * 10 + 10)))
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.set_xlabel("Porcentaje de personas", labelpad=12)
        ax.set_axisbelow(True)
        ax.xaxis.grid(True, color="#E2E8F0", linewidth=0.8)
        ax.tick_params(axis="both", length=0, labelsize=11, pad=9)
        for borde in ax.spines.values():
            borde.set_visible(False)
        ax.bar_label(barras, labels=[porcentaje(v) for v in tabla.pobreza_pct], padding=9, fontsize=13, weight="bold", color="#0F172A")
        fig.text(0.07, 0.09, "Fuente: INEI, ENAHO 2024", fontsize=10, weight="bold")
        fig.text(0.07, 0.045, "Estimación con la base de personas · factor de expansión: facpob07", fontsize=9, color="#64748B")
    return fig


def ejecutar(raiz: Path, anio: int, por: str) -> pd.DataFrame:
    base, informe = cargar_base_validada(raiz, anio)
    tabla = agrupar_pobreza(base, crear_grupos(base, por)).sort_values(["pobreza_pct", "grupo"], ascending=[False, True], ignore_index=True)
    if por == "departamento":
        referencia = pd.read_csv(raiz / f"referencias/pobreza_departamento_{anio}.csv",
                                 dtype={"ccdd": "string"}).set_index("ccdd")
        nombres = tabla.grupo.map(referencia.departamento.str.title())
        exigir(nombres.notna().all(), "Hay departamentos sin nombre en la referencia")
        tabla = tabla.rename(columns={"grupo": "codigo_departamento"}).assign(grupo=nombres)
    salida = raiz / "figuras"
    salida.mkdir(parents=True, exist_ok=True)
    nombre = f"pobreza_{por}_{anio}"
    fig = dibujar(tabla, por, anio, raiz)
    try:
        fig.savefig(salida / f"{nombre}.png", dpi=200, facecolor="white")
    finally:
        iniciar_graficos(raiz).close(fig)
    tabla.to_csv(salida / f"{nombre}.csv", index=False, encoding="utf-8")
    guardar_json(salida / f"{nombre}.json", {
        "anio": anio, "por": por, "universo": "residentes habituales", "peso": "facpob07",
        "base_sha256": informe["base"]["sha256"], "dpi": 200,
        "orden": "pobreza de mayor a menor", "inicio_eje": 0,
        "grupos_edad": EDADES if por == "edad" else None,
    })
    return tabla


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio", type=int, choices=[2024], required=True)
    parser.add_argument("--por", choices=list(TITULOS), default="area")
    args = parser.parse_args()
    try:
        tabla = ejecutar(RAIZ, args.anio, args.por)
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: figuras/pobreza_{args.por}_{args.anio}.png; peso facpob07")
    for fila in tabla.itertuples():
        print(f"  {fila.grupo}: {porcentaje(fila.pobreza_pct)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
