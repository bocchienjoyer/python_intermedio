# Créditos audiovisuales

- Datos: Contraloría General de la República, informe y Anexo 1 de obras paralizadas al 30 de junio de 2026.
- Cartografía referencial: servicio del MEF, atribución INEI en los metadatos de la capa departamental.
- Gráficos y composición: elaboración a partir de los datos oficiales mediante `scripts/generar_reel.py`.
- Capturas: dashboard Obras que esperan, de Jose Pablo Navarro Nateros.
- Música: composición instrumental original mediante síntesis de ondas sinusoidales en `scripts/generar_reel.py`. Sin muestras ni grabaciones de terceros. Código y composición disponibles para reutilización bajo CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/.
- Tipografías: fuentes del sistema operativo; no se redistribuyen sus archivos.

`vista_previa.mp4` contiene música y subtítulos, con aviso visible de ausencia de narración. La narración final se incorpora con `--narracion` después de generar y verificar el audio IA a partir de una referencia de voz propia.

La generación de voz utiliza un entorno separado con `reel/requirements_voz.txt`. El montaje requiere `reel/requirements.txt`. `scripts/generar_narracion.py` produce un WAV por escena, un WAV concatenado y sus tiempos reales en una carpeta privada. El montaje recibe la narración y esos tiempos mediante `--narracion` y `--tiempos`; los subtítulos deben revisarse al escuchar el resultado. La mezcla limita la música a un nivel RMS al menos 20 dB inferior al de la narración.
