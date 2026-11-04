"""Validación de la base y agregación compartidas por gráficos y mapas."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


class ErrorAnalisis(ValueError):
    """No se puede analizar una base o una unión sin validar."""


def exigir(condicion: bool, mensaje: str) -> None:
    if not condicion:
        raise ErrorAnalisis(mensaje)


def huella(ruta: Path) -> str:
    with ruta.open("rb") as archivo:
        return hashlib.file_digest(archivo, "sha256").hexdigest()


def cargar_base_validada(raiz: Path, anio: int) -> tuple[pd.DataFrame, dict]:
    exigir(anio == 2024, "Este proyecto solo tiene implementada ENAHO 2024")
    ruta = raiz / f"salidas/personas_{anio}.parquet"
    ruta_json = raiz / f"salidas/validacion_{anio}.json"
    ruta_txt = raiz / "salidas/validacion.txt"
    archivos = (ruta, ruta_json, ruta_txt)
    if any(not archivo.is_file() for archivo in archivos):
        limpieza = raiz / ".claude/skills/limpiando-enaho/scripts/limpiar.py"
        resultado = subprocess.run([sys.executable, str(limpieza), "--anio", str(anio)], cwd=raiz)
        exigir(resultado.returncode == 0, "No se pudo preparar una base ENAHO validada")
    for archivo in archivos:
        if not archivo.is_file():
            raise FileNotFoundError(f"Falta {archivo.name}; usar primero la skill limpiando-enaho")
    informe = json.loads(ruta_json.read_text(encoding="utf-8"))
    exigir(informe.get("estado") == "OK" and informe.get("anio") == anio, "La limpieza no tiene validación OK para el año pedido")
    exigir("Estado: OK" in ruta_txt.read_text(encoding="utf-8").splitlines(), "validacion.txt no tiene estado OK")
    exigir(informe.get("base", {}).get("archivo") == ruta.name, "El informe corresponde a otra base")
    exigir(informe["base"].get("sha256") == huella(ruta), "El SHA-256 de la base no coincide con su validación; repetir limpiando-enaho")
    base = pd.read_parquet(ruta)
    columnas = {
        "anio", "conglome", "vivienda", "hogar", "codperso", "ubigeo", "estrato",
        "departamento", "urbano", "pobreza", "pobre", "facpob07", "p207", "p208a",
    }
    exigir(columnas.issubset(base.columns), f"Faltan columnas en la base: {sorted(columnas - set(base.columns))}")
    exigir(not base.empty and len(base) == informe.get("filas", {}).get("base"), "El número de filas no coincide con la validación")
    exigir(base.anio.eq(anio).fillna(False).all(), "La base contiene otro año o un año faltante")
    exigir(not base.duplicated(["conglome", "vivienda", "hogar", "codperso"]).any(), "Hay personas duplicadas")
    exigir(base.pobreza.isin([1, 2, 3]).all(), "Pobreza faltante o fuera de 1, 2, 3")
    exigir(base.pobre.isin([0, 1]).all() and base.pobre.eq(base.pobreza.isin([1, 2])).all(), "El indicador de pobreza es inválido")
    exigir(base.estrato.isin(range(1, 9)).all() and base.urbano.eq(base.estrato.le(5)).fillna(False).all(), "Área de residencia inconsistente")
    exigir(base.p207.isin([1, 2]).all(), "Sexo faltante o fuera de 1, 2")
    exigir(base.p208a.between(0, 120).fillna(False).all() and base.p208a.mod(1).eq(0).all(), "Edad faltante o inválida")
    codigos = base.departamento.astype("string")
    exigir(codigos.str.fullmatch(r"[0-9]{2}").fillna(False).all(), "Códigos departamentales sin formato de dos caracteres")
    exigir(codigos.eq(base.ubigeo.astype("string").str[:2]).fillna(False).all(), "Departamento y ubigeo no coinciden")
    base["facpob07"] = pesos_validos(base.facpob07)
    return base, informe


def pesos_validos(pesos: pd.Series) -> pd.Series:
    pesos = pd.to_numeric(pesos, errors="raise").astype("float64")
    exigir(pesos.notna().all() and pesos.map(math.isfinite).all() and pesos.gt(0).all(), "Pesos faltantes, no finitos o no positivos")
    return pesos


def agrupar_pobreza(base: pd.DataFrame, grupos: pd.Series) -> pd.DataFrame:
    exigir(not base.empty and grupos.index.equals(base.index), "Los grupos no corresponden a las filas de la base")
    exigir(grupos.notna().all(), "Hay personas sin grupo asignado")
    exigir(base.pobre.notna().all() and base.pobre.isin([0, 1]).all(), "Indicador de pobreza inválido")
    peso = pesos_validos(base.facpob07)
    datos = pd.DataFrame({
        "grupo": grupos.astype("string"), "peso": peso,
        "peso_pobre": peso * base.pobre.astype("float64"),
    })
    tabla = datos.groupby("grupo", sort=True).agg(
        n_personas=("peso", "size"), poblacion_expandida=("peso", "sum"),
        poblacion_pobre=("peso_pobre", "sum"),
    ).reset_index()
    tabla["pobreza_pct"] = 100 * tabla.poblacion_pobre / tabla.poblacion_expandida
    exigir(tabla.pobreza_pct.between(0, 100).all(), "Tasa fuera de 0–100 %")
    exigir(int(tabla.n_personas.sum()) == len(base), "La agregación perdió personas")
    return tabla


def iniciar_graficos(raiz: Path):
    os.environ.setdefault("MPLCONFIGDIR", str(raiz / ".matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def porcentaje(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",") + " %"


def guardar_json(ruta: Path, contenido: dict) -> None:
    ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
