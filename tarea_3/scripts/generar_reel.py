"""Genera una previsualización animada o monta una narración IA ya producida.

Sin --narracion produce vista_previa.mp4, identificada como video sin narración.
Con --narracion utiliza el audio proporcionado y ajusta las seis escenas a su duración.
La referencia de voz propia debe mantenerse fuera del repositorio público.
"""
from pathlib import Path
import argparse,json,re,wave
from functools import lru_cache
from fractions import Fraction
import av
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps

RAIZ=Path(__file__).resolve().parents[1]
REEL=RAIZ/'reel'
W,H,FPS,RATE=1080,1920,24,48000
PAPEL='#f6f4ec';TINTA='#163e36';VERDE='#196b54';NARANJA='#b94720';GRIS='#53655f'

@lru_cache(maxsize=64)
def fuente(n,serif=False,negrita=False):
    nombre=('georgiab.ttf' if negrita else 'georgia.ttf') if serif else ('arialbd.ttf' if negrita else 'arial.ttf')
    ruta=Path('C:/Windows/Fonts')/nombre
    if not ruta.exists():
        nombre=('DejaVuSerif' if serif else 'DejaVuSans')+('-Bold.ttf' if negrita else '.ttf')
        ruta=Path('/usr/share/fonts/truetype/dejavu')/nombre
    return ImageFont.truetype(str(ruta),n)

def lineas_texto(draw,contenido,font,ancho):
    lineas=[]
    for parrafo in contenido.split('\n'):
        linea=''
        for palabra in parrafo.split():
            prueba=(linea+' '+palabra).strip()
            if draw.textlength(prueba,font=font)>ancho and linea:
                lineas.append(linea);linea=palabra
            else:linea=prueba
        if linea:lineas.append(linea)
    return lineas

def centrado(draw,contenido,y,tamano=44,color=TINTA,ancho=936,serif=False,negrita=False):
    font=fuente(tamano,serif,negrita)
    for linea in lineas_texto(draw,contenido,font,ancho):
        draw.text((W/2,y),linea,font=font,fill=color,anchor='mt');y+=tamano*1.2
    return y

def entrada(im,contenido,y,t,desde,tamano,color=TINTA,ancho=936,serif=False):
    """Entrada breve con desplazamiento y transparencia, sin modificar la voz."""
    progreso=float(np.clip((t-desde)/.45,0,1))
    if progreso==0:return
    capa=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(capa)
    centrado(d,contenido,y+24*(1-progreso),tamano,color,ancho,serif,True)
    capa.putalpha(capa.getchannel('A').point(lambda a:round(a*progreso)))
    im.paste(capa,(0,0),capa)

def texto(draw,contenido,xy,tamano=44,color=TINTA,ancho=930,serif=False):
    font=fuente(tamano,serif);x,y=xy;palabras=contenido.split();linea=''
    for p in palabras:
        prueba=(linea+' '+p).strip()
        if draw.textlength(prueba,font=font)>ancho and linea:
            draw.text((x,y),linea,font=font,fill=color);y+=tamano*1.24;linea=p
        else:linea=prueba
    if linea:draw.text((x,y),linea,font=font,fill=color);y+=tamano*1.24
    return y

@lru_cache(maxsize=2)
def datos_mapa(solo_mayor90=True):
    geo=json.loads((RAIZ/'web/data/departamentos.geojson').read_text(encoding='utf-8'))
    datos=json.loads((RAIZ/'web/data/obras.json').read_text(encoding='utf-8'))
    cuentas={}
    for o in datos:
        if not solo_mayor90 or (o['avance'] is not None and o['avance']>90):
            dep=o['departamento'].replace('P. C. DEL CALLAO','CALLAO');cuentas[dep]=cuentas.get(dep,0)+1
    # Geometrías referenciales del MEF. Conversión equirectangular para el gráfico.
    polys=[]
    for f in geo['features']:
        p=f['geometry']['coordinates'];p=[p] if f['geometry']['type']=='Polygon' else p
        polys.append((f['properties']['NOMBDEP'],p))
    puntos=[v for _,p in polys for pol in p for r in pol for v in r]
    xmin=min(v[0] for v in puntos);ymax=max(v[1] for v in puntos)
    return polys,cuentas,xmin,ymax

