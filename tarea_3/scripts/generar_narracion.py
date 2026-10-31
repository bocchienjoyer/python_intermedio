"""Sintetiza las seis escenas con una referencia de voz propia mantenida en privado.

API: documentación oficial de QwenLM/Qwen3-TTS, modelo Base 0.6B.
Las salidas se guardan fuera de tarea_3, en una carpeta privada indicada al ejecutar.
"""
from pathlib import Path
import argparse,json,os,re

RAIZ=Path(__file__).resolve().parents[1]
MODELO='Qwen/Qwen3-TTS-12Hz-0.6B-Base'
REVISION='5d83992436eae1d760afd27aff78a71d676296fc'

def marca(t):
    ms=round(t*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--referencia',type=Path,required=True)
    p.add_argument('--transcripcion',type=Path,required=True)
    p.add_argument('--salida',type=Path,required=True)
    args=p.parse_args()
    # Mantener tanto la referencia como las salidas biométricas fuera del árbol público.
    for ruta in [args.referencia,args.salida]:
        if ruta.resolve().is_relative_to(RAIZ.resolve()):
            raise ValueError('Usar una carpeta privada fuera de tarea_3 para voz y salidas.')
    os.environ.setdefault('HF_HOME',str(RAIZ.parent/'.cache/tarea3-modelos'))
    import torch
    import soundfile as sf
    import numpy as np
    from qwen_tts import Qwen3TTSModel
    audio,sr=sf.read(args.referencia)
    if not 15<=len(audio)/sr<=25:raise ValueError('La referencia debe durar entre 15 y 25 segundos.')
    transcripcion=args.transcripcion.read_text(encoding='utf-8').strip()
    if not transcripcion:raise ValueError('La transcripción exacta de la referencia es necesaria.')
    device='cuda:0' if torch.cuda.is_available() else 'cpu'
    model=Qwen3TTSModel.from_pretrained(MODELO,revision=REVISION,device_map=device,
                                     dtype=torch.float16 if device.startswith('cuda') else torch.float32,
                                     attn_implementation='eager')
    prompt=model.create_voice_clone_prompt(ref_audio=str(args.referencia),ref_text=transcripcion,x_vector_only_mode=False)
    guion=json.loads((RAIZ/'reel/guion.json').read_text(encoding='utf-8'))
    args.salida.mkdir(parents=True,exist_ok=True)
    trozos=[];tiempos=[];inicio=0;subtitulos=[];tasa_comun=None
    for i,escena in enumerate(guion['escenas']):
        inicio_escena=inicio;fragmentos=[]
        # Cada subtítulo reproduce una oración completa y usa su duración sintetizada.
        frases=re.split(r'(?<=[.!?])\s+',escena['narracion'].strip())
        for j,frase in enumerate(frases):
            wavs,tasa=model.generate_voice_clone(text=frase,language='Spanish',voice_clone_prompt=prompt)
            if tasa_comun is None:tasa_comun=tasa
            if tasa!=tasa_comun:raise ValueError('La frecuencia de muestreo debe ser constante.')
            fragmento=np.asarray(wavs[0],dtype=np.float32).reshape(-1)
            pausa=.3 if j==len(frases)-1 else .18
            fragmento=np.concatenate([fragmento,np.zeros(round(pausa*tasa),dtype=np.float32)])
            fin=inicio+len(fragmento)/tasa
            subtitulos.append(f'{len(subtitulos)+1}\n{marca(inicio)} --> {marca(fin)}\n{frase}\n')
            inicio=fin;fragmentos.append(fragmento)
        voz=np.concatenate(fragmentos)
        sf.write(args.salida/f'escena_{i+1:02}.wav',voz,tasa)
        duracion=inicio-inicio_escena;tiempos.append({'inicio':inicio_escena,'fin':inicio});trozos.append(voz)
        print('Escena',i+1,round(duracion,2),'segundos',flush=True)
    sf.write(args.salida/'narracion.wav',np.concatenate(trozos),tasa)
    (args.salida/'tiempos_escenas.json').write_text(json.dumps(tiempos,indent=2),encoding='utf-8')
    (args.salida/'subtitulos.srt').write_text('\n'.join(subtitulos),encoding='utf-8')
    (args.salida/'modelo.json').write_text(json.dumps({'modelo':MODELO,'revision':REVISION,'device':device,
        'sample_rate':tasa,'segundos':inicio,'fuente_api':'https://github.com/QwenLM/Qwen3-TTS',
        'torch':torch.__version__},indent=2),encoding='utf-8')
    print('Duración total',round(inicio,2),'s. Revisar pronunciación y subtítulos antes del montaje final.')
    if not 45<=inicio<=75:print('La narración requiere ajustar ritmo o guion para cumplir 45–75 s.')

if __name__=='__main__':main()
