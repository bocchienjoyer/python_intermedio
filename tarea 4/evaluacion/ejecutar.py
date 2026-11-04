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
    if modo == "A":
        return
    shutil.copy2(RAIZ / "pyproject.toml", carpeta / "pyproject.toml")
    if (RAIZ / "uv.lock").is_file():
        shutil.copy2(RAIZ / "uv.lock", carpeta / "uv.lock")
    for nombre in (".agents/skills", ".claude/skills", "mcp", "scripts", "referencias"):
        shutil.copytree(RAIZ / nombre, carpeta / nombre,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"))
    datos = carpeta / "datos"
    datos.mkdir()
    for nombre in ENTRADAS:
        shutil.copy2(RAIZ / "datos" / nombre, datos / nombre)



def ejecutar(codex, fila, modo, modelo, registros):
    with tempfile.TemporaryDirectory(prefix=f"tarea4-{modo}-") as directorio:
        carpeta = Path(directorio)
        preparar(modo, carpeta)
        comando = [codex, "-c", 'model_reasoning_effort="low"']
        if modo == "B":
            comando.extend([
                "-c", 'mcp_servers.bcrp={command="uv",args=["run","python","mcp/server.py"],required=true,startup_timeout_sec=90}',
            ])
        comando.extend([
            "exec", "--model", modelo, "--ephemeral", "--ignore-user-config",
            "--skip-git-repo-check", "--approve-for-me", "--json", "-",
        ])
        prompt = (
            "Responde en español. Indica las cifras, unidades, período, ámbito y fuente. "
            "Usa únicamente las herramientas disponibles y los archivos de esta carpeta de trabajo. "
            "Mantén los microdatos localmente y devuelve solo resultados agregados. Si faltan datos para verificar una cifra, dilo. No delegues.\n\n" + fila["pregunta"]
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
    items = [evento["item"] for evento in eventos if evento.get("type") == "item.completed"]
    respuesta = next((item["text"] for item in reversed(items)
                      if item["type"] == "agent_message"), "")
    usos = dict.fromkeys(
        f"{item.get('server', '')}/{item.get('tool', '')}" if item["type"] == "mcp_tool_call"
        else item["type"]
        for item in items if item["type"] in {"mcp_tool_call", "command_execution", "web_search"}
    )
    completo = any(evento["type"] == "turn.completed" for evento in eventos)
    error = next((evento.get("message") for evento in reversed(eventos)
                  if evento["type"] == "error"), None)
    if not completo and not error:
        error = f"Codex terminó con código {proceso.returncode} sin completar la respuesta"
    return {
        "id_pregunta": fila["id"], "modo": modo, "pregunta": fila["pregunta"],
        "respuesta_esperada": fila["respuesta_esperada"],
        "respuesta_generada": respuesta if completo else "",
        "fuente": "", "herramientas": ", ".join(usos), "correcta": "",
        "tiempo_segundos": f"{segundos:.3f}",
        "error": error or "",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", required=True, help="Identificador fijo de modelo de Codex")
    parser.add_argument("--registros", type=Path, required=True, help="Carpeta local fuera del repositorio")
    parser.add_argument("--pregunta", help="ID para una comprobación individual")
    args = parser.parse_args()
    codex = shutil.which("codex")
    if not codex or subprocess.run([codex, "login", "status"], capture_output=True).returncode != 0:
        parser.error("Inicia sesión en Codex antes de ejecutar la evaluación")
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
                resultado = ejecutar(codex, fila, modo, args.modelo, registros)
                if escritor is None:
                    escritor = csv.DictWriter(archivo, fieldnames=resultado)
                    escritor.writeheader()
                escritor.writerow(resultado)
                archivo.flush()
                print(f"{modo} {fila['id']} · {resultado['tiempo_segundos']} s", flush=True)


if __name__ == "__main__":
    main()
