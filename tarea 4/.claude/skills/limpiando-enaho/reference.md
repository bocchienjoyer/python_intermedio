# Procesamiento de ENAHO 2024

- Conservar los ceros iniciales de `conglome`, `vivienda`, `hogar` y `ubigeo`.
- Seleccionar residentes habituales con `((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))`.
- Unir personas y hogares por `conglome`, `vivienda` y `hogar` con `validate="m:1"`.
- Estimar la pobreza con los factores de expansión correspondientes a la unidad de análisis.
- Verificar cardinalidad, ponderadores, 108 664 residentes habituales y 25 códigos territoriales. Contrastar la pobreza nacional con 27,6 % y una tolerancia de 0,1 puntos porcentuales.
- Registrar las verificaciones en `salidas/validacion.txt` y detener el flujo ante un fallo esencial.
