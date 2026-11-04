"""Recalcula las referencias ENAHO de la evaluación desde los ZIP originales."""

from pathlib import Path
from zipfile import ZipFile

import pandas as pd

DATOS = Path(__file__).resolve().parents[1] / "datos"
LLAVES = ["conglome", "vivienda", "hogar"]


def leer(modulo, archivo, columnas):
    with ZipFile(DATOS / f"966-Modulo{modulo}.zip") as zipfile:
        nombre = next(n for n in zipfile.namelist() if Path(n).name.lower() == archivo)
        with zipfile.open(nombre) as flujo:
            return pd.read_stata(flujo, convert_categoricals=False, columns=columnas)


def tasa(tabla, peso):
    return 100 * peso[tabla["pobreza"].isin([1, 2])].sum() / peso.sum()


def main():
    hogar = leer("34", "sumaria-2024.dta", LLAVES + ["pobreza", "factor07", "mieperho"])
    miembros = leer("02", "enaho01-2024-200.dta",
                    LLAVES + ["p204", "p205", "p206", "estrato", "ubigeo", "facpob07"])
    residentes = miembros.query("(p204 == 1 and p205 == 2) or (p204 == 2 and p206 == 1)")
    base = residentes.merge(hogar[LLAVES + ["pobreza"]], on=LLAVES, how="left", validate="m:1")
    assert base.pobreza.isin([1, 2, 3]).all()
    rural = base[base.estrato.ge(6)]
    urbana = base[base.estrato.le(5)]
    departamentos = {
        codigo: tasa(grupo, grupo.facpob07)
        for codigo, grupo in base.groupby(base.ubigeo.str[:2])
    }
    brecha = tasa(rural, rural.facpob07) - tasa(urbana, urbana.facpob07)
    maximo = max(departamentos, key=departamentos.get)
    print("E01", len(residentes))
    print("E02", tasa(hogar, hogar.factor07 * hogar.mieperho))
    print("E03 y componente ENAHO de M01", brecha)
    print("E04", maximo, departamentos[maximo])
    print("Componente ENAHO de M02", departamentos["07"] - departamentos["15"])


if __name__ == "__main__":
    main()
