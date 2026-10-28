"""Genera una previsualización animada o monta una narración IA ya producida.

Sin --narracion produce vista_previa.mp4, identificada como video sin narración.
Con --narracion utiliza el audio proporcionado y ajusta las seis escenas a su duración.
La referencia de voz propia debe mantenerse fuera del repositorio público.
"""
from pathlib import Path
import argparse,json,math,textwrap,wave
from functools import lru_cache
import av
import numpy as np
from PIL import Image,ImageDraw,ImageFont

RAIZ=Path(__file__).resolve().parents[1]
REEL=RAIZ/'reel'
W,H,FPS,RATE=1080,1920,24,48000
PAPEL='#f6f4ec';TINTA='#163e36';VERDE='#196b54';NARANJA='#b94720';GRIS='#53655f'

@lru_cache(maxsize=64)
def fuente(n,serif=False):
    ruta=Path('C:/Windows/Fonts')/('georgia.ttf' if serif else 'arial.ttf')
    if not ruta.exists():ruta=Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSerif.ttf' if serif else 'DejaVuSans.ttf')
    return ImageFont.truetype(str(ruta),n)

def texto(draw,contenido,xy,tamano=44,color=TINTA,ancho=930,serif=False):
    font=fuente(tamano,serif);x,y=xy;palabras=contenido.split();linea=''
    for p in palabras:
        prueba=(linea+' '+p).strip()
        if draw.textlength(prueba,font=font)>ancho and linea:
            draw.text((x,y),linea,font=font,fill=color);y+=tamano*1.24;linea=p
        else:linea=prueba
    if linea:draw.text((x,y),linea,font=font,fill=color);y+=tamano*1.24
    return y

@lru_cache(maxsize=1)
def datos_mapa():
    geo=json.loads((RAIZ/'web/data/departamentos.geojson').read_text(encoding='utf-8'))
    datos=json.loads((RAIZ/'web/data/obras.json').read_text(encoding='utf-8'))
    cuentas={}
    for o in datos:
        if o['avance'] is not None and o['avance']>90:
            dep=o['departamento'].replace('P. C. DEL CALLAO','CALLAO');cuentas[dep]=cuentas.get(dep,0)+1
    # Geometrías referenciales del MEF. Conversión equirectangular para el gráfico.
    polys=[]
    for f in geo['features']:
        p=f['geometry']['coordinates'];p=[p] if f['geometry']['type']=='Polygon' else p
        polys.append((f['properties']['NOMBDEP'],p))
    puntos=[v for _,p in polys for pol in p for r in pol for v in r]
    xmin=min(v[0] for v in puntos);ymax=max(v[1] for v in puntos)
    return polys,cuentas,xmin,ymax

def mapa(im,d,fraccion=1):
    polys,cuentas,xmin,ymax=datos_mapa()
    escala=48;mx=max(cuentas.values())
    for nombre,poligonos in polys:
        n=cuentas.get(nombre,0);a=(n/mx)*fraccion;c=tuple(int(v) for v in np.array([220,233,214])*(1-a)+np.array([25,107,84])*a)
        for pol in poligonos:
            for ring in pol[:1]:
                vertices=[(180+(v[0]-xmin)*escala,570+(ymax-v[1])*escala) for v in ring]
                d.polygon(vertices,fill=c,outline=PAPEL,width=2)