def mapa(im,d,fraccion=1,solo_mayor90=True):
    polys,cuentas,xmin,ymax=datos_mapa(solo_mayor90)
    escala=44;mx=max(cuentas.values())
    for nombre,poligonos in polys:
        n=cuentas.get(nombre,0);a=(n/mx)*fraccion;c=tuple(int(v) for v in np.array([220,233,214])*(1-a)+np.array([25,107,84])*a)
        for pol in poligonos:
            for ring in pol[:1]:
                vertices=[(85+(v[0]-xmin)*escala,500+(ymax-v[1])*escala) for v in ring]
                d.polygon(vertices,fill=c,outline=PAPEL,width=2)

@lru_cache(maxsize=1)
def fondo_obra():
    """Fotografía de archivo, utilizada como fondo referencial con transparencia."""
    foto=Image.open(REEL/'recursos/obra_referencial.jpg').convert('RGB')
    foto=ImageOps.fit(foto,(W,1070),method=Image.Resampling.LANCZOS,centering=(.5,.52)).convert('RGBA')
    intensidad=.22*np.sin(np.linspace(0,np.pi,1070))**.7
    alfa=np.repeat((intensidad*255).astype(np.uint8)[:,None],W,axis=1)
    foto.putalpha(Image.fromarray(alfa));return foto

@lru_cache(maxsize=1)
def billete():
    im=Image.new('RGBA',(190,120),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle((8,20,182,100),radius=4,fill='#d9e4d3',outline=VERDE,width=5)
    d.rectangle((18,30,172,90),outline=VERDE,width=2)
    d.ellipse((69,31,122,89),fill=PAPEL,outline=VERDE,width=3)
    d.text((78,43),'S/',font=fuente(31),fill=VERDE)
    for x in [34,147]:
        d.ellipse((x-9,39,x+9,57),outline=VERDE,width=2)
        d.ellipse((x-9,64,x+9,82),outline=VERDE,width=2)
    return im

def continuidad_grafica(im,t):
    """Foto real de fondo, billete que se aleja y reloj de espera animado."""
    foto=fondo_obra();im.paste(foto,(0,330),foto)
    avance=np.clip((t-.2)/9,0,1)**1.15
    nota=billete().rotate(8*np.sin(t*1.8)-4,resample=Image.Resampling.BICUBIC,expand=True)
    cx=945+300*avance;cy=710-45*avance+6*np.sin(t*1.5)
    im.paste(nota,(round(cx-nota.width/2),round(cy-nota.height/2)),nota)
    d=ImageDraw.Draw(im)
    if t>=3.53:
        cx,cy,r=540,1175,63
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=PAPEL,outline=NARANJA,width=6)
        for angulo in [-np.pi/2,0,np.pi/2,np.pi]:
            d.line((cx+49*np.cos(angulo),cy+49*np.sin(angulo),cx+55*np.cos(angulo),cy+55*np.sin(angulo)),fill=NARANJA,width=4)
        for angulo,largo,grosor in [(-np.pi/2+.10*t,42,5),(-2.5+.025*t,28,7)]:
            d.line((cx,cy,cx+largo*np.cos(angulo),cy+largo*np.sin(angulo)),fill=NARANJA,width=grosor)
        d.ellipse((cx-5,cy-5,cx+5,cy+5),fill=NARANJA)
    centrado(d,'Foto referencial · EE. UU. · Strange Happenings / Pexels',1378,21,color='#7b8580')

def senal_pausa(d,t):
    """La señal representa la clasificación de paralización, no su causa."""
    radio=76+3*np.sin(t*2)
    d.line((180,945,420,945),fill='#d4dcd1',width=5)
    d.line((660,945,900,945),fill='#d4dcd1',width=5)
    d.ellipse((540-radio,945-radio,540+radio,945+radio),fill='#f3e4d9',outline=NARANJA,width=5)
    for x in [512,550]:d.rounded_rectangle((x,910,x+18,980),radius=4,fill=NARANJA)

@lru_cache(maxsize=2)
def captura_dashboard(nombre):
    with Image.open(REEL/'recursos'/nombre) as archivo:
        return ImageOps.contain(archivo.convert('RGB'),(936,810),method=Image.Resampling.LANCZOS)

