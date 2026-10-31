 'use strict';
const $=id=>document.getElementById(id);
const nf=new Intl.NumberFormat('es-PE'),dec=new Intl.NumberFormat('es-PE',{maximumFractionDigits:1});
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=s=>String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/^P\. C\. DEL CALLAO$/,'CALLAO');
const etiquetaPresupuesto=o=>({con_asignacion:'Con presupuesto para 2026',sin_asignacion_registrada:'Sin presupuesto registrado para 2026',sin_cui:'Presupuesto no verificable'})[o.estado_presupuesto];
let obras=[],mapa,seleccion=[],limite=8;
const ids=['departamento','tipo','avance','pim','anio'];
const tramos=[['tramo1','De 0 a 25 %'],['tramo2','Más de 25 a 50 %'],['tramo3','Más de 50 a 75 %'],['tramo4','Más de 75 a 90 %'],['tramo5','Más de 90 % (sin 100 %)'],['cien','100 % reportado'],['sin','Sin avance declarado']];
function tramo(avance){return avance===null?'sin':avance===100?'cien':avance>90?'tramo5':avance>75?'tramo4':avance>50?'tramo3':avance>25?'tramo2':'tramo1';}
function agrupar(d,c){const m=new Map();d.forEach(x=>m.set(x[c]??'Sin dato',(m.get(x[c]??'Sin dato')||0)+1));return [...m].sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0])));}
function filtrar(){const v=Object.fromEntries(ids.map(id=>[id,$(id).value]));return obras.filter(o=>(!v.departamento||o.departamento===v.departamento)&&(!v.tipo||o.tipo_obra===v.tipo)&&(!v.pim||o.estado_presupuesto===v.pim)&&(!v.avance||(v.avance==='alto'?o.avance>90:tramo(o.avance)===v.avance))&&(!v.anio||(v.anio==='sin'?o.anio_inicio===null:v.anio==='hasta2015'?o.anio_inicio!==null&&o.anio_inicio<=2015:o.anio_inicio===Number(v.anio))));}
function barras(id,datos,destacado=''){const max=Math.max(1,...datos.map(x=>x[1]));$(id).innerHTML=datos.length?datos.map(([nombre,n])=>`<div class="barra ${nombre===destacado?'destacada':''}"><div class="etiqueta"><span>${esc(nombre)}</span><strong>${nf.format(n)}</strong></div><div class="riel" role="img" aria-label="${esc(nombre)}: ${n} obras"><div class="relleno" style="width:${100*n/max}%"></div></div></div>`).join(''):'<p class="vacio">No hay obras para esta selección.</p>';}
function dibujarMapa(d){const cuentas=new Map(agrupar(d,'departamento').map(([k,v])=>[norm(k),v]));const max=Math.max(1,...cuentas.values());const coords=mapa.features.flatMap(f=>f.geometry.type==='Polygon'?f.geometry.coordinates.flat():f.geometry.coordinates.flat(2));const xs=coords.map(p=>p[0]),ys=coords.map(p=>p[1]);const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys),sx=330/(xmax-xmin),sy=330/(ymax-ymin),scale=Math.min(sx,sy),xp=x=>(x-xmin)*scale+20,yp=y=>(ymax-y)*scale+10;const paths=mapa.features.map(f=>{const nombre=f.properties.NOMBDEP,n=cuentas.get(norm(nombre))||0,polys=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;const path=polys.map(p=>p.map(r=>r.map((v,i)=>(i?'L':'M')+xp(v[0]).toFixed(2)+','+yp(v[1]).toFixed(2)).join('')+'Z').join('')).join('');const light=n?90-61*n/max:94;return `<path class="departamento" d="${path}" fill="hsl(151 32% ${light}%)" data-nombre="${esc(nombre)}" tabindex="0" role="button" aria-label="${esc(nombre)}: ${n} obras. Filtrar"><title>${esc(nombre)}: ${nf.format(n)} obras</title></path>`;});$('mapa').innerHTML=`<svg viewBox="0 0 ${(xmax-xmin)*scale+40} ${(ymax-ymin)*scale+20}" role="group" aria-label="Mapa de obras por departamento">${paths.join('')}</svg>`;$('mapa').querySelectorAll('path').forEach(p=>{const elegir=()=>{const valor=[...$('departamento').options].find(o=>norm(o.value)===norm(p.dataset.nombre));if(valor){$('departamento').value=valor.value;actualizar();}};p.addEventListener('click',elegir);p.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();elegir();}});});}