def escena(numero,t,duracion,guion,narrada):
    im=Image.new('RGB',(W,H),PAPEL);d=ImageDraw.Draw(im)
    d.text((72,80),'OBRAS QUE ESPERAN / PERÚ',font=fuente(26),fill=VERDE)
    d.line((72,135,1008,135),fill='#c5d3be',width=2)
    titulo=guion['escenas'][numero]['titulo'];texto(d,titulo,(72,205),78,serif=True)
    anim=min(1,max(0,t/2))
    if numero in [0,1]:
        mapa(im,d,anim)
        d.text((700,525),str(round(281*anim)),font=fuente(118,True),fill=NARANJA)
        texto(d,'obras con más de 90 % de avance reportado',(700,680),34,ancho=300)
        texto(d,'2.262 obras en el inventario nacional',(72,1430),36)
    elif numero==2:
        d.text((72,480),str(round(169*anim)),font=fuente(190,True),fill=NARANJA)
        texto(d,'de 281 obras de mayor avance',(72,710),47)
        d.rounded_rectangle((72,880,1008,1030),radius=10,fill='#d9e4d3')
        d.rounded_rectangle((72,880,72+936*(169/281)*anim,1030),radius=10,fill=VERDE)
        texto(d,'Sin PIM positivo: 169 (60,1 %)',(72,1080),39)
        texto(d,'Con PIM positivo: 112 (39,9 %)',(72,1140),39)
        texto(d,'Presupuesto registrado para 2026, no gasto ejecutado.',(72,1320),34,color=GRIS)
    elif numero==3:
        datos=[('Vivienda, construcción y saneamiento',79),('Transportes y comunicaciones',57),('Educación y cultura',49),('Agricultura',41),('Otros tipos de obra',55)]
        for k,(nombre,n) in enumerate(datos):
            y=520+k*175;texto(d,nombre,(72,y),34,ancho=790);d.text((930,y),str(n),font=fuente(38),fill=TINTA)
            d.rounded_rectangle((72,y+70,72+900*n/79*anim,y+108),radius=4,fill=VERDE if k<2 else '#9eb7a1')
        texto(d,'136 de 281 · 48,4 % en los dos primeros tipos',(72,1480),40,color=NARANJA)
    elif numero==4:
        d.text((72,475),'23',font=fuente(190,True),fill=NARANJA)
        texto(d,'reportan 100 % y siguen en el inventario',(72,710),54,serif=True)
        d.line((72,970,1008,970),fill='#b7c8af',width=3)
        texto(d,'AVANCE FÍSICO',(72,1040),32,color=VERDE)
        texto(d,'Describe el progreso reportado de la construcción.',(72,1110),42)
        texto(d,'PUESTA EN SERVICIO',(72,1290),32,color=VERDE)
        texto(d,'Requiere verificación adicional de funcionamiento.',(72,1360),42)
    else:
        captura=REEL/'recursos/dashboard_general.png'
        if captura.exists():
            shot=Image.open(captura).convert('RGB');shot.thumbnail((936,650));im.paste(shot,(72,450))
        texto(d,'¿Qué deberíamos exigir para que una obra deje de esperar?',(72,1150),66,serif=True)
        texto(d,'Explora los datos y sus fuentes en el dashboard.',(72,1470),35,color=VERDE)
    # Subtítulos de la maqueta, ajustados por escena. Se recalculan al incorporar narración.
    frase=guion['escenas'][numero]['subtitulos'][min(1,int(t/(duracion/2)))]
    d.rectangle((0,1600,W,1790),fill=TINTA);texto(d,frase,(72,1630),38,color=PAPEL)
    d.text((72,1820),'Fuente: Contraloría · corte 30/06/2026',font=fuente(25),fill=GRIS)
    aviso='Voz generada con IA a partir de voz propia' if narrada else 'VISTA PREVIA · SIN NARRACIÓN'
    d.text((72,1855),'Gráficos y música: elaboración propia',font=fuente(21),fill=GRIS)
    d.text((72,1883),aviso,font=fuente(20),fill=NARANJA)
    d.rectangle((0,1908,int(W*(numero+t/duracion)/6),1920),fill=NARANJA)
    return im

def musica(segundos):
    n=round(segundos*RATE);audio=np.zeros(n,dtype=np.float32)
    for i,inicio in enumerate(np.arange(0,segundos,2.5)):
        largo=min(round(2.3*RATE),n-round(inicio*RATE));t=np.arange(largo)/RATE
        frecuencia=[220,261.6256,329.6276,293.6648,246.9417,196][i%6]
        env=np.minimum(t/.15,1)*np.maximum(0,1-t/2.3)**2
        nota=(np.sin(2*np.pi*frecuencia*t)+.3*np.sin(2*np.pi*2*frecuencia*t))*env*.014
        start=round(inicio*RATE);audio[start:start+largo]+=nota.astype(np.float32)
    return audio

