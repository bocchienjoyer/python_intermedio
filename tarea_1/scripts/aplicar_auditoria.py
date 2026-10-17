"""Sustituye descartes humanos solo dentro de train, sin mover validación ni test."""

import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.recoleccion import COLUMNS, PoliteClient, article_metadata, title_key, now
from difflib import SequenceMatcher

data = pd.read_csv(ROOT / 'datos/noticias.csv', keep_default_na=False)
splits = pd.read_csv(ROOT / 'datos/particiones.csv', keep_default_na=False)
audit = pd.read_csv(ROOT / 'datos/auditoria_humana.csv', keep_default_na=False)
metadata_path = ROOT / 'resultados/particiones.json'
metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
corrections_path = ROOT / 'datos/correcciones_auditoria.csv'

if corrections_path.exists():
    old = pd.read_csv(corrections_path, keep_default_na=False)
    if set(old.url_reemplazo).issubset(set(data.url)) and not set(old.url_descartada).intersection(data.url):
        print('Correcciones ya aplicadas; validación y test conservados.')
        sys.exit(0)
    raise RuntimeError('Las correcciones registradas no coinciden con el dataset; revisar antes de continuar.')

digest_before = hashlib.sha256((ROOT / 'datos/noticias.csv').read_text(encoding='utf-8').encode()).hexdigest()
assert digest_before == metadata['sha256_dataset']
test_before = set(splits[splits.particion == 'test'].url)
val_before = set(splits[splits.particion == 'validacion'].url)
flagged = audit[audit.decision_humana == 'descartar'].merge(splits, on='url', validate='one_to_one')
assert len(flagged) and flagged.particion.eq('train').all(), 'Esta corrección solo permite sustituir casos de train.'

client = PoliteClient()
candidates = pd.read_csv(ROOT / 'datos/candidatos.csv', keep_default_na=False)
records = []
data.to_csv(ROOT / 'datos/noticias_antes_auditoria.csv', index=False, encoding='utf-8')
(ROOT / 'resultados/particiones_antes_auditoria.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')


def replacement(category):
    filters = {'politica': 'congreso|senado', 'ciencia_tecnologia': 'nasa|planeta|telescopio|astronom|fisic|galax'}
    pool = candidates[(candidates.etiqueta == category) & ~candidates.url.isin(data.url)
                      & candidates.url.str.contains('/2026/')
                      & candidates.url.str.contains(filters[category], regex=True)]
    pool = pool.sample(frac=1, random_state=42)
    proposal = ROOT / 'datos/reemplazo_auditoria_propuesto.json'
    preferred = json.loads(proposal.read_text(encoding='utf-8')) if proposal.exists() else None
    urls = ([preferred['url']] if preferred and preferred['etiqueta'] == category else []) + pool.url.tolist()
    for url in dict.fromkeys(urls):
        try:
            row = article_metadata(client.get(url), url)
            if row['etiqueta'] != category or not all(row[c] for c in COLUMNS):
                continue
            if not '2026-01-01' <= row['fecha'] <= now()[:10]:
                continue
            key = title_key(row['titular'])
            if any(SequenceMatcher(None, key, title_key(t), autojunk=False).ratio() >= 0.95 for t in data.titular):
                continue
            return {c: row[c] for c in COLUMNS}
        except Exception as error:
            print('Candidato no utilizado:', type(error).__name__, flush=True)
    raise RuntimeError('No hay un reemplazo válido disponible para ' + category)


for row in flagged.itertuples():
    original = data[data.url == row.url].iloc[0]
    new = replacement(original.etiqueta)
    assert new['url'] not in set(data.url)
    data.loc[data.url == row.url, COLUMNS] = [new[c] for c in COLUMNS]
    splits.loc[splits.url == row.url, 'url'] = new['url']
    records.append({'caso': row.caso, 'url_descartada': row.url, 'titular_descartado': original.titular,
                    'etiqueta_referencia_original': original.etiqueta, 'particion': 'train',
                    'url_reemplazo': new['url'], 'titular_reemplazo': new['titular'],
                    'motivo_humano': row.observacion, 'fecha': now()})

assert set(splits[splits.particion == 'test'].url) == test_before
assert set(splits[splits.particion == 'validacion'].url) == val_before
assert len(data) == 400 and not data.url.duplicated().any() and data.etiqueta.value_counts().eq(100).all()
checked = data.merge(splits, on='url', validate='one_to_one')
assert checked.groupby(['particion', 'etiqueta']).size().to_dict() == {
    (partition, label): count for partition, count in [('train', 70), ('validacion', 15), ('test', 15)]
    for label in data.etiqueta.unique()}
data[COLUMNS].to_csv(ROOT / 'datos/noticias.csv', index=False, encoding='utf-8')
splits.to_csv(ROOT / 'datos/particiones.csv', index=False, encoding='utf-8')
pd.DataFrame(records).to_csv(corrections_path, index=False, encoding='utf-8')
discarded = pd.read_csv(ROOT / 'datos/descartes.csv', keep_default_na=False)
extra = pd.DataFrame([{'url': r['url_descartada'], 'titular': r['titular_descartado'],
                       'motivo': 'auditoria_humana_fuera_de_alcance'} for r in records])
pd.concat([discarded, extra], ignore_index=True).to_csv(ROOT / 'datos/descartes.csv', index=False, encoding='utf-8')
metadata.update(sha256_dataset=hashlib.sha256((ROOT / 'datos/noticias.csv').read_text(encoding='utf-8').encode()).hexdigest(),
                sha256_dataset_antes_auditoria=digest_before, fecha_correccion_humana=now(), correcciones_train=len(records),
                nota_particiones='Split inicial estratificado random_state=42; dos reemplazos de la misma categoría solo en train. Validación, baseline de 40 y test no cambian.')
metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
summary_path = ROOT / 'datos/resumen_recoleccion.json'
summary = json.loads(summary_path.read_text(encoding='utf-8'))
summary['fecha_recoleccion_inicial'] = summary['fecha_descarga']
summary['fecha_descarga'] = now()
summary['correcciones_auditoria_humana'] = len(records)
summary['descartes']['auditoria_humana_fuera_de_alcance'] = len(records)
summary['fecha_min'], summary['fecha_max'] = data.fecha.min(), data.fecha.max()
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(pd.DataFrame(records)[['caso', 'particion', 'titular_reemplazo']].to_string(index=False), flush=True)
print('400 noticias, cuotas y particiones conservadas. Los dos casos descartados permanecen en la auditoría original de 20.', flush=True)
