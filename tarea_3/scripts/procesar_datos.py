"""Prepara una fila por obra INFOBRAS sin equiparar obra e inversión CUI."""
from pathlib import Path
import json
import re
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CAMPOS = {1:'infobras',2:'cui',5:'obra',6:'entidad',8:'modalidad',9:'costo_obra',10:'saldo_obra',
          11:'costo_inversion',13:'saldo_inversion',14:'pim_2026',15:'tiene_pim',16:'tipo_obra',
          17:'subtipo_obra',18:'infraestructura',19:'departamento',20:'provincia',21:'distrito',
          22:'anio_inicio',23:'plazo_dias',24:'avance',25:'rango_avance_fuente',26:'nivel_gobierno',
          27:'sector',28:'causa',30:'inventario_mef',32:'informe_situacional',34:'url_informe'}

def main():
    archivo = next((RAIZ/'datos/originales').glob('*anexo-n-01*.XLSX'))
    fuente = pd.read_excel(archivo, sheet_name='Data')
    if len(fuente.columns) != 38 or 'INFOBRAS' not in fuente.columns[1] or 'AVANCE' not in fuente.columns[24]:
        raise ValueError('Cambió el esquema del anexo: revisar el mapeo antes de continuar.')
    datos=fuente.iloc[:,list(CAMPOS)].copy()
    datos.columns=list(CAMPOS.values())
    for c in datos.columns:
        datos[c]=datos[c].map(lambda x: re.sub(r'\s+',' ',x).strip() if isinstance(x,str) else x)
        datos[c]=datos[c].replace('',pd.NA)
    # Ausencia declarada por la fuente, distinta del valor numérico cero.
    datos=datos.replace(r'(?i)^no declarado$',pd.NA,regex=True)
    for c in ['infobras','cui','anio_inicio']:
        datos[c]=pd.to_numeric(datos[c],errors='raise').astype('Int64')
    datos.loc[datos.cui.eq(0),'cui']=pd.NA
    for c in ['costo_obra','saldo_obra','costo_inversion','saldo_inversion','pim_2026','plazo_dias','avance']:
        datos[c]=pd.to_numeric(datos[c],errors='raise')
    # Un cero se conserva como valor reportado. No se interpreta como costo real nulo.
    datos['causa']=datos['causa'].str.replace(r'^\d+\s+','',regex=True)
    datos['corte']='2026-06-30'
    datos['avance_alto']=datos['avance'].gt(90)&datos['avance'].le(100)
    # Tabla 12 del informe: NO PIM incluye obras sin CUI. No equiparar ambos casos.
    datos['estado_presupuesto']='sin_asignacion_registrada'
    datos.loc[datos.pim_2026.gt(0),'estado_presupuesto']='con_asignacion'
    datos.loc[datos.cui.isna(),'estado_presupuesto']='sin_cui'
    if datos['infobras'].isna().any() or datos['infobras'].duplicated().any():
        raise ValueError('El código INFOBRAS debe identificar una obra única.')
    if ((datos['avance']<0)|(datos['avance']>100)).any():
        raise ValueError('Avance fuera de 0–100 %.')
    if not datos.avance_alto.eq(datos.rango_avance_fuente.eq('90 - 100 %')).all():
        raise ValueError('El umbral de avance alto no coincide con el rango de la fuente.')
    if not datos.tiene_pim.eq('SI').eq(datos.pim_2026.gt(0)).all():
        raise ValueError('La bandera de PIM difiere de la asignación numérica.')
    if (datos.cui.isna()&datos.pim_2026.gt(0)).any():
        raise ValueError('Revisar obras sin CUI que registren PIM positivo.')
    salida=RAIZ/'datos/procesados';salida.mkdir(exist_ok=True)
    datos.to_csv(salida/'obras.csv',index=False,encoding='utf-8')
    calidad={'filas_originales':len(fuente),'obras':len(datos),'duplicados_infobras':int(datos.infobras.duplicated().sum()),
             'cui_unicos':int(datos.cui.nunique()),'cui_faltantes':int(datos.cui.isna().sum()),
             'obras_con_cui_repetido':int((datos.cui.notna()&datos.cui.duplicated(keep=False)).sum()),
             'estado_presupuesto':datos.estado_presupuesto.value_counts().to_dict(),
             'faltantes':{c:int(datos[c].isna().sum()) for c in datos},
             'costos_obra_cero':int(datos.costo_obra.eq(0).sum()),
             'avance_cien':int(datos.avance.eq(100).sum()),
             'anios_posteriores_corte':int(datos.anio_inicio.gt(2026).sum()),
             'montos_negativos':{c:int(datos[c].lt(0).sum()) for c in ['costo_obra','saldo_obra','costo_inversion','saldo_inversion','pim_2026']}}
    (salida/'calidad.json').write_text(json.dumps(calidad,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(calidad,ensure_ascii=False))

if __name__=='__main__':main()