def leer_voz(path):
    partes=[];res=av.AudioResampler(format='s16',layout='mono',rate=RATE)
    with av.open(str(path)) as c:
        for f in c.decode(audio=0):
            for x in res.resample(f):partes.append(x.to_ndarray().reshape(-1).astype(np.float32)/32768)
        for x in res.resample(None):partes.append(x.to_ndarray().reshape(-1).astype(np.float32)/32768)
    return np.concatenate(partes)

def marca(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--narracion',type=Path);parser.add_argument('--tiempos',type=Path);parser.add_argument('--fps',type=int,default=24);args=parser.parse_args()
    guion=json.loads((REEL/'guion.json').read_text(encoding='utf-8'))
    voz=leer_voz(args.narracion) if args.narracion else None
    segundos=len(voz)/RATE if voz is not None else 60
    if not 45<=segundos<=75:raise ValueError('La narración debe durar entre 45 y 75 segundos.')
    if voz is not None:
        if not args.tiempos:raise ValueError('Proporcionar --tiempos con los límites reales de las seis escenas.')
        tiempos=json.loads(args.tiempos.read_text(encoding='utf-8'))
        if len(tiempos)!=6 or abs(tiempos[0]['inicio'])>.01 or abs(tiempos[-1]['fin']-segundos)>.1:
            raise ValueError('Los tiempos no corresponden a la narración completa.')
        if any(e['fin']<=e['inicio'] for e in tiempos) or any(abs(tiempos[i]['inicio']-tiempos[i-1]['fin'])>.01 for i in range(1,6)):
            raise ValueError('Las escenas deben ser consecutivas y tener duración positiva.')
    else:tiempos=[{'inicio':i*10,'fin':(i+1)*10} for i in range(6)]
    audio=musica(segundos)
    if voz is not None:audio+=voz
    audio=np.clip(audio,-.98,.98);salida=REEL/('reel.mp4' if voz is not None else 'vista_previa.mp4')
    recursos=REEL/'recursos';recursos.mkdir(exist_ok=True)
    with wave.open(str(recursos/'musica_original.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes((musica(segundos)*32767).astype('<i2').tobytes())
    with av.open(str(salida),'w') as cont:
        video=cont.add_stream('libx264',rate=args.fps);video.width=W;video.height=H;video.pix_fmt='yuv420p';video.options={'crf':'24','preset':'veryfast'}
        sonido=cont.add_stream('aac',rate=RATE);sonido.layout='mono';sonido.bit_rate=96000
        for i in range(round(segundos*args.fps)):
            ti=i/args.fps;num=next((j for j,e in enumerate(tiempos) if ti<e['fin']),5)
            duracion=tiempos[num]['fin']-tiempos[num]['inicio']
            im=escena(num,ti-tiempos[num]['inicio'],duracion,guion,voz is not None)
            if i%args.fps==0:
                if int(ti)%10==0:print('Segundo',round(ti),flush=True)
                if abs(ti-tiempos[num]['inicio'])<1:im.save(recursos/f'escena_{num+1:02}.png')
            frame=av.VideoFrame.from_ndarray(np.asarray(im),format='rgb24')
            for packet in video.encode(frame):cont.mux(packet)
        for packet in video.encode():cont.mux(packet)
        for inicio in range(0,len(audio),1024):
            chunk=(audio[inicio:inicio+1024]*32767).astype(np.int16).reshape(1,-1)
            frame=av.AudioFrame.from_ndarray(chunk,format='s16',layout='mono');frame.sample_rate=RATE;frame.pts=inicio
            for packet in sonido.encode(frame):cont.mux(packet)
        for packet in sonido.encode():cont.mux(packet)
    srt=[]
    for i,e in enumerate(guion['escenas']):
        duracion=tiempos[i]['fin']-tiempos[i]['inicio']
        for j,frase in enumerate(e['subtitulos']):
            ini=tiempos[i]['inicio']+j*duracion/2;fin=ini+duracion/2
            srt.append(f'{len(srt)+1}\n{marca(ini)} --> {marca(fin)}\n{frase}\n')
    (REEL/'subtitulos.srt').write_text('\n'.join(srt),encoding='utf-8')
    print('Exportado',salida,round(segundos,2),'s',flush=True)

if __name__=='__main__':main()
