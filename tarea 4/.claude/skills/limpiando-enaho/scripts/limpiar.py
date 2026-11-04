"""Pipeline reproducible de miembros y sumaria de ENAHO 2024."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = [*LLAVES_HOGAR, "codperso"]
GEOGRAFIA = ["ubigeo", "dominio", "estrato"]
ANCHOS = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}
COLUMNAS_PERSONAS = [
    "anio", "mes", *LLAVES_PERSONA, *GEOGRAFIA,
    "p203", "p204", "p205", "p206", "p207", "p208a", "facpob07",
]
COLUMNAS_SUMARIA = ["anio", *LLAVES_HOGAR, *GEOGRAFIA, "pobreza", "factor07", "mieperho"]
REFERENCIAS = {"hogares": 33691, "miembros": 117721, "residentes": 108664}
TOLERANCIA_PP = 0.1


class ErrorValidacion(ValueError):
    """Una entrada o resultado incumple los controles del pipeline."""


def exigir(condicion: bool, mensaje: str) -> None:
    if not condicion:
        raise ErrorValidacion(mensaje)


def huella(ruta: Path) -> str:
    with ruta.open("rb") as archivo:
        return hashlib.file_digest(archivo, "sha256").hexdigest()


def leer_modulo(ruta: Path, nombre_dta: str) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta {ruta.name}; ejecutar scripts/preparar_datos.py")
    with ZipFile(ruta) as comprimido:
        candidatos = [n for n in comprimido.namelist() if Path(n).name.lower() == nombre_dta.lower()]
        exigir(len(candidatos) == 1, f"Se esperaba un único {nombre_dta} dentro de {ruta.name}")
        with comprimido.open(candidatos[0]) as archivo:
            return pd.read_stata(archivo, convert_categoricals=False)


def preparar_tabla(df: pd.DataFrame, columnas: list[str], anio: int, nombre: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = ["anio" if str(c).strip().lower() == "año" else str(c).strip().lower() for c in df.columns]
    exigir(df.columns.is_unique, f"{nombre}: nombres duplicados tras normalizar")
    faltantes = set(columnas) - set(df.columns)
    exigir(not faltantes, f"{nombre}: faltan columnas {sorted(faltantes)}")
    df = df[columnas].copy()
    exigir(not df.empty, f"{nombre}: tabla vacía")
    exigir(df.anio.astype("string").eq(str(anio)).fillna(False).all(), f"{nombre}: el año no es {anio}")
    for columna, ancho in ANCHOS.items():
        if columna in df:
            texto = df[columna].astype("string").str.strip()
            exigir(texto.str.fullmatch(rf"[0-9]{{{ancho}}}").fillna(False).all(), f"{nombre}: formato incorrecto en {columna}")
            df[columna] = texto
    llaves = LLAVES_PERSONA if "codperso" in df else LLAVES_HOGAR
    exigir(not df.duplicated(llaves).any(), f"{nombre}: llaves duplicadas {llaves}")
    exigir(df.dominio.isin(range(1, 9)).all(), f"{nombre}: dominio fuera de 1–8")
    exigir(df.estrato.isin(range(1, 9)).all(), f"{nombre}: estrato fuera de 1–8")
    exigir(df.ubigeo.str[:2].isin([f"{i:02d}" for i in range(1, 26)]).all(), f"{nombre}: departamento inválido")
    df["anio"] = anio
    return df


def pesos_validos(pesos: pd.Series, nombre: str) -> pd.Series:
    pesos = pd.to_numeric(pesos, errors="raise").astype("float64")
    exigir(pesos.notna().all() and pesos.map(math.isfinite).all() and pesos.gt(0).all(), f"{nombre}: pesos nulos, no finitos o no positivos")
    return pesos


def tasa_ponderada(indicador: pd.Series, pesos: pd.Series) -> float:
    exigir(not indicador.empty and indicador.index.equals(pesos.index), "Indicador y pesos vacíos o desalineados")
    exigir(indicador.notna().all() and indicador.isin([0, 1]).all(), "Indicador inválido o faltante")
    pesos = pesos_validos(pesos, "Tasa ponderada")
    return float(100 * (indicador.astype("float64") * pesos).sum() / pesos.sum())


def estimar(pobreza: pd.Series, pesos: pd.Series, nombre_peso: str) -> dict:
    return {
        "peso": nombre_peso,
        "pobreza_pct": tasa_ponderada(pobreza.isin([1, 2]), pesos),
        "extrema_pct": tasa_ponderada(pobreza.eq(1), pesos),
        "poblacion_expandida": float(pesos.sum()),
    }


def construir_base(personas: pd.DataFrame, sumaria: pd.DataFrame, anio: int) -> tuple[pd.DataFrame, dict]:
    personas = preparar_tabla(personas, COLUMNAS_PERSONAS, anio, "Miembros")
    sumaria = preparar_tabla(sumaria, COLUMNAS_SUMARIA, anio, "Sumaria")
    exigir(sumaria.pobreza.isin([1, 2, 3]).all(), "Sumaria: pobreza faltante o fuera de 1, 2, 3")
    factor_hogar = pesos_validos(sumaria.factor07, "factor07")
    miembros = pesos_validos(sumaria.mieperho, "mieperho")
    exigir(miembros.mod(1).eq(0).all(), "Sumaria: mieperho no entero")
    peso_sumaria = factor_hogar * miembros
    filtro = ((personas.p204 == 1) & (personas.p205 == 2)) | ((personas.p204 == 2) & (personas.p206 == 1))
    residentes = personas.loc[filtro.fillna(False)].copy()
    exigir(not residentes.empty, "No hay residentes habituales")
    residentes["facpob07"] = pesos_validos(residentes.facpob07, "facpob07 de residentes")
    exigir(residentes.p207.isin([1, 2]).all(), "Residentes: sexo faltante o fuera de 1, 2")
    edad = residentes.p208a
    exigir(edad.notna().all() and edad.between(0, 120).all() and edad.mod(1).eq(0).all(), "Residentes: edad faltante o inválida")
    base = residentes.merge(
        sumaria[[*LLAVES_HOGAR, *GEOGRAFIA, "pobreza"]],
        on=LLAVES_HOGAR, how="left", validate="m:1", suffixes=("", "_sumaria"), indicator=True,
    )
    exigir(base._merge.eq("both").all(), "Hay residentes sin hogar correspondiente en sumaria")
    exigir(len(base) == len(residentes), "La unión perdió o multiplicó residentes")
    exigir(not base.duplicated(LLAVES_PERSONA).any(), "La base tiene llaves de persona duplicadas")
    for columna in GEOGRAFIA:
        exigir(base[columna].eq(base[f"{columna}_sumaria"]).all(), f"Geografía distinta entre módulos: {columna}")
    base = base.drop(columns=["_merge", *[f"{c}_sumaria" for c in GEOGRAFIA]])
    base["departamento"] = base.ubigeo.str[:2]
    base["urbano"] = base.estrato.le(5)
    base["pobre"] = base.pobreza.isin([1, 2])
    base["pobre_extremo"] = base.pobreza.eq(1)
    base = base.sort_values(LLAVES_PERSONA, kind="stable", ignore_index=True)
    resumen = {
        "anio": anio,
        "filas": {
            "hogares": len(sumaria), "miembros": len(personas), "residentes": len(residentes),
            "excluidos": len(personas) - len(residentes), "base": len(base),
        },
        "controles": {
            "llaves_hogar_unicas": True, "llaves_persona_unicas": True,
            "personas_sin_hogar": 0, "filas_perdidas_o_multiplicadas": 0,
            "discrepancias_geograficas": 0, "departamentos": int(base.departamento.nunique()),
            "pesos_validos": True, "pobreza_sin_faltantes": True,
        },
        "estimaciones": {
            "sumaria": estimar(sumaria.pobreza, peso_sumaria, "factor07 * mieperho"),
            "personas": estimar(base.pobreza, base.facpob07, "facpob07"),
        },
    }
    return base, resumen


def validar_referencias(resumen: dict) -> None:
    exigir(resumen["anio"] == 2024, "No hay referencias implementadas para este año")
    for nombre, esperado in REFERENCIAS.items():
        exigir(resumen["filas"][nombre] == esperado, f"Conteo de {nombre}: {resumen['filas'][nombre]}, esperado {esperado}")
    exigir(resumen["controles"]["departamentos"] == 25, "La base no contiene los 25 departamentos")
    for universo, estimacion in resumen["estimaciones"].items():
        for indicador, referencia in [("pobreza_pct", 27.6), ("extrema_pct", 5.5)]:
            exigir(abs(estimacion[indicador] - referencia) < TOLERANCIA_PP, f"{universo}, {indicador}: diferencia de al menos {TOLERANCIA_PP} puntos con la referencia")


def escribir_texto(ruta: Path, contenido: str) -> None:
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(contenido, encoding="utf-8")
    temporal.replace(ruta)


def informe_texto(resumen: dict) -> str:
    filas = resumen["filas"]
    lineas = [
        "VALIDACIÓN ENAHO 2024", "Estado: OK", "",
        f"Hogares en sumaria: {filas['hogares']:,}",
        f"Registros en miembros: {filas['miembros']:,}",
        f"Residentes habituales / filas finales: {filas['residentes']:,} / {filas['base']:,}",
        f"Miembros excluidos por residencia: {filas['excluidos']:,}",
        "Llaves de hogar y persona: únicas, como texto y con sus ceros",
        "Unión: m:1; cero residentes sin hogar; cero filas perdidas o duplicadas",
        "Geografía: coincidente entre módulos; 25 departamentos",
        "Pobreza: códigos 1, 2 y 3 válidos, sin faltantes; pesos positivos y finitos", "",
        "Referencia nacional: pobreza 27.6 %; extrema 5.5 %; tolerancia < 0.1 puntos porcentuales",
    ]
    for universo, estimacion in resumen["estimaciones"].items():
        lineas.extend([
            f"{universo.capitalize()} (peso: {estimacion['peso']}):",
            f"  Pobreza: {estimacion['pobreza_pct']:.5f} %; extrema: {estimacion['extrema_pct']:.5f} %",
            f"  Población expandida: {estimacion['poblacion_expandida']:,.2f}",
        ])
    lineas.extend([
        "", "Las referencias del curso por departamento y área proceden de sumaria.",
        "Para analizar personas se usa facpob07; ambos universos pueden producir tasas distintas.",
        "No multiplicar facpob07 por mieperho ni promediar los códigos de pobreza.",
        "Estas son estimaciones puntuales; no se calcularon errores estándar del diseño muestral.",
        f"Base: salidas/{resumen['base']['archivo']}",
        f"SHA-256 base: {resumen['base']['sha256']}",
    ])
    return "\n".join(lineas) + "\n"


def ejecutar(raiz: Path, anio: int) -> dict:
    salida = raiz / "salidas"
    salida.mkdir(parents=True, exist_ok=True)
    json_salida = salida / f"validacion_{anio}.json"
    try:
        exigir(anio == 2024, "Este pipeline y sus referencias solo admiten 2024")
        fuentes = [
            (raiz / "datos/966-Modulo34.zip", "sumaria-2024.dta"),
            (raiz / "datos/966-Modulo02.zip", "enaho01-2024-200.dta"),
        ]
        sumaria, personas = [leer_modulo(ruta, dta) for ruta, dta in fuentes]
        base, resumen = construir_base(personas, sumaria, anio)
        validar_referencias(resumen)
        destino = salida / f"personas_{anio}.parquet"
        temporal = destino.with_suffix(".parquet.tmp")
        base.to_parquet(temporal, engine="pyarrow", compression="snappy", index=False)
        temporal.replace(destino)
        resumen.update({
            "estado": "OK",
            "referencias": {"pobreza_pct": 27.6, "extrema_pct": 5.5, "tolerancia_pp": TOLERANCIA_PP},
            "entradas": [{"archivo": str(ruta.relative_to(raiz)).replace("\\", "/"), "dta": dta, "sha256": huella(ruta)} for ruta, dta in fuentes],
            "base": {"archivo": destino.name, "sha256": huella(destino), "columnas": list(base.columns)},
        })
        escribir_texto(json_salida, json.dumps(resumen, ensure_ascii=False, indent=2) + "\n")
        filas = [
            {"indicador": indicador, "unidad_analisis": universo, "ambito": "nacional",
             "codigo": "PE", "periodo": anio, "valor": estimacion[clave], "unidad": "%",
             "fuente": "INEI, ENAHO 2024", "ponderador": estimacion["peso"]}
            for universo, estimacion in resumen["estimaciones"].items()
            for indicador, clave in (("pobreza monetaria", "pobreza_pct"), ("pobreza extrema", "extrema_pct"))
        ]
        escribir_texto(salida / "indicadores.csv", pd.DataFrame(filas).to_csv(index=False, lineterminator="\n"))
        escribir_texto(salida / "validacion.txt", informe_texto(resumen))
        return resumen
    except (OSError, ValueError, BadZipFile) as error:
        fallo = {"estado": "ERROR", "anio": anio, "error": str(error)}
        escribir_texto(json_salida, json.dumps(fallo, ensure_ascii=False, indent=2) + "\n")
        escribir_texto(salida / "validacion.txt", f"VALIDACIÓN ENAHO {anio}\nEstado: ERROR\n{error}\nUna base previa no queda validada por esta ejecución.\n")
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio", type=int, choices=[2024], required=True)
    argumentos = parser.parse_args()
    try:
        resumen = ejecutar(RAIZ, argumentos.anio)
    except (OSError, ValueError, BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {resumen['filas']['base']:,} residentes; pobreza de personas {resumen['estimaciones']['personas']['pobreza_pct']:.5f} %")
    print("Leer salidas/validacion.txt antes de analizar la base.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
