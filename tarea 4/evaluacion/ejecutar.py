"""Ejecuta preguntas en sesiones nuevas y conserva el registro bruto en local."""

import argparse
import csv
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from time import perf_counter

RAIZ = Path(__file__).resolve().parents[1]
EVALUACION = RAIZ / "evaluacion"
ENTRADAS = ("966-Modulo34.zip", "966-Modulo02.zip", "peru_departamental_simple.geojson")


def preparar(modo, carpeta):
    config = carpeta / ".mcp.json"
    if modo == "A":
        config.write_text('{"mcpServers": {}}', encoding="utf-8")
        return config
    for nombre in (".mcp.json", "pyproject.toml"):
        shutil.copy2(RAIZ / nombre, carpeta / nombre)
    for nombre in (".claude/skills", "mcp", "scripts", "referencias"):
        shutil.copytree(RAIZ / nombre, carpeta / nombre,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"))
    if (RAIZ / "uv.lock").is_file():
        shutil.copy2(RAIZ / "uv.lock", carpeta / "uv.lock")
    datos = carpeta / "datos"
    datos.mkdir()
    for nombre in ENTRADAS:
        shutil.copy2(RAIZ / "datos" / nombre, datos / nombre)
    return config


def ejecutar(claude, fila, modo, modelo, registros):
    with tempfile.TemporaryDirectory(prefix=f"tarea4-{modo}-") as directorio:
        carpeta = Path(directorio)
        config = preparar(modo, carpeta)
        herramientas = "" if modo == "A" else "Read,Skill,Bash"
        permitidas = ["Read", "Skill", "Bash(uv run python .claude/skills/*)", "mcp__bcrp"]
        comando = [
            claude, "-p", "--model", modelo, "--no-session-persistence",
            "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", str(config),
            "--tools", herramientas, "--permission-mode", "dontAsk",
            "--output-format", "stream-json", "--verbose",
        ]
        if modo == "B":
            comando.extend(["--allowedTools", ",".join(permitidas)])
        prompt = (
            "Responde en español. Indica las cifras, unidades, período, ámbito y fuente. "
            "Si faltan datos para verificar una cifra, dilo.\n\n" + fila["pregunta"]
        )
        entorno = os.environ.copy()
        entorno.pop("UV_PROJECT_ENVIRONMENT", None)
        entorno.pop("UV_NO_SYNC", None)
        inicio = perf_counter()
        proceso = subprocess.run(
            comando, input=prompt, cwd=carpeta, capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=entorno,
        )
        segundos = perf_counter() - inicio
    registro = registros / f"{modo}_{fila['id']}.jsonl"
    registro.write_text(proceso.stdout, encoding="utf-8")
    registro.with_suffix(".prompt.txt").write_text(prompt, encoding="utf-8")
    if proceso.stderr:
        registro.with_suffix(".stderr.txt").write_text(proceso.stderr, encoding="utf-8")
    eventos = [json.loads(linea) for linea in proceso.stdout.splitlines() if linea.startswith("{")]
    resultado = next((evento for evento in reversed(eventos) if evento.get("type") == "result"), {})
    usos = dict.fromkeys(
        bloque["name"] for evento in eventos if evento.get("type") == "assistant"
        for bloque in evento.get("message", {}).get("content", [])
        if bloque.get("type") == "tool_use" and "name" in bloque
    )
    error = proceso.returncode != 0 or resultado.get("is_error") or not resultado
    return {
        "id_pregunta": fila["id"], "modo": modo, "pregunta": fila["pregunta"],
        "respuesta_esperada": fila["respuesta_esperada"],
        "respuesta_generada": "" if error else resultado.get("result", ""),
        "fuente": "", "herramientas": ", ".join(usos), "correcta": "",
        "tiempo_segundos": f"{segundos:.3f}",
        "error": (resultado.get("result") or f"Claude Code terminó con código {proceso.returncode}")
        if error else "",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", required=True, help="Identificador fijo de modelo de Claude Code")
    parser.add_argument("--registros", type=Path, required=True, help="Carpeta local fuera del repositorio")
    parser.add_argument("--pregunta", help="ID para una comprobación individual")
    args = parser.parse_args()
    claude = shutil.which("claude")
    if not claude or subprocess.run([claude, "auth", "status"], capture_output=True).returncode != 0:
        parser.error("Inicia sesión en Claude Code antes de ejecutar la evaluación")
    registros = args.registros.resolve()
    if registros.is_relative_to(RAIZ.parent):
        parser.error("Los registros completos deben guardarse fuera del repositorio para revisión")
    registros.mkdir(parents=True, exist_ok=True)
    destino = registros / "resultados.csv"
    if destino.exists():
        parser.error("Usa una carpeta nueva para conservar la ejecución anterior")
    with (EVALUACION / "preguntas.csv").open(encoding="utf-8", newline="") as archivo:
        preguntas = [fila for fila in csv.DictReader(archivo) if args.pregunta in (None, fila["id"])]
    if not preguntas:
        parser.error("ID de pregunta desconocido")
    with destino.open("w", encoding="utf-8", newline="") as archivo:
        escritor = None
        for fila in preguntas:
            for modo in ("A", "B"):
                resultado = ejecutar(claude, fila, modo, args.modelo, registros)
                if escritor is None:
                    escritor = csv.DictWriter(archivo, fieldnames=resultado)
                    escritor.writeheader()
                escritor.writerow(resultado)
                archivo.flush()
                print(f"{modo} {fila['id']} · {resultado['tiempo_segundos']} s", flush=True)


if __name__ == "__main__":
    main()
