"""Sintetiza las seis escenas con una referencia de voz propia mantenida en privado.

API: documentación oficial de QwenLM/Qwen3-TTS, modelo Base 0.6B.
Las salidas se guardan fuera de tarea_3, en una carpeta privada indicada al ejecutar.
"""
from pathlib import Path
import argparse,hashlib,json,os,re

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
    for ruta in [args.referencia,args.transcripcion,args.salida]:
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
    if device=='cpu':torch.set_num_threads(min(4,os.cpu_count() or 1))
    # La ruta local evita consultas de metadatos del procesador con pesos ya disponibles.
    cache_modelo=Path(os.environ['HF_HOME'])/'hub/models--Qwen--Qwen3-TTS-12Hz-0.6B-Base/snapshots'/REVISION
    origen=str(cache_modelo.resolve()) if cache_modelo.is_dir() else MODELO
    print('Cargando modelo de voz en',device,flush=True)
    model=Qwen3TTSModel.from_pretrained(origen,revision=REVISION,device_map=device,
                                     dtype=torch.float16 if device.startswith('cuda') else torch.float32,
                                     attn_implementation='eager')
    print('Preparando referencia de voz',flush=True)
    prompt=model.create_voice_clone_prompt(ref_audio=str(args.referencia),ref_text=transcripcion,x_vector_only_mode=False)
    guion=json.loads((RAIZ/'reel/guion.json').read_text(encoding='utf-8'))
    args.salida.mkdir(parents=True,exist_ok=True)
    cache_fragmentos=args.salida/'fragmentos';cache_fragmentos.mkdir(exist_ok=True)
    firma_referencia=hashlib.sha256(args.referencia.read_bytes()).hexdigest()
    trozos=[];tiempos=[];inicio=0;subtitulos=[];tasa_comun=None
    for i,escena in enumerate(guion['escenas']):
        inicio_escena=inicio;fragmentos=[]
        # Cada subtítulo reproduce una oración completa y usa su duración sintetizada.
        frases=re.split(r'(?<=[.!?])\s+',escena['narracion'].strip())
        for j,frase in enumerate(frases):
            semilla=20261031+i*10+j
            metadatos={'modelo':MODELO,'revision':REVISION,'referencia_sha256':firma_referencia,
                       'referencia_texto':transcripcion,'texto':frase,'semilla':semilla,
                       'non_streaming_mode':True,'max_new_tokens':512,'qwen_tts':'0.1.1'}
            clave=hashlib.sha256(json.dumps(metadatos,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            archivo=cache_fragmentos/f'{clave}.wav';ficha=archivo.with_suffix('.json')
            if archivo.exists() and ficha.exists() and json.loads(ficha.read_text(encoding='utf-8'))==metadatos:
                fragmento,tasa=sf.read(archivo,dtype='float32')
                print('Reutilizado fragmento',i+1,j+1,flush=True)
            else:
                print('Generando fragmento',i+1,j+1,flush=True)
                torch.manual_seed(semilla)
                wavs,tasa=model.generate_voice_clone(text=frase,language='Spanish',voice_clone_prompt=prompt,
                                                     non_streaming_mode=True,max_new_tokens=512)
                fragmento=np.asarray(wavs[0],dtype=np.float32).reshape(-1)
                if not len(fragmento) or not np.isfinite(fragmento).all():raise ValueError('Audio generado inválido.')
                sf.write(archivo,fragmento,tasa,subtype='FLOAT')
                ficha.write_text(json.dumps(metadatos,ensure_ascii=False,indent=2),encoding='utf-8')
            if tasa_comun is None:tasa_comun=tasa
            if tasa!=tasa_comun:raise ValueError('La frecuencia de muestreo debe ser constante.')
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
        'torch':torch.__version__,'sintesis':'por oraciones, caché privada y semillas por fragmento',
        'non_streaming_mode':True,'max_new_tokens':512},indent=2),encoding='utf-8')
    print('Duración total',round(inicio,2),'s. Revisar pronunciación y subtítulos antes del montaje final.')
    if not 45<=inicio<=75:print('La narración requiere ajustar ritmo o guion para cumplir 45–75 s.')

if __name__=='__main__':main()
