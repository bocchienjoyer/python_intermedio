# Créditos audiovisuales

- Datos: Contraloría General de la República, informe y Anexo 1 de obras paralizadas al 30 de junio de 2026.
- Interpretación de continuidad presupuestaria: OCDE, *OECD Economic Surveys: Peru 2025*, capítulo 1; Banco Mundial, *Peru: Seizing Opportunities for Growth and Prosperity* (2025), capítulo 4, párrafos 185 y 189–192. Enlaces completos en `reel/guion.json`. El mecanismo general no se atribuye como causa a cada obra.
- Cartografía referencial: servicio del MEF, atribución INEI en los metadatos de la capa departamental.
- Fotografía de fondo: Strange Happenings, «Abandoned Concrete Structure in Desert Landscape», Pexels, publicada el 2 de enero de 2026. [Fuente](https://www.pexels.com/photo/abandoned-concrete-structure-in-desert-landscape-35496428/) y [licencia Pexels](https://www.pexels.com/license/). Se conserva el archivo descargado en `obra_referencial.jpg`; en el video se aplica recorte, escala y transparencia. Es una fotografía referencial de EE. UU., no un caso identificado del inventario peruano.
- Billete, reloj y señal de pausa: elementos conceptuales originales dibujados y animados mediante `scripts/generar_reel.py`. La señal de pausa representa la clasificación reportada de paralización.
- Gráficos y composición: elaboración a partir de los datos oficiales mediante `scripts/generar_reel.py`.
- Capturas: dashboard Obras que esperan, de Jose Pablo Navarro Nateros.
- Narración: generada con [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), modelo Base 0.6B, a partir de una grabación de voz propia de 19,84 segundos. La referencia se mantiene en privado.
- Música: «Tech Live», Kevin MacLeod (incompetech.com), ISRC USUAN1700030, bajo [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). [Ficha del compositor](https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1700030) y [archivo original](https://incompetech.com/music/royalty-free/mp3-royaltyfree/Tech%20Live.mp3), recuperado el 31 de octubre de 2026 y conservado en `tech_live.mp3`. Se utiliza un fragmento desde el segundo 8, convertido a mono, con fundidos y reducción de volumen durante la narración. No se atribuye la autoría de esta música al proyecto.
- Tipografías: fuentes del sistema operativo; no se redistribuyen sus archivos.

`reel.mp4` incorpora narración IA, música con licencia abierta, subtítulos y un aviso visible del origen de la voz.

La generación de voz utiliza un entorno separado con `reel/requirements_voz.txt`. El montaje requiere `reel/requirements.txt`. `scripts/generar_narracion.py` sintetiza por oraciones y guarda fragmentos en una caché privada para reanudar sin repetir los que coinciden en texto, referencia y parámetros. Produce un WAV por escena, uno concatenado, los tiempos reales y un SRT con el texto pronunciado. El montaje recibe `--narracion`, `--tiempos` y `--subtitulos`; conserva los tiempos del SRT y comprueba que cubran el audio. La música parte de un nivel RMS 13 dB inferior al de la voz y se atenúa suavemente hasta un factor de 0,65 mientras hay habla; la mezcla completa se normaliza sin saturar. El reel incorpora dos capturas del dashboard en el cierre.