function buscarRegistros(){
    const q=$('buscar').value.trim();
    if(q.length<2){$('resultados').innerHTML='';$('estado-busqueda').textContent='Escribe al menos dos caracteres para buscar dentro de la selección de arriba.';$('mas').hidden=true;return;}
    const datos=seleccion.filter(o=>/^\d+$/.test(q)?String(o.infobras)===q:norm([o.obra,o.entidad].join(' ')).includes(norm(q)));
    const visibles=datos.slice(0,limite);
    $('resultados').innerHTML=visibles.map(o=>`<article class="resultado"><h3>${esc(o.obra)}</h3><p>${esc(o.entidad)} · ${esc(o.departamento)} / ${esc(o.distrito||'Distrito no declarado')}</p><p>Avance: ${o.avance===null?'sin dato':dec.format(o.avance)+' %'} · ${etiquetaPresupuesto(o)}</p><small>INFOBRAS ${esc(o.infobras)}</small>${o.url_informe&&/^https:\/\/ofi5\.mef\.gob\.pe\//.test(o.url_informe)?`<a href="${esc(o.url_informe)}" target="_blank" rel="noopener">Informe situacional ↗</a>`:''}</article>`).join('');
    $('estado-busqueda').textContent=datos.length?`${nf.format(datos.length)} ${datos.length===1?'coincidencia':'coincidencias'} · Mostrando ${nf.format(visibles.length)} · Búsqueda dentro de la selección de arriba.`:'No hay coincidencias en esta selección. Prueba otro nombre o restablece los filtros.';
    $('mas').hidden=limite>=datos.length;
}
function actualizar(){
    seleccion=filtrar();limite=8;
    const n=seleccion.length,alto=seleccion.filter(o=>o.avance>90).length,sin=seleccion.filter(o=>o.estado_presupuesto==='sin_asignacion_registrada').length,conDato=seleccion.filter(o=>o.estado_presupuesto!=='sin_cui').length,dep=new Set(seleccion.map(o=>o.departamento)).size;
    const k=[['Obras seleccionadas',nf.format(n),'del inventario nacional'],['Más del 90 % de avance',nf.format(alto),'Avance físico reportado'],['Sin presupuesto para 2026',nf.format(sin),conDato?'Asignación registrada al corte':'Sin información verificable en esta selección'],['Departamentos',nf.format(dep),'En la selección actual']];
    $('kpis').innerHTML=k.map(([a,b,c])=>`<article class="kpi"><span>${a}</span><strong>${b}</strong><small>${c}</small></article>`).join('');
    $('estado').textContent=`${nf.format(n)} obras seleccionadas · Los indicadores y gráficos responden a los filtros`;
    barras('tipos',agrupar(seleccion,'tipo_obra'));
    const conteos=new Map(tramos.map(([k])=>[k,0]));seleccion.forEach(o=>conteos.set(tramo(o.avance),conteos.get(tramo(o.avance))+1));
    barras('distribucion',tramos.map(([k,n])=>[n,conteos.get(k)]),'100 % reportado');
    const causas=agrupar(seleccion,'causa'),principal=causas.slice(0,7);if(causas.length>7)principal.push(['Resto de causas',causas.slice(7).reduce((s,x)=>s+x[1],0)]);
    barras('causas',principal);dibujarMapa(seleccion);buscarRegistros();
    $('alcance-descarga').textContent=`CSV con las ${nf.format(n)} obras seleccionadas arriba. La búsqueda de casos no modifica la descarga.`;
}
function descargar(){
    const campos=['infobras','cui','estado_presupuesto','obra','entidad','departamento','provincia','distrito','tipo_obra','anio_inicio','avance','pim_2026','causa'];
    const valor=v=>'"'+String(v??'').replace(/^[=+@-]/,"'$&").replace(/"/g,'""')+'"';
    const contenido='\ufeff'+[campos.join(','),...seleccion.map(o=>campos.map(c=>valor(o[c])).join(','))].join('\r\n');
    const u=URL.createObjectURL(new Blob([contenido],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=u;a.download='obras_paralizadas_seleccion_2026-06.csv';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);
}
async function iniciar(){try{
    const respuestas=await Promise.all(['data/obras.json','data/departamentos.geojson','data/hallazgos.json'].map(async u=>{const r=await fetch(u);if(!r.ok)throw Error('No se pudo cargar '+u);return r.json();}));
    let hallazgos;[obras,mapa,hallazgos]=respuestas;
    $('hero-obras').textContent=nf.format(obras.filter(o=>o.avance>90).length);
    $('hero-presupuesto').textContent=nf.format(obras.filter(o=>o.avance>90&&o.estado_presupuesto==='sin_asignacion_registrada').length);
    $('hallazgo-cien').textContent=nf.format(hallazgos.reportan_cien);$('hallazgo-antiguas').textContent=nf.format(hallazgos.inicio_hasta_2015);
    $('hallazgo-contratos').textContent=nf.format(hallazgos.causas_reportadas['INCUMPLIMIENTO DE CONTRATO']);
    for(const[id,col]of [['departamento','departamento'],['tipo','tipo_obra']]){[...new Set(obras.map(o=>o[col]))].sort((a,b)=>a.localeCompare(b,'es')).forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;$(id).append(o);});}
    [...new Set(obras.map(o=>o.anio_inicio).filter(a=>a!==null&&a>2015))].sort((a,b)=>a-b).forEach(a=>{const opcion=document.createElement('option');opcion.value=String(a);opcion.textContent=String(a);$('anio').insertBefore(opcion,$('anio').lastElementChild);});
    ids.forEach(id=>$(id).addEventListener('change',actualizar));
    $('reiniciar').onclick=()=>{ids.forEach(id=>$(id).value='');actualizar();};
    $('buscar').addEventListener('input',()=>{limite=8;buscarRegistros();});
    $('descargar').onclick=descargar;$('mas').onclick=()=>{limite+=8;buscarRegistros();};
    $('ver-cien').onclick=()=>{ids.forEach(id=>$(id).value='');$('avance').value='cien';actualizar();$('titulo-explorar').scrollIntoView({behavior:'smooth',block:'start'});};
    $('ver-antiguas').onclick=()=>{ids.forEach(id=>$(id).value='');$('anio').value='hasta2015';$('avance').value='alto';actualizar();$('titulo-explorar').scrollIntoView({behavior:'smooth',block:'start'});};
    actualizar();
}catch(e){$('estado').textContent='No se pudieron cargar los datos. Recarga la página o consulta el repositorio del proyecto.';console.error(e);}}
iniciar();