def escena(numero,t,duracion,guion,narrada,subtitulo=None):
    im=Image.new('RGB',(W,H),PAPEL);d=ImageDraw.Draw(im)
    aviso='Voz generada con IA a partir de voz propia' if narrada else 'VISTA PREVIA · SIN NARRACIÓN'
    centrado(d,aviso,66,26,color='#7b8580')
    titulo=guion['escenas'][numero]['titulo']
    if numero in [0,1,3,5]:centrado(d,titulo,165,76 if numero in [0,5] else 86,serif=True,negrita=True)
    anim=min(1,max(0,t/2))
    if numero in [0,1]:
        mapa(im,d,anim,solo_mayor90=numero==1)
        total=2262 if numero==0 else 281
        d.text((855,615),str(round(total*anim)),font=fuente(112 if numero==0 else 142,True,True),fill=NARANJA,anchor='mt')
        descripcion='obras paralizadas en el inventario nacional' if numero==0 else 'obras con más de 90 % de avance físico'
        # La columna del dato queda fuera de la silueta del mapa.
        font=fuente(38)
        for j,linea in enumerate(lineas_texto(d,descripcion,font,285)):
            d.text((855,800+j*47),linea,font=font,fill=TINTA,anchor='mt')
        centrado(d,'Perú · corte al 30 de junio de 2026',1355,30,color=GRIS)
    elif numero==2:
        centrado(d,str(round(155*anim)),280,310,color=NARANJA,serif=True,negrita=True)
        centrado(d,'figuran sin presupuesto\npara 2026',665,66,negrita=True)
        d.rounded_rectangle((100,915,980,985),radius=12,fill='#d9e4d3')
        if anim>0:d.rounded_rectangle((100,915,100+880*(155/281)*anim,985),radius=12,fill=VERDE)
        centrado(d,'de 281 obras con más del 90 %\nde avance físico',1050,46)
        centrado(d,'Asignación registrada al 30 de junio de 2026',1270,28,color='#7b8580')
    elif numero==3:
        continuidad_grafica(im,t)
        centrado(d,'OCDE · PERÚ · 2025',345,32,color=VERDE)
        entrada(im,'Sin continuidad\nfinanciera…',480,t,0,90,serif=True)
        # «Genera demoras» comienza en 3,53 s de la voz conservada.
        entrada(im,'…la culminación\npuede demorarse.',850,t,3.53,80,color=NARANJA,serif=True)
    elif numero==4:
        centrado(d,'23',195,300,color=NARANJA,serif=True,negrita=True)
        centrado(d,'obras reportan',530,48)
        centrado(d,'100 %',605,132,serif=True,negrita=True)
        centrado(d,'de avance físico',775,48)
        senal_pausa(d,t)
        centrado(d,'y siguen',1050,46)
        d.rounded_rectangle((188,1140,892,1250),radius=18,fill=NARANJA)
        centrado(d,'PARALIZADAS',1160,66,color=PAPEL,negrita=True)
    else:
        nombre='dashboard_general.png' if t<duracion/2 else 'dashboard_exploracion.png'
        if (REEL/'recursos'/nombre).exists():
            shot=captura_dashboard(nombre)
            im.paste(shot,((W-shot.width)//2,500+(810-shot.height)//2))
        centrado(d,'Explora los datos y sus fuentes\nen el dashboard.',1320,40,color=VERDE,negrita=True)
    # El montaje narrado conserva los intervalos del audio; la maqueta usa referencias.
    frase=subtitulo if narrada else guion['escenas'][numero]['subtitulos'][min(1,int(t/(duracion/2)))]
    d.rounded_rectangle((40,1450,1040,1775),radius=22,fill=TINTA)
    tamano=48
    while len(lineas_texto(d,frase,fuente(tamano),900))*tamano*1.2>280:tamano-=1
    n_lineas=len(lineas_texto(d,frase,fuente(tamano),900))
    centrado(d,frase,1450+(325-n_lineas*tamano*1.2)/2,tamano,color=PAPEL,ancho=900)
    referencia='OCDE (2025) · Estudio económico de Perú' if numero==3 else 'Fuente: Contraloría · corte 30/06/2026'
    centrado(d,referencia,1820,25,color=GRIS)
    centrado(d,'Gráficos y música: elaboración propia',1858,21,color=GRIS)
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

def leer_subtitulos(path,segundos):
    def instante(s):
        h,m,s,ms=map(int,re.split('[:,]',s));return h*3600+m*60+s+ms/1000
    bloques=[]
    for bloque in re.split(r'\n\s*\n',path.read_text(encoding='utf-8-sig').strip()):
        lineas=bloque.splitlines()
        if len(lineas)<3:raise ValueError('Subtítulo incompleto.')
        inicio,fin=lineas[1].split(' --> ')
        bloques.append((instante(inicio),instante(fin),' '.join(lineas[2:])))
    if not bloques or abs(bloques[0][0])>.02 or abs(bloques[-1][1]-segundos)>.1:
        raise ValueError('Los subtítulos deben cubrir la narración completa.')
    if any(a<0 or b<=a or b>segundos+.1 for a,b,_ in bloques):raise ValueError('Tiempos de subtítulos inválidos.')
    if any(abs(bloques[i][0]-bloques[i-1][1])>.02 for i in range(1,len(bloques))):
        raise ValueError('Los subtítulos deben ser consecutivos y no solaparse.')
    return bloques

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--narracion',type=Path);parser.add_argument('--tiempos',type=Path);parser.add_argument('--subtitulos',type=Path);parser.add_argument('--fps',type=int,default=24);args=parser.parse_args()
    guion=json.loads((REEL/'guion.json').read_text(encoding='utf-8'))
    voz=leer_voz(args.narracion) if args.narracion else None
    segundos=len(voz)/RATE if voz is not None else 60
    if not 45<=segundos<=75:raise ValueError('La narración debe durar entre 45 y 75 segundos.')
    subtitulos_reales=[]
    if voz is not None:
        if not args.subtitulos:raise ValueError('Proporcionar --subtitulos con el SRT de la narración real.')
        subtitulos_reales=leer_subtitulos(args.subtitulos,segundos)
        if not args.tiempos:raise ValueError('Proporcionar --tiempos con los límites reales de las seis escenas.')
        tiempos=json.loads(args.tiempos.read_text(encoding='utf-8'))
        if len(tiempos)!=6 or abs(tiempos[0]['inicio'])>.01 or abs(tiempos[-1]['fin']-segundos)>.1:
            raise ValueError('Los tiempos no corresponden a la narración completa.')
        if any(e['fin']<=e['inicio'] for e in tiempos) or any(abs(tiempos[i]['inicio']-tiempos[i-1]['fin'])>.01 for i in range(1,6)):
            raise ValueError('Las escenas deben ser consecutivas y tener duración positiva.')
    else:tiempos=[{'inicio':i*10,'fin':(i+1)*10} for i in range(6)]
    audio=musica(segundos)
    if voz is not None:
        rms_voz=float(np.sqrt(np.mean(voz**2)))
        if rms_voz<1e-5:raise ValueError('La narración no contiene una señal de voz utilizable.')
        rms_musica=float(np.sqrt(np.mean(audio**2)))
        audio*=min(1,.1*rms_voz/max(rms_musica,1e-8))
        audio+=voz
    pico=float(np.max(np.abs(audio)))
    if pico>0:audio*=.95/pico
    salida=REEL/('reel.mp4' if voz is not None else 'vista_previa.mp4')
    recursos=REEL/'recursos';recursos.mkdir(exist_ok=True)
    with wave.open(str(recursos/'musica_original.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes((musica(segundos)*32767).astype('<i2').tobytes())
    with av.open(str(salida),'w',options={'movflags':'+faststart'}) as cont:
        video=cont.add_stream('libx264',rate=args.fps);video.width=W;video.height=H;video.pix_fmt='yuv420p';video.sample_aspect_ratio=Fraction(1,1);video.options={'crf':'24','preset':'veryfast'}
        sonido=cont.add_stream('aac',rate=RATE);sonido.layout='mono';sonido.bit_rate=96000
        for i in range(round(segundos*args.fps)):
            ti=i/args.fps;num=next((j for j,e in enumerate(tiempos) if ti<e['fin']),5)
            duracion=tiempos[num]['fin']-tiempos[num]['inicio']
            frase=next((texto for inicio,fin,texto in subtitulos_reales if inicio<=ti<fin),'')
            im=escena(num,ti-tiempos[num]['inicio'],duracion,guion,voz is not None,frase)
            if i%args.fps==0:
                if int(ti)%10==0:print('Segundo',round(ti),flush=True)
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
    contenido=args.subtitulos.read_text(encoding='utf-8-sig') if voz is not None else '\n'.join(srt)
    (REEL/'subtitulos.srt').write_text(contenido,encoding='utf-8')
    print('Exportado',salida,round(segundos,2),'s',flush=True)

if __name__=='__main__':main()
