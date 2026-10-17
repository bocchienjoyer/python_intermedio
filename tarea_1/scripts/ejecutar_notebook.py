"""Ejecuta un notebook usando el mismo Python del entorno aislado."""

import argparse
from pathlib import Path
import sys

from jupyter_client import KernelManager
from nbclient import NotebookClient
import nbformat

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("notebook")
args = parser.parse_args()
path = Path(args.notebook).resolve()


class CurrentPythonKernel(KernelManager):
    def format_kernel_cmd(self, extra_arguments=None):
        return [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}".format(connection_file=self.connection_file)] + (extra_arguments or [])


notebook = nbformat.read(path, as_version=4)
client = NotebookClient(notebook, timeout=2400, kernel_name="python3",
                        kernel_manager_class=CurrentPythonKernel,
                        resources={"metadata": {"path": str(path.parent)}})
try:
    client.execute()
finally:
    nbformat.write(notebook, path)
print("Notebook ejecutado:", path)
print("Celdas de código:", sum(c.cell_type == "code" for c in notebook.cells))
print("Errores:", sum(o.output_type == "error" for c in notebook.cells if c.cell_type == "code" for o in c.get("outputs", [])))
