"""Prueba funcional del dashboard y su clasificador real con Streamlit AppTest."""

import json
from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=120).run()
assert not app.exception, app.exception
assert [m.value for m in app.metric] == ['400', '0.820', '65%']
assert len(app.dataframe[0].value) == 400
app.sidebar.multiselect[1].set_value(['deportes']).run()
assert not app.exception
assert len(app.dataframe[0].value) == 100
assert set(app.dataframe[0].value['etiqueta']) == {'Deportes'}
app.sidebar.multiselect[0].set_value([]).run()
assert not app.exception and len(app.dataframe[0].value) == 0 and len(app.info) >= 1
app.sidebar.multiselect[0].set_value(['La Republica']).run()
app.sidebar.multiselect[1].set_value([]).run()
assert not app.exception and len(app.dataframe[0].value) == 0
app.button[0].click().run()
assert not app.exception and any('Escribe un titular' in w.value for w in app.warning)
app.text_area[0].set_value('La selección peruana de fútbol ganó la final del campeonato').run()
app.button[0].click().run()
assert not app.exception, app.exception
assert len(app.success) == 1 and app.success[0].value in ['Política', 'Economía', 'Deportes', 'Ciencia y tecnología']
assert len(app.metric) == 4 and app.metric[3].value.endswith('%')
scores = app.dataframe[-1].value
assert len(scores) == 4 and abs(scores.Probabilidad.sum() - 1) < 1e-5
result = {'estado': 'correcto', 'herramienta': 'Streamlit AppTest',
          'controles': ['400 noticias y métricas reales', 'filtro deportes: 100', 'medio vacío: 0',
                       'categorías vacías: 0', 'titular vacío: aviso', 'inferencia real CPU y cuatro probabilidades'],
          'titular_prueba': app.text_area[0].value, 'prediccion': app.success[0].value,
          'probabilidad_mostrada': app.metric[3].value}
(ROOT / 'resultados/verificacion_app.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
