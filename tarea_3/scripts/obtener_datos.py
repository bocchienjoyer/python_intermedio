"""Descarga el informe y sus anexos desde la publicación original de Contraloría."""
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import hashlib
import html
import json
import re

RAIZ = Path(__file__).resolve().parents[1]
PUBLICACION = 'https://www.gob.pe/institucion/contraloria/informes-publicaciones/8489152-informe-de-obras-paralizadas-en-el-territorio-nacional-a-junio-de-2026'

def descargar(url):
    with urlopen(Request(url, headers={'User-Agent': 'Investigacion-academica-obras/1.0'}), timeout=90) as respuesta:
        return respuesta.read()

def main():
    destino = RAIZ / 'datos' / 'originales'
    destino.mkdir(parents=True, exist_ok=True)
    pagina = descargar(PUBLICACION).decode('utf-8')
    manifiesto = destino / 'fuentes.json'
    anteriores = {r['archivo']: r for r in json.loads(manifiesto.read_text(encoding='utf-8'))} if manifiesto.exists() else {}
    enlaces = list(dict.fromkeys(html.unescape(u) for u in re.findall(r'href=["\x27]([^"\x27]+)', pagina)
                               if 'cdn.www.gob.pe/uploads/document/file/' in u))
    registros = []
    for url in enlaces:
        nombre = url.split('/')[-1].split('?')[0]
        if not nombre.lower().endswith(('.xlsx', '.pdf')):
            continue
        archivo = destino / nombre
        anterior = anteriores.get(nombre)
        if not archivo.exists() or anterior is None:
            archivo.write_bytes(descargar(url))
            recuperado = datetime.now(timezone.utc).isoformat()
        else:
            recuperado = anterior['recuperado_utc']
        contenido = archivo.read_bytes()
        huella = hashlib.sha256(contenido).hexdigest()
        if anterior is not None and huella != anterior['sha256']:
            raise ValueError(f'El original cambió respecto del manifiesto: {nombre}. Revisar antes de actualizar.')
        registros.append({'archivo': nombre, 'url': url, 'publicacion': PUBLICACION,
                          'corte': '2026-06-30', 'recuperado_utc': recuperado,
                          'sha256': huella, 'bytes': len(contenido)})
        print(nombre, len(contenido))
    if not registros:
        raise RuntimeError('La publicación no contiene los archivos esperados.')
    (destino / 'fuentes.json').write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
