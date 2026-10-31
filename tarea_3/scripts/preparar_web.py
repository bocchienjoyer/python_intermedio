"""Exporta los registros del análisis y la cartografía oficial para la web estática."""
from pathlib import Path
from urllib.request import urlopen
import json
import pandas as pd

RAIZ=Path(__file__).resolve().parents[1]
MAPA='https://ws.mineco.gob.pe/server/rest/services/cartografia_base_limites/MapServer/1/query?where=1%3D1&outFields=*&outSR=4326&geometryPrecision=3&maxAllowableOffset=0.02&f=geojson'
def main():
    destino=RAIZ/'web/data';destino.mkdir(exist_ok=True)
    d=pd.read_csv(RAIZ/'datos/procesados/obras.csv',dtype={'infobras':'string','cui':'string'})
    campos=['infobras','cui','obra','entidad','modalidad','costo_obra','departamento','provincia','distrito',
            'anio_inicio','avance','tipo_obra','nivel_gobierno','causa','pim_2026','estado_presupuesto','url_informe']
    (destino/'obras.json').write_text(d[campos].to_json(orient='records',force_ascii=False),encoding='utf-8')
    mapa=destino/'departamentos.geojson'
    if not mapa.exists():
        contenido=urlopen(MAPA,timeout=90).read()
        if len(json.loads(contenido).get('features',[]))!=25:raise ValueError('La cartografía debe incluir 25 unidades.')
        mapa.write_bytes(contenido)
    (destino/'fuentes_mapa.json').write_text(json.dumps({'url':MAPA,'proveedor':'MEF, capa Límite Departamental',
        'fuente_atribucion':'INEI, según atributos de la capa','uso':'Límites referenciales para visualización, sin medición de áreas.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Web:',len(d),'obras y 25 unidades cartográficas.')
if __name__=='__main__':main()
