// =====================================================================
//  pagina.h  -  Pagina web servida por el ESP32 del EMG
//  No usa internet: funciona conectado a la red WiFi del ESP32 (http://192.168.4.1).
//  La pagina es un ESPEJO de la maquina: muestra la senal (RMS) y el estado del juego,
//  graba la sesion en el navegador (CSV / PNG) y puede PEDIR una calibracion.
//  RECOLECCION SEMGIA: "Tomar muestra" -> formulario -> 24 s con indicaciones
//  (REPOSO 8 / CONTRAIGA 8 / REPOSO 8) -> descarga semgia_sample_*.json. Cada calibracion
//  terminada descarga semgia_calib_*.json. En el PC: python scripts/import_web.py
//  (repo SEMGIA) crea data/raw/sample_NNN/ y data/raw/calibration_EXX/.
//  Solo seudonimos (P001 / OP01 / E01): nunca nombres.
//  El HTML/JS se guarda en la memoria flash del ESP32 y el navegador lo ejecuta.
// =====================================================================
#pragma once

const char PAGINA_HTML[] PROGMEM = R"rawliteral(<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEMGIA EMG</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--tx:#e2e8f0;--mut:#94a3b8;--verde:#4ade80}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--tx);padding:12px;max-width:1100px;margin:auto}
h1{font-size:1.15rem;margin:4px 0 10px}
#banner{padding:12px;border-radius:10px;font-weight:700;text-align:center;margin-bottom:10px;background:var(--card);color:#0f172a}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-bottom:8px}
.c{background:var(--card);border-radius:10px;padding:10px}
.c small{color:var(--mut);display:block;font-size:.75rem;margin-bottom:2px}
.c b{font-size:1.35rem;font-variant-numeric:tabular-nums}
#ambito{color:var(--mut);display:block;margin:4px 0 6px}
canvas{width:100%;height:330px;border-radius:10px;display:block}
#cvR{height:200px;margin-top:8px}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
button,input{font:inherit;padding:10px 14px;border-radius:8px;border:0}
button{background:#334155;color:var(--tx);cursor:pointer}
button.p{background:#0284c7}button.g{background:#b91c1c}button.r{background:#7c2d12}
input,select{font:inherit;background:var(--card);color:var(--tx);flex:1;min-width:180px}
[hidden]{display:none!important}
/* Recoleccion SEMGIA */
#recol{margin:10px 0;border:2px solid #0284c7}
#recol h2,.caja h2{font-size:1rem;margin:0 0 8px}
.fila{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin-bottom:8px}
.fila label,.caja label{display:flex;flex-direction:column;font-size:.75rem;color:var(--mut);gap:2px}
.fila input{min-width:0;width:6.5em;flex:none;background:#0f172a;text-transform:uppercase}
#vCnt{font-size:1.35rem}
button.grande{font-size:1.2rem;padding:14px 22px;font-weight:700}
#msgRecol{display:block;min-height:1.2em}
.err{color:#f87171}.ok{color:var(--verde)}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:9;padding:12px}
.caja{background:var(--card);border-radius:12px;padding:16px;width:100%;max-width:520px;max-height:100%;overflow:auto}
.caja label{margin-bottom:8px}.caja input,.caja select{min-width:0;background:#0f172a;padding:8px;border-radius:6px;border:0}
.cue{position:fixed;inset:0;z-index:10;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;text-align:center;padding:16px}
#cueInfo{font-size:clamp(1rem,3.5vw,2rem);opacity:.9}
#cueTxt{font-size:clamp(3rem,16vw,12rem);font-weight:800;line-height:1.05}
#cueSeg{font-size:clamp(2.5rem,12vw,8rem);font-weight:700;font-variant-numeric:tabular-nums}
#cuePct{font-size:clamp(1rem,3.5vw,2rem);min-height:1.2em}
.prog{width:min(90vw,900px);height:14px;background:rgba(255,255,255,.25);border-radius:7px;margin:18px 0}
#cueBar{height:100%;width:0;background:#fff;border-radius:7px}
#cueStop{background:rgba(0,0,0,.35);color:#fff}
</style></head><body>
<h1>SEMGIA &middot; Monitor EMG</h1>
<div id="banner">Conectando&hellip;</div>
<div class="grid">
  <div class="c"><small>RMS actual (mV)</small><b id="vAct">&ndash;</b></div>
  <div class="c"><small>% contracci&oacute;n m&aacute;x.</small><b id="vPct">&ndash;</b></div>
  <div class="c"><small>RMS m&iacute;nimo (mV)</small><b id="vMin">&ndash;</b></div>
  <div class="c"><small>RMS m&aacute;ximo (mV)</small><b id="vMax">&ndash;</b></div>
  <div class="c"><small>RMS promedio (mV)</small><b id="vProm">&ndash;</b></div>
  <div class="c"><small>Activaciones</small><b id="vNAct">0</b></div>
  <div class="c"><small>Reposo / M&aacute;x. calib. (mV)</small><b id="vCal">&ndash;</b></div>
  <div class="c"><small>Contracci&oacute;n</small><b id="vEst">&ndash;</b></div>
</div>
<!-- Datos de la maquina (solo lectura: se cambian en la maquina) -->
<div class="grid">
  <div class="c"><small>Nivel &middot; tiempo (m&aacute;quina)</small><b id="vMaq">&ndash;</b></div>
  <div class="c"><small>Carga catapulta</small><b id="vCar">&ndash;</b></div>
  <div class="c"><small>Tiros</small><b id="vTiros">&ndash;</b></div>
  <div class="c"><small>Canastas / r&eacute;cord</small><b id="vPts">&ndash;</b></div>
</div>
<small id="ambito">Estad&iacute;sticas &uacute;ltimos 10 s</small>
<canvas id="cv"></canvas>
<small id="ambitoR" style="color:var(--mut);display:block;margin:8px 0 0">Se&ntilde;al EMG cruda del ADC (12 bits, sin offset para la gr&aacute;fica), 1000 muestras/s &middot; &uacute;ltimos 5 s</small>
<canvas id="cvR"></canvas>
<!-- Recoleccion de datos SEMGIA: una calibracion por colocacion, luego muestras de 24 s -->
<div class="c" id="recol">
  <h2>Recolecci&oacute;n de datos SEMGIA (solo seud&oacute;nimos, nunca nombres)</h2>
  <div class="fila">
    <label>Sujeto<input id="fSuj" placeholder="P001" maxlength="4" autocomplete="off"></label>
    <label>Operador<input id="fOp" placeholder="OP01" maxlength="4" autocomplete="off"></label>
    <label>Colocaci&oacute;n<input id="fPl" placeholder="E01" maxlength="3" autocomplete="off"></label>
    <div><small style="color:var(--mut);font-size:.75rem">Muestra</small><br><b id="vCnt">&ndash;</b>
      <button id="bCnt" title="Corregir el contador (p. ej. tras borrar una muestra mala)">&#9998;</button></div>
  </div>
  <div class="fila">
    <button class="r" id="bCal">1&middot; Calibrar colocaci&oacute;n</button>
    <button class="p grande" id="bMuestra">2&middot; &#9654; Tomar muestra (24 s)</button>
  </div>
  <small id="msgRecol"></small>
</div>
<div class="bar">
  <button class="p" id="bGrab">&#9679; Iniciar grabaci&oacute;n</button>
  <button id="bCsv">Descargar datos (CSV)</button>
  <button id="bPng">Descargar gr&aacute;fica (PNG)</button>
  <button id="bRaw">Descargar EMG 1 kHz (CSV)</button>
</div>
<!-- Formulario de la muestra (campos = METADATA_FIELDS de semgia/storage.py) -->
<div id="dlg" class="modal" hidden><div class="caja">
  <h2>Datos de la muestra</h2>
  <p id="dlgIds" style="margin:0 0 10px"></p>
  <label>M&uacute;sculo<select id="mMus"></select></label>
  <label>Lado<select id="mLado"></select></label>
  <label>Esfuerzo<select id="mEsf"></select></label>
  <label>Condici&oacute;n<select id="mCond"></select></label>
  <label>Sensor<input id="mSens"></label>
  <label>Tipo de electrodo<input id="mElec"></label>
  <label>Notas de colocaci&oacute;n (sin nombres)<input id="mPNot"></label>
  <label>Notas t&eacute;cnicas (sin nombres)<input id="mNot"></label>
  <small id="dlgPlan" style="display:block;margin-bottom:6px"></small>
  <small id="dlgAviso" class="err" style="display:block;margin-bottom:6px"></small>
  <div class="fila"><button id="dlgNo">Cancelar</button><button class="p grande" id="dlgSi">Comenzar (24 s)</button></div>
</div></div>
<!-- Indicaciones a pantalla completa durante la muestra (legible a 2 m) -->
<div id="cue" class="cue" hidden>
  <div id="cueInfo"></div>
  <div id="cueTxt"></div>
  <div id="cueSeg"></div>
  <div id="cuePct"></div>
  <div class="prog"><div id="cueBar"></div></div>
  <button id="cueStop">Cancelar muestra</button>
</div>
<script>
const FS=50, VENTANA=FS*10;               // 50 puntos por segundo, 10 s en la grafica en vivo
// Texto del recuadro superior para cada codigo "st" que manda el ESP32 (ver estadoParaWeb())
const ESTADOS=['Sin conexión con la máquina: encienda la estación',
 'Sin calibrar: presione el botón de la máquina o «Recalibrar»',
 'Calibración: prepárese, en unos segundos RELAJE el músculo',
 'Calibración: RELAJE el músculo (midiendo reposo)',
 'Calibración: ¡CONTRAIGA AL MÁXIMO!',
 'Calibración: calculando…',
 'Calibración lista',
 'La calibración falló: revise electrodos y vuelva a calibrar',
 'Listo · midiendo'];
const COL_EST=['#f87171','#facc15','#facc15','#38bdf8','#f87171','#38bdf8','#4ade80','#f87171','#4ade80'];
const OSC={bg:'#1e293b',grid:'#334155',tx:'#94a3b8',linea:'#38bdf8',act:'rgba(74,222,128,.18)',mut:'#94a3b8',rojo:'#f87171',amar:'#facc15'};
const CLARO={bg:'#ffffff',grid:'#e5e7eb',tx:'#374151',linea:'#0369a1',act:'rgba(22,163,74,.15)',mut:'#6b7280',rojo:'#dc2626',amar:'#ca8a04'};
const $=id=>document.getElementById(id);
let desde=0, vivo=[], sesion=[], grabando=false, iIni=0, inicio=null, guardado=true;
let cal={rest:0,max:0,thr:0,pa:70}, calSesion=null, calOk=false, prevAct=0, nAct=0, fallos=0;
let maq={tie:0,car:0,rec:0,tiros:0,pts:0,hs:0}, maq0=null;
// EMG filtrada (1 kHz): en vivo los ultimos 5 s; en la grabacion tiempos y valores en dos arreglos
const FSR=1000, VENTANA_R=FSR*5;
let desdeR=0, vivoR=[], rIni=0, sesRt=[], sesRv=[];   // estado de la maquina y valores al iniciar la grabacion

function banner(t,c){const b=$('banner');b.textContent=t;b.style.background=c;}

// Pide los datos nuevos al ESP32 cada 150 ms
async function sondear(){
  try{
    const r=await fetch('/datos?desde='+desde+'&desdeR='+desdeR,{cache:'no-store'});
    procesar(await r.json()); fallos=0;
  }catch(e){ if(++fallos>3) banner('Sin conexión con el ESP32…','#f87171'); }
  setTimeout(sondear,150);
}

function procesar(j){
  calOk=j.cal==1;
  cal={rest:j.rest,max:calOk?j.max:0,thr:j.thr,pa:j.pa};
  maq={tie:j.tie,car:j.car,rec:j.rec,tiros:j.tiros,pts:j.pts,hs:j.hs};
  let t=ESTADOS[j.st]||''; if(j.st>=2&&j.st<=4&&j.rt>0) t+=' ('+j.rt+' s)';
  banner(t,COL_EST[j.st]||'#94a3b8');
  revisarCalibracion(j);
  if(j.idx<desde){  // el ESP32 se reinicio
    vivo=[];
    if(grabando) iIni=j.i0-Math.round((sesion.length?sesion[sesion.length-1].t:0)*FS)-1;
  }
  let i=j.i0;
  for(const p of j.d){
    const s={i:i,rms:p[0],pct:p[1],act:p[2],car:p[3],tiros:p[4],pts:p[5]};   // car/tiros/pts: estado de la maquina
    vivo.push(s);
    if(grabando){
      s.t=(i-iIni)/FS; sesion.push(s); guardado=false;
      if(s.act&&!prevAct) nAct++;
      if(calOk) calSesion={...cal};
    }
    prevAct=s.act; i++;
  }
  if(vivo.length>VENTANA) vivo.splice(0,vivo.length-VENTANA);
  desde=j.idx;
  // EMG filtrada (1 kHz)
  if(j.r){
    if(j.ridx<desdeR){  // el ESP32 se reinicio
      vivoR=[];
      if(grabando) rIni=j.r0-Math.round((sesRt.length?sesRt[sesRt.length-1]:0)*FSR)-1;
      abortarMuestra('el ESP32 se reinició'); perderCalibracion();
    }else if(j.r0!==desdeR){  // el navegador se atraso mas que el buffer del ESP32: faltan muestras
      abortarMuestra('se perdieron datos (conexión lenta o pestaña en segundo plano)'); perderCalibracion();
    }
    let k=j.r0;
    for(const v of j.r){
      vivoR.push(v);
      if(grabando){ sesRt.push((k-rIni)/FSR); sesRv.push(v); }
      if(smp&&k>=smp.ini&&smp.v.length<N_MUESTRA) smp.v.push(v);
      if(calCap){ calCap.v.push(v); calCap.p.push(j.st-2); }   // paso de calibracion 0..3
      k++;
    }
    if(smp&&smp.v.length>=N_MUESTRA) terminarMuestra();
    if(vivoR.length>VENTANA_R) vivoR.splice(0,vivoR.length-VENTANA_R);
    desdeR=j.ridx;
  }
  actualizarUI();
}

function stats(a){
  if(!a.length) return null;
  let mn=Infinity,mx=-Infinity,sm=0;
  for(const s of a){ if(s.rms<mn)mn=s.rms; if(s.rms>mx)mx=s.rms; sm+=s.rms; }
  return {mn:mn,mx:mx,prom:sm/a.length};
}
const f1=v=>v.toFixed(1);
const durTxt=s=>Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0');
// Tiros y canastas de la sesion grabada (diferencia desde que se empezo a grabar)
function maqSesion(){
  if(!maq0) return {tiros:0,pts:0};
  const d=(a,b)=>a>=b?a-b:a;              // si la maquina se reinicio, cuenta desde 0
  return {tiros:d(maq.tiros,maq0.tiros),pts:d(maq.pts,maq0.pts)};
}

function actualizarUI(){
  const u=vivo[vivo.length-1];
  if(u){
    $('vAct').textContent=f1(u.rms);
    $('vPct').textContent=calOk?Math.round(u.pct)+' %':'–';
    $('vEst').textContent=u.act?'SOBRE UMBRAL':'reposo';
    $('vEst').style.color=u.act?'var(--verde)':'var(--mut)';
  }
  actualizarCue();
  const st=stats(grabando?sesion:vivo);
  if(st){ $('vMin').textContent=f1(st.mn); $('vMax').textContent=f1(st.mx); $('vProm').textContent=f1(st.prom); }
  $('vCal').textContent=calOk?f1(cal.rest)+' / '+f1(cal.max):'–';
  $('vNAct').textContent=nAct;
  $('vMaq').textContent=cal.pa+' % · '+maq.tie+' s';
  $('vCar').textContent=maq.rec?'recargando':maq.car+' %';
  $('vTiros').textContent=maq.tiros;
  $('vPts').textContent=maq.pts+' / '+maq.hs;
  const d=sesion.length?sesion[sesion.length-1].t:0;
  $('ambito').textContent=grabando?('● Grabando '+durTxt(d)+' — estadísticas de la sesión')
    :(sesion.length?('Sesión detenida ('+durTxt(d)+'): lista para descargar — estadísticas últimos 10 s')
    :'Estadísticas últimos 10 s');
}

// Dibuja la grafica en cualquier canvas (en vivo y para exportar)
function dibujar(ctx,W,H,datos,o){
  const tit=o.titulo||[];
  const m={l:62,r:14,t:tit.length?tit.length*22+18:12,b:30}, pw=W-m.l-m.r, ph=H-m.t-m.b, c=o.cal;
  ctx.fillStyle=o.bg; ctx.fillRect(0,0,W,H);
  tit.forEach((t,k)=>{ctx.fillStyle=o.tx;ctx.textAlign='left';ctx.font=(k?'':'bold ')+(k?13:16)+'px system-ui';ctx.fillText(t,m.l,22+k*22);});
  let lo=Infinity,hi=-Infinity;
  for(const s of datos){ if(s.rms<lo)lo=s.rms; if(s.rms>hi)hi=s.rms; }
  if(c&&c.max>0){ lo=Math.min(lo,c.rest); hi=Math.max(hi,c.max); }
  if(!isFinite(lo)){lo=0;hi=100;}
  if(lo<0.3*hi) lo=0; else lo*=0.95;
  hi=hi*1.08+1;
  const Y=v=>m.t+ph*(1-(v-lo)/(hi-lo));
  const slots=Math.max(o.slots,2), X=k=>m.l+pw*k/(slots-1);
  ctx.font='12px system-ui'; ctx.lineWidth=1;
  for(let g=0;g<=5;g++){
    const v=lo+(hi-lo)*g/5,y=Y(v);
    ctx.strokeStyle=o.grid;ctx.beginPath();ctx.moveTo(m.l,y);ctx.lineTo(m.l+pw,y);ctx.stroke();
    ctx.fillStyle=o.tx;ctx.textAlign='right';ctx.fillText(v.toFixed(0),m.l-6,y+4);
  }
  ctx.textAlign='center';
  for(let g=0;g<=o.nx;g++) ctx.fillText(o.etqX(g/o.nx),m.l+pw*g/o.nx,H-10);
  ctx.save();ctx.translate(14,m.t+ph/2);ctx.rotate(-Math.PI/2);ctx.fillText('RMS (mV)',0,0);ctx.restore();

  // Agrupar por pixel (min/max) para que sesiones largas se vean completas
  const N=datos.length,k0=slots-N,pts=[]; let cur=null;
  for(let k=0;k<N;k++){
    const s=datos[k],px=Math.round(X(k0+k));
    if(!cur||cur.px!==px){ if(cur)pts.push(cur); cur={px:px,mn:s.rms,mx:s.rms,a:s.act,f:s.rms,l:s.rms}; }
    else{ cur.mn=Math.min(cur.mn,s.rms); cur.mx=Math.max(cur.mx,s.rms); cur.a=s.act; cur.l=s.rms; }
  }
  if(cur)pts.push(cur);
  const w=Math.ceil(Math.max(1,pw/(slots-1)))+1;
  ctx.fillStyle=o.act;
  for(const p of pts) if(p.a) ctx.fillRect(p.px-w/2,m.t,w,ph);

  const hl=(v,col,t)=>{const y=Y(v);ctx.strokeStyle=col;ctx.setLineDash([6,4]);ctx.beginPath();ctx.moveTo(m.l,y);ctx.lineTo(m.l+pw,y);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=col;ctx.textAlign='left';ctx.fillText(t,m.l+6,y-4);};
  if(c&&c.max>0){ hl(c.rest,o.mut,'reposo'); hl(c.thr,o.rojo,'umbral '+c.pa+' %'); hl(c.max,o.amar,'máx. calibración'); }

  ctx.strokeStyle=o.linea; ctx.lineWidth=1.6; ctx.beginPath();
  pts.forEach((p,k)=>{
    if(k===0) ctx.moveTo(p.px,Y(p.f)); else ctx.lineTo(p.px,Y(p.f));
    if(p.mn!==p.mx){ ctx.lineTo(p.px,Y(p.mx)); ctx.lineTo(p.px,Y(p.mn)); }
    ctx.lineTo(p.px,Y(p.l));
  });
  ctx.stroke();
}

// Grafica de la EMG cruda (cuentas ADC): se resta la media de lo visible (solo para dibujar),
// min/max por pixel, escala simetrica alrededor de 0
function dibujarRaw(ctx,W,H,crudos,o){
  let mu=0; for(const v of crudos) mu+=v; mu=crudos.length?mu/crudos.length:0;
  const vals=crudos.map(v=>v-mu);
  const m={l:62,r:14,t:10,b:26}, pw=W-m.l-m.r, ph=H-m.t-m.b, N=vals.length, slots=Math.max(o.slots,2);
  ctx.fillStyle=o.bg; ctx.fillRect(0,0,W,H);
  let a=10; for(const v of vals){ const x=Math.abs(v); if(x>a)a=x; }
  a*=1.1;
  const Y=v=>m.t+ph*(0.5-v/(2*a)), X=k=>m.l+pw*k/(slots-1);
  ctx.font='12px system-ui'; ctx.lineWidth=1;
  for(let g=-2;g<=2;g++){
    const v=a*g/2,y=Y(v);
    ctx.strokeStyle=o.grid;ctx.beginPath();ctx.moveTo(m.l,y);ctx.lineTo(m.l+pw,y);ctx.stroke();
    ctx.fillStyle=o.tx;ctx.textAlign='right';ctx.fillText(v.toFixed(0),m.l-6,y+4);
  }
  ctx.textAlign='center';
  for(let g=0;g<=5;g++) ctx.fillText((g-5)+' s',m.l+pw*g/5,H-8);
  ctx.save();ctx.translate(14,m.t+ph/2);ctx.rotate(-Math.PI/2);ctx.fillText('EMG (ADC)',0,0);ctx.restore();
  ctx.strokeStyle=o.linea; ctx.lineWidth=1; ctx.beginPath();
  const k0=slots-N; let px0=-1,mn=0,mx=0;
  for(let k=0;k<=N;k++){
    const px=k<N?Math.round(X(k0+k)):-2;
    if(px!==px0){
      if(px0>=0){ ctx.moveTo(px0,Y(mx)); ctx.lineTo(px0,Y(mn)); }
      if(k<N){ px0=px; mn=mx=vals[k]; }
    }else{ if(vals[k]<mn)mn=vals[k]; if(vals[k]>mx)mx=vals[k]; }
  }
  ctx.stroke();
}

const cv=$('cv'), cx=cv.getContext('2d');
const cvR=$('cvR'), cxR=cvR.getContext('2d');
function render(){
  const d=window.devicePixelRatio||1, w=cv.clientWidth, h=cv.clientHeight;
  if(cv.width!==Math.round(w*d)||cv.height!==Math.round(h*d)){cv.width=Math.round(w*d);cv.height=Math.round(h*d);}
  cx.setTransform(d,0,0,d,0,0);
  dibujar(cx,w,h,vivo,{...OSC,slots:VENTANA,nx:5,etqX:f=>(f*10-10).toFixed(0)+' s',cal:cal});
  const wR=cvR.clientWidth, hR=cvR.clientHeight;
  if(cvR.width!==Math.round(wR*d)||cvR.height!==Math.round(hR*d)){cvR.width=Math.round(wR*d);cvR.height=Math.round(hR*d);}
  cxR.setTransform(d,0,0,d,0,0);
  dibujarRaw(cxR,wR,hR,vivoR,{...OSC,slots:VENTANA_R});
  requestAnimationFrame(render);
}

// ---------------- Grabacion y descargas ----------------
function paciente(){ const s=ids().s; return RE_SUJ.test(s)?s:'P000'; }   // seudonimo, nunca el nombre
function nombreArchivo(){
  const d=inicio||new Date(), p=n=>String(n).padStart(2,'0');
  return 'EMG_'+paciente().replace(/[^\wáéíóúñÁÉÍÓÚÑ-]+/g,'_')+'_'+d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+'_'+p(d.getHours())+'-'+p(d.getMinutes());
}
function descargar(blob,nombre){
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=nombre;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href),2000);
}
function lineasResumen(){
  const st=stats(sesion)||{mn:0,mx:0,prom:0}, c=calSesion||cal, d=sesion.length?sesion[sesion.length-1].t:0, ms=maqSesion();
  return ['Sujeto: '+paciente()+'   ·   '+(inicio?inicio.toLocaleString():'')+'   ·   Duración '+durTxt(d),
          'RMS mín '+f1(st.mn)+' mV   ·   máx '+f1(st.mx)+' mV   ·   promedio '+f1(st.prom)+' mV   ·   Activaciones '+nAct,
          'Calibración: reposo '+f1(c.rest)+' mV   ·   máx '+f1(c.max)+' mV   ·   umbral ('+c.pa+' %) '+f1(c.thr)+' mV',
          'Máquina: nivel '+cal.pa+' %   ·   tiempo '+maq.tie+' s   ·   tiros '+ms.tiros+'   ·   canastas '+ms.pts];
}
function exportarCSV(){
  if(!sesion.length) return alert('Primero graba una sesión.');
  const L=lineasResumen().map(t=>'# '+t.replace(/,/g,' '));
  L.push('tiempo_s,rms_mV,porcentaje_contraccion,sobre_umbral,carga_pct,tiros,canastas');
  for(const s of sesion) L.push(s.t.toFixed(2)+','+s.rms+','+s.pct+','+s.act+','+s.car+','+s.tiros+','+s.pts);
  descargar(new Blob([L.join('\n')],{type:'text/csv'}),nombreArchivo()+'.csv');
  guardado=true;
}
// EMG cruda de la sesion grabada (cuentas del ADC), 1000 muestras por segundo
function exportarRaw(){
  if(!sesRv.length) return alert('Primero graba una sesi\u00f3n.');
  const L=lineasResumen().map(t=>'# '+t.replace(/,/g,' '));
  L.push('# EMG filtrada por el circuito analogico, cuentas crudas del ADC de 12 bits (0..4095, reposo ~2048)');
  L.push('tiempo_s,emg_adc');
  for(let k=0;k<sesRv.length;k++) L.push(sesRt[k].toFixed(3)+','+sesRv[k]);
  descargar(new Blob([L.join('\n')],{type:'text/csv'}),nombreArchivo()+'_EMG_1kHz.csv');
}
function exportarPNG(){
  if(!sesion.length) return alert('Primero graba una sesión.');
  const d=sesion[sesion.length-1].t, W=Math.min(8000,Math.max(1800,Math.round(d*30))), H=720;
  const c=document.createElement('canvas'); c.width=W; c.height=H;
  dibujar(c.getContext('2d'),W,H,sesion,{...CLARO,slots:sesion.length,nx:Math.max(5,Math.round(W/200)),
    etqX:f=>durTxt(f*d),cal:calSesion||cal,titulo:lineasResumen()});
  c.toBlob(b=>descargar(b,nombreArchivo()+'.png'));
}

$('bGrab').onclick=()=>{
  if(!grabando){
    if(sesion.length&&!guardado&&!confirm('La sesión anterior no se ha descargado. ¿Descartarla?')) return;
    sesion=[]; nAct=0; iIni=desde; inicio=new Date(); sesRt=[]; sesRv=[]; rIni=desdeR; calSesion=calOk?{...cal}:null; maq0={...maq}; grabando=true;
    $('bGrab').textContent='■ Detener grabación'; $('bGrab').className='g';
  }else{
    grabando=false; $('bGrab').textContent='● Iniciar grabación'; $('bGrab').className='p';
  }
  actualizarUI();
};
$('bCsv').onclick=exportarCSV;
$('bPng').onclick=exportarPNG;
$('bRaw').onclick=exportarRaw;
// La web solo PIDE la calibracion: la maquina la ejecuta y guia al paciente en su pantalla
// La calibracion queda guardada para la colocacion (E01...) escrita arriba.
$('bCal').onclick=()=>{
  const d=ids();
  if(!idsValidos(d)) return;
  if(smp) return msg('Espere a que termine la muestra.','err');
  const ya=ls.get('cal_'+d.p,null);
  const txt=ya?d.p+' ya tiene calibración. Si se volvieron a poner los electrodos, use una colocación NUEVA. ¿Calibrar igual?'
              :'¿Calibrar la colocación '+d.p+'? La máquina guiará al paciente en su pantalla (reposo, luego contracción máxima).';
  if(confirm(txt)) fetch('/cal',{method:'POST'});
};
window.addEventListener('beforeunload',e=>{ if((sesion.length&&!guardado)||smp){ e.preventDefault(); e.returnValue=''; } });

// =====================================================================
//  RECOLECCION SEMGIA - mismo flujo y formato que scripts/record.py del repo.
//  Estas constantes DEBEN coincidir con semgia/config.py (import_web.py lo verifica).
// =====================================================================
const PASOS=[[0,8],[1,8],[0,8]];         // config.SAMPLE_STEPS: (etiqueta, s) REPOSO / CONTRAIGA / REPOSO
const N_MUESTRA=24000;                    // 24 s x 1000 Hz (config.FS)
const MUSCULOS=['biceps brachii','triceps brachii','flexor carpi radialis','tibialis anterior','other'];
const LADOS=['right','left'], ESFUERZOS=['light','medium','strong'], CONDICIONES=['fresh','fatigued'];
// docs/protocol.md: 10 muestras por colocacion
const N_PLAN=10;
const PLAN=[['light','fresh'],['light','fresh'],['light','fresh'],['medium','fresh'],['medium','fresh'],
            ['medium','fresh'],['strong','fresh'],['strong','fresh'],['medium','fatigued'],['medium','fatigued']];
const GUIA={light:'~20 % del máximo',medium:'~50 % del máximo',strong:'lo más fuerte posible'};
const RE_SUJ=/^P\d{3}$/, RE_OP=/^OP\d{2}$/, RE_PL=/^E\d{2}$/;
let smp=null;      // muestra en curso {meta, ini: indice EMG de inicio, v: valores, lab: fase mostrada}
let calCap=null;   // EMG grabada durante la calibracion de la maquina {v, p, ok, ids, t}

// localStorage puede fallar (modo privado): la pagina sigue funcionando sin el
const ls={get:(k,d)=>{try{const v=localStorage.getItem('semgia_'+k);return v===null?d:JSON.parse(v);}catch(e){return d;}},
          set:(k,v)=>{try{localStorage.setItem('semgia_'+k,JSON.stringify(v));}catch(e){}}};
function ids(){ return {s:$('fSuj').value.trim().toUpperCase(),o:$('fOp').value.trim().toUpperCase(),p:$('fPl').value.trim().toUpperCase()}; }
function idsValidos(d){
  if(!RE_SUJ.test(d.s)){ msg('Sujeto debe ser como P001 (seudónimo, nunca el nombre).','err'); return false; }
  if(!RE_OP.test(d.o)){ msg('Operador debe ser como OP01.','err'); return false; }
  if(!RE_PL.test(d.p)){ msg('Colocación debe ser como E01 (número nuevo cada vez que se ponen electrodos).','err'); return false; }
  return true;
}
function msg(t,cls){ const m=$('msgRecol'); m.textContent=t; m.className=cls||''; }
const cuenta=p=>ls.get('cnt_'+p,0);       // muestras ya guardadas de esa colocacion
function mostrarContador(){
  const d=ids();
  $('vCnt').textContent=RE_PL.test(d.p)?(Math.min(cuenta(d.p)+1,99)+' de '+N_PLAN):'–';
  if(!smp&&RE_PL.test(d.p)&&!calCap)
    msg(ls.get('cal_'+d.p,null)?d.p+': calibración guardada ✓':d.p+': sin calibración todavía → «1· Calibrar colocación»',
        ls.get('cal_'+d.p,null)?'ok':'');
}
for(const [id,k] of [['fSuj','suj'],['fOp','op'],['fPl','pl']]){
  $(id).value=ls.get(k,'');
  $(id).oninput=()=>{ ls.set(k,$(id).value.trim().toUpperCase()); mostrarContador(); };
}
$('bCnt').onclick=()=>{
  const d=ids(); if(!RE_PL.test(d.p)) return;
  const n=parseInt(prompt('¿Cuántas muestras buenas hay ya guardadas de '+d.p+'?',cuenta(d.p)),10);
  if(n>=0) ls.set('cnt_'+d.p,n);
  mostrarContador();
};

function llenar(sel,ops){ $(sel).innerHTML=ops.map(o=>'<option>'+o+'</option>').join(''); }
llenar('mMus',MUSCULOS); llenar('mLado',LADOS); llenar('mEsf',ESFUERZOS); llenar('mCond',CONDICIONES);

// Pitidos en cada cambio de fase (el sujeto no tiene que mirar la pantalla todo el tiempo)
let audio=null;
function pitido(f,ms,n){
  try{
    audio=audio||new (window.AudioContext||window.webkitAudioContext)();
    for(let i=0;i<(n||1);i++){
      const o=audio.createOscillator(),g=audio.createGain(),t=audio.currentTime+i*(ms+90)/1000;
      o.frequency.value=f; o.connect(g); g.connect(audio.destination);
      g.gain.setValueAtTime(.35,t); g.gain.setValueAtTime(0,t+ms/1000); o.start(t); o.stop(t+ms/1000+.02);
    }
  }catch(e){}
}

$('bMuestra').onclick=()=>{
  if(smp) return;
  const d=ids();
  if(!idsValidos(d)) return;
  if(fallos>3) return msg('Sin conexión con el ESP32.','err');
  if(calCap) return msg('Espere a que termine la calibración.','err');
  const n=cuenta(d.p), plan=PLAN[Math.min(n,PLAN.length-1)], u=ls.get('meta',{});
  $('mMus').value=u.muscle||MUSCULOS[0]; $('mLado').value=u.side||LADOS[0];
  $('mSens').value=u.sensor_id||'DFRobot-SEN0240'; $('mElec').value=u.electrode_type||'dry (built-in)';
  $('mPNot').value=u.placement_notes||''; $('mNot').value='';
  $('mEsf').value=plan[0]; $('mCond').value=plan[1];
  $('dlgIds').textContent=d.s+' · '+d.o+' · colocación '+d.p+' · muestra '+(n+1)+' de '+N_PLAN;
  $('dlgPlan').textContent='Plan (protocolo) para la muestra '+(n+1)+': '+plan[0]+' · '+plan[1]
    +(plan[1]==='fatigued'?' → antes: contracción fuerte ~60 s, luego grabar enseguida.':'');
  $('dlgAviso').textContent=(ls.get('cal_'+d.p,null)?'':'Aviso: '+d.p+' no tiene calibración guardada en este navegador. ')
    +(n>=N_PLAN?'Aviso: '+d.p+' ya tiene '+n+' muestras.':'');
  $('dlg').hidden=false;
};
$('dlgNo').onclick=()=>{ $('dlg').hidden=true; };
$('dlgSi').onclick=()=>{
  const d=ids();
  const meta={placement_id:d.p,subject_id:d.s,operator_id:d.o,muscle:$('mMus').value,side:$('mLado').value,
    sensor_id:$('mSens').value.trim(),electrode_type:$('mElec').value.trim(),placement_notes:$('mPNot').value.trim(),
    effort:$('mEsf').value,condition:$('mCond').value,sampling_rate_hz:FSR,
    start_time_utc:new Date().toISOString().slice(0,19)+'+00:00',notes:$('mNot').value.trim()};
  ls.set('meta',meta);
  $('dlg').hidden=true;
  smp={meta:meta,ini:desdeR,v:[],lab:PASOS[0][0]};   // empieza con la proxima muestra que llegue del ESP32
  pitido(660,200);
  msg('Grabando muestra…');
  $('cue').hidden=false; actualizarCue();
};
$('cueStop').onclick=()=>abortarMuestra('cancelada por el operador');

// Fase y segundos restantes segun las muestras RECIBIDAS (el reloj es el ESP32, no el PC)
function fase(n){
  let fin=0;
  for(const [lab,s] of PASOS){ fin+=s*FSR; if(n<fin) return {lab:lab,resta:(fin-n)/FSR}; }
  return {lab:PASOS[PASOS.length-1][0],resta:0};
}
function actualizarCue(){
  if(!smp) return;
  const n=smp.v.length, f=fase(n), d=smp.meta;
  if(f.lab!==smp.lab){ smp.lab=f.lab; pitido(f.lab?1047:523,300); }
  $('cue').style.background=f.lab?'#b91c1c':'#15803d';
  $('cueTxt').textContent=f.lab?'¡CONTRAIGA!':'REPOSO';
  $('cueSeg').textContent=Math.ceil(f.resta)+' s';
  $('cueInfo').textContent='Muestra '+(cuenta(d.placement_id)+1)+' de '+N_PLAN+' · '+d.placement_id+' · '
    +d.effort+(f.lab?' ('+GUIA[d.effort]+')':'')+(d.condition==='fatigued'?' · fatigado':'');
  const u=vivo[vivo.length-1];
  $('cuePct').textContent=(calOk&&u)?'Activación '+Math.round(u.pct)+' %':'';
  $('cueBar').style.width=(100*n/N_MUESTRA)+'%';
}
function sello(){ return new Date().toISOString().slice(0,19).replace(/[-:]/g,'')+'Z'; }
function bajarJSON(obj,nombre){ descargar(new Blob([JSON.stringify(obj)],{type:'application/json'}),nombre); }

function terminarMuestra(){
  const m=smp; smp=null; $('cue').hidden=true;
  // Las etiquetas 0/1 NO van en el archivo: import_web.py las calcula del numero de fila (temporizador)
  bajarJSON({format:'semgia-sample-1',metadata:m.meta,values:m.v.slice(0,N_MUESTRA)},
            'semgia_sample_'+m.meta.placement_id+'_'+sello()+'.json');
  const p=m.meta.placement_id, n=cuenta(p)+1;
  ls.set('cnt_'+p,n);
  pitido(880,150,2);
  mostrarContador();
  msg('✓ Muestra '+n+' de '+N_PLAN+' ('+p+') descargada. Descanse ~10 s. En el PC: python scripts/import_web.py','ok');
}
function abortarMuestra(motivo){
  if(!smp) return;
  smp=null; $('cue').hidden=true; pitido(220,600);
  msg('✗ Muestra NO guardada: '+motivo+'. Repítala.','err');
}

// Calibracion: la dirige la maquina (estados 2..5). La pagina graba la EMG mientras dura
// y, si termina bien (estado 6), descarga la calibracion para la colocacion actual.
function revisarCalibracion(j){
  const calibrando=j.st>=2&&j.st<=5;
  if(calibrando&&smp) abortarMuestra('la máquina empezó una calibración');
  if(calibrando&&!calCap){ calCap={v:[],p:[],ok:true,ids:ids(),t:new Date()}; msg('Calibrando… (grabando EMG)'); }
  if(!calCap||calibrando) return;
  const c=calCap; calCap=null;
  if(j.st===7) return msg('✗ La calibración falló: revise electrodos y calibre de nuevo.','err');
  if(j.st!==6||j.cal!==1) return msg('✗ Calibración interrumpida: no se guardó.','err');
  if(!c.ok) return msg('✗ Calibración hecha en la máquina, pero se perdieron datos en la web: no se guardó. Calibre de nuevo.','err');
  const d=c.ids;
  if(!RE_SUJ.test(d.s)||!RE_OP.test(d.o)||!RE_PL.test(d.p))
    return msg('✗ Calibración hecha, pero NO guardada: complete Sujeto / Operador / Colocación y calibre de nuevo.','err');
  bajarJSON({format:'semgia-calib-1',placement_id:d.p,subject_id:d.s,operator_id:d.o,
             start_time_utc:c.t.toISOString().slice(0,19)+'+00:00',sampling_rate_hz:FSR,
             rest_mV:j.rest,max_mV:j.max,values:c.v,steps:c.p},
            'semgia_calib_'+d.p+'_'+sello()+'.json');
  ls.set('cal_'+d.p,{rest:j.rest,max:j.max});
  mostrarContador();
  msg('✓ Calibración de '+d.p+' descargada (reposo '+f1(j.rest)+' mV, máx. '+f1(j.max)+' mV). Ahora: «Tomar muestra».','ok');
}
function perderCalibracion(){ if(calCap) calCap.ok=false; }
mostrarContador();

sondear(); render();
</script></body></html>)rawliteral";
