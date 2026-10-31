# Créditos audiovisuales

- Datos: Contraloría General de la República, informe y Anexo 1 de obras paralizadas al 30 de junio de 2026.
- Interpretación de continuidad presupuestaria: OCDE, *OECD Economic Surveys: Peru 2025*, capítulo 1; Banco Mundial, *Peru: Seizing Opportunities for Growth and Prosperity* (2025), capítulo 4, párrafos 185 y 189–192. Enlaces completos en `reel/guion.json`. El mecanismo general no se atribuye como causa a cada obra.
- Cartografía referencial: servicio del MEF, atribución INEI en los metadatos de la capa departamental.
- Ilustración de continuidad: dibujo conceptual original de financiamiento, construcción y servicio público, generado por código; no representa un caso particular del inventario.
- Gráficos y composición: elaboración a partir de los datos oficiales mediante `scripts/generar_reel.py`.
- Capturas: dashboard Obras que esperan, de Jose Pablo Navarro Nateros.
- Narración: generada con [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), modelo Base 0.6B, a partir de una grabación de voz propia de 19,84 segundos. La referencia se mantiene en privado.
- Música: composición instrumental original mediante síntesis de ondas sinusoidales en `scripts/generar_reel.py`. Sin muestras ni grabaciones de terceros. Código y composición disponibles para reutilización bajo CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/.
- Tipografías: fuentes del sistema operativo; no se redistribuyen sus archivos.

`reel.mp4` incorpora narración IA, música original, subtítulos y un aviso visible del origen de la voz.

La generación de voz utiliza un entorno separado con `reel/requirements_voz.txt`. El montaje requiere `reel/requirements.txt`. `scripts/generar_narracion.py` sintetiza por oraciones y guarda fragmentos en una caché privada para reanudar sin repetir los que coinciden en texto, referencia y parámetros. Produce un WAV por escena, uno concatenado, los tiempos reales y un SRT con el texto pronunciado. El montaje recibe `--narracion`, `--tiempos` y `--subtitulos`; conserva los tiempos del SRT y comprueba que cubran el audio. La mezcla limita la música a un nivel RMS al menos 20 dB inferior al de la narración. El reel incorpora dos capturas del dashboard en el cierre.
