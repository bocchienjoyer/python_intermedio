"""Genera el gráfico de inflación interanual de Lima Metropolitana para 2024."""

import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "mcp"))

from server import serie


def main():
    consulta = serie("PN01273PM", "2024-01", "2024-12")
    datos = consulta["datos"]
    fechas = [date.fromisoformat(f"{fila['periodo']}-01") for fila in datos]
    valores = [fila["valor"] for fila in datos]
    fig, ax = plt.subplots(figsize=(9, 4.8), layout="constrained")
    fig.suptitle("Inflación interanual de Lima Metropolitana en 2024", fontsize=16, weight="bold")
    ax.plot(fechas, valores, marker="o", color="#2563A6", linewidth=2)
    ax.set_xticks(fechas, "Ene Feb Mar Abr May Jun Jul Ago Set Oct Nov Dic".split())
    ax.set_ylabel("Variación en 12 meses")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=1))
    ax.grid(axis="y", alpha=0.25)
    ax.set_xlabel("Fuente: BCRP, serie PN01273PM", loc="left", labelpad=12)
    salida = RAIZ / "figuras" / "inflacion_lima_2024.png"
    salida.parent.mkdir(exist_ok=True)
    fig.savefig(salida, dpi=180)
    plt.close(fig)
    print(f"{salida.relative_to(RAIZ)} · {consulta['fuente']}")


if __name__ == "__main__":
    main()
