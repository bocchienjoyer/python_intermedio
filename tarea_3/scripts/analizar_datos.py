"""Calcula estadísticas descriptivas del inventario de obras paralizadas."""
from pathlib import Path
import json
import pandas as pd

RAIZ=Path(__file__).resolve().parents[1]

def main():
    salida=RAIZ/'datos/procesados'
    d=pd.read_csv(salida/'obras.csv',dtype={'infobras':'string','cui':'string'})
    alto=d[d.avance.gt(90)&d.avance.le(100)]
    identificadas=alto[alto.cui.notna()]
    sin_cien=identificadas[identificadas.avance.lt(100)]
    resumen={'corte':'2026-06-30','obras':len(d),'avance_alto':len(alto),'porcentaje_avance_alto':round(100*len(alto)/len(d),2),
             'avance_alto_cero_en_fuente_incluye_sin_cui':int(alto.pim_2026.eq(0).sum()),
             'avance_alto_sin_cui':int(alto.cui.isna().sum()),
             'avance_alto_con_cui':len(identificadas),
             'avance_alto_con_asignacion':int(alto.estado_presupuesto.eq('con_asignacion').sum()),
             'avance_alto_sin_asignacion_registrada':int(identificadas.pim_2026.eq(0).sum()),
             'porcentaje_alto_sin_asignacion_entre_con_cui':round(100*identificadas.pim_2026.eq(0).mean(),2),
             'entidades':int(d.entidad.nunique()),'departamentos':int(d.departamento.nunique()),
             'avance_mediano':float(d.avance.median()),'costo_obra_reportado':float(d.costo_obra.sum()),
             'anio_inicio_conocido':int(d.anio_inicio.notna().sum()),
             'inicio_hasta_2015':int(d.anio_inicio.le(2015).sum()),
             'alto_inicio_hasta_2015':int(alto.anio_inicio.le(2015).sum()),
             'alto_avance_cien':int(alto.avance.eq(100).sum()),
             'alto_sin_cien':int(alto.avance.lt(100).sum()),
             'alto_sin_cien_con_cui':len(sin_cien),
             'alto_sin_cien_sin_cui':int((alto.avance.lt(100)&alto.cui.isna()).sum()),
             'alto_sin_cien_sin_asignacion_registrada':int(sin_cien.pim_2026.eq(0).sum()),
             'porcentaje_alto_sin_cien_sin_asignacion_entre_con_cui':round(100*sin_cien.pim_2026.eq(0).mean(),2),
             'alto_vivienda_y_transporte':int(alto.tipo_obra.isin(['Vivienda, Construcción Y Saneamiento','Transportes Y Comunicaciones']).sum()),
             'cero_en_fuente_incluye_sin_cui_total':int(d.pim_2026.eq(0).sum()),
             'sin_cui_total':int(d.cui.isna().sum()),
             'con_cui_total':int(d.cui.notna().sum()),
             'sin_asignacion_registrada_total':int(d.estado_presupuesto.eq('sin_asignacion_registrada').sum()),
             'porcentaje_sin_asignacion_entre_con_cui_total':round(100*d.loc[d.cui.notna(),'pim_2026'].eq(0).mean(),2)}
    for col in ['departamento','tipo_obra','nivel_gobierno','causa']:
        tabla=d.groupby(col,dropna=False).agg(obras=('infobras','size'),avance_alto=('avance_alto','sum'),
                  costo_obra_reportado=('costo_obra','sum')).reset_index()
        tabla['porcentaje_obras']=100*tabla.obras/len(d)
        tabla.sort_values('obras',ascending=False).to_csv(salida/f'por_{col}.csv',index=False)
    alto.groupby('tipo_obra').size().sort_values(ascending=False).to_csv(salida/'avance_alto_por_tipo.csv',header=['obras'])
    (salida/'resumen.json').write_text(json.dumps(resumen,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(resumen,ensure_ascii=False,indent=2))
    print('AVANCE ALTO: TIPO',alto.tipo_obra.value_counts().to_dict())
    print('CAUSAS',d.causa.value_counts().head(6).to_dict())
    print('ALTO CAUSAS',alto.causa.value_counts().head(6).to_dict())

if __name__=='__main__':main()
