// =====================================================================
//  pagina.h - SEMGIA recording page, served by the ESP32 (http://192.168.4.1, no internet needed)
//  The ESP32 only streams raw ADC counts (/datos). Everything else runs here, in the browser:
//    - live plots: raw EMG (5 s) and RMS (10 s, 200 ms windows minus their mean = config.WINDOW)
//    - "1· Calibrar colocación": full-screen PREPÁRESE 3 s / REPOSO 5 s / ¡MÁXIMO! 5 s with beeps
//      -> rest RMS + max RMS for that placement -> downloads semgia_calib_EXX_*.json
//    - "2· Tomar muestra": form -> REPOSO 8 / ¡CONTRAIGA! 8 / REPOSO 8 -> semgia_sample_EXX_*.json
//  On the PC: python scripts/import_web.py  -> data/raw/sample_NNN/ and data/raw/calibration_EXX/
//  Constants marked "= config.X" MUST match semgia/config.py (tests/test_sources_storage.py checks them).
//  Pseudonyms only (P001 / OP01 / E01), never names.
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
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:8px}
.c{background:var(--card);border-radius:10px;padding:10px}
.c small{color:var(--mut);display:block;font-size:.75rem;margin-bottom:2px}
.c b{font-size:1.35rem;font-variant-numeric:tabular-nums}
.leyenda{color:var(--mut);display:block;margin:8px 0 4px;font-size:.8rem}
canvas{width:100%;height:240px;border-radius:10px;display:block}
#cvR{height:180px}
button,input,select{font:inherit;padding:10px 14px;border-radius:8px;border:0}
button{background:#334155;color:var(--tx);cursor:pointer}
button.p{background:#0284c7}button.r{background:#7c2d12}
[hidden]{display:none!important}
#recol{margin:10px 0;border:2px solid #0284c7}
#recol h2,.caja h2{font-size:1rem;margin:0 0 8px}
.fila{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin-bottom:8px}
.fila label,.caja label{display:flex;flex-direction:column;font-size:.75rem;color:var(--mut);gap:2px}
.fila input{width:6.5em;background:#0f172a;color:var(--tx);text-transform:uppercase}
#vCnt{font-size:1.35rem}
button.grande{font-size:1.2rem;padding:14px 22px;font-weight:700}
#msgRecol{display:block;min-height:1.2em}
.err{color:#f87171}.ok{color:var(--verde)}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:9;padding:12px}
.caja{background:var(--card);border-radius:12px;padding:16px;width:100%;max-width:520px;max-height:100%;overflow:auto}
.caja label{margin-bottom:8px}.caja input,.caja select{background:#0f172a;color:var(--tx);padding:8px;border-radius:6px}
.cue{position:fixed;inset:0;z-index:10;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;text-align:center;padding:16px}
#cueInfo{font-size:clamp(1.2rem,4vw,2.4rem);opacity:.95;font-weight:600}
#cueTxt{font-size:clamp(3rem,16vw,12rem);font-weight:800;line-height:1.05}
#cueSub{font-size:clamp(1.2rem,4vw,2.4rem);min-height:1.2em}
#cueSeg{font-size:clamp(2.5rem,12vw,8rem);font-weight:700;font-variant-numeric:tabular-nums}
.prog{width:min(90vw,900px);height:14px;background:rgba(255,255,255,.25);border-radius:7px;margin:18px 0}
#cueBar{height:100%;width:0;background:#fff;border-radius:7px}
#cueStop{background:rgba(0,0,0,.35);color:#fff}
</style></head><body>
<h1>SEMGIA &middot; Recolecci&oacute;n EMG</h1>
<div id="banner">Conectando&hellip;</div>
<div class="grid">
  <div class="c"><small>RMS actual (cuentas ADC)</small><b id="vRms">&ndash;</b></div>
  <div class="c"><small>Activaci&oacute;n (% del m&aacute;ximo calibrado)</small><b id="vPct">&ndash;</b></div>
  <div class="c"><small>Calibraci&oacute;n: reposo / m&aacute;x. (RMS)</small><b id="vCal">&ndash;</b></div>
  <div class="c"><small>Valor crudo (reposo &asymp; 1860)</small><b id="vRaw">&ndash;</b></div>
</div>

<div class="c" id="recol">
  <h2>Recolecci&oacute;n de datos (solo seud&oacute;nimos, nunca nombres)</h2>
  <div class="fila">
    <label>Sujeto<input id="fSuj" placeholder="P001" maxlength="4" autocomplete="off"></label>
    <label>Operador<input id="fOp" placeholder="OP01" maxlength="4" autocomplete="off"></label>
    <label>Colocaci&oacute;n<input id="fPl" placeholder="E01" maxlength="3" autocomplete="off"></label>
    <div><small style="color:var(--mut);font-size:.75rem">Muestra</small><br><b id="vCnt">&ndash;</b>
      <button id="bCnt" title="Corregir el contador (p. ej. tras borrar una muestra mala)">&#9998;</button></div>
  </div>
  <div class="fila">
    <button class="r grande" id="bCal">1&middot; Calibrar colocaci&oacute;n (13 s)</button>
    <button class="p grande" id="bMuestra">2&middot; &#9654; Tomar muestra (24 s)</button>
  </div>
  <small id="msgRecol"></small>
</div>

<small class="leyenda">RMS (ventanas de 200 ms) &middot; &uacute;ltimos 10 s &middot; l&iacute;neas: reposo y m&aacute;ximo de la calibraci&oacute;n</small>
<canvas id="cv"></canvas>
<small class="leyenda">EMG cruda (cuentas ADC, sin offset solo para dibujar), 1000 muestras/s &middot; &uacute;ltimos 5 s</small>
<canvas id="cvR"></canvas>

<!-- Sample form (fields = METADATA_FIELDS in semgia/storage.py) -->
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

<!-- Full-screen cues for calibration and samples (readable from 2 m) -->
<div id="cue" class="cue" hidden>
  <div id="cueInfo"></div>
  <div id="cueTxt"></div>
  <div id="cueSub"></div>
  <div id="cueSeg"></div>
  <div class="prog"><div id="cueBar"></div></div>
  <button id="cueStop">Cancelar</button>
</div>

<script>
// ---------------- constants (= semgia/config.py) ----------------
const FSR=1000;                                   // = config.FS
const PASOS=[[0,8],[1,8],[0,8]];                  // = config.SAMPLE_STEPS (label, s): REPOSO / CONTRAIGA / REPOSO
const N_MUESTRA=24000;                            // 24 s x FS
const PASOS_CAL=[[0,3],[1,5],[2,5]];              // = config.CALIB_STEPS (step, s): prepare / rest / max
const N_CAL=13000;                                // 13 s x FS
const CAL_SALTAR=1000;                            // = config.CALIB_SKIP_S x FS: reaction time, ignored
const CAL_MIN_RATIO=2;                            // = config.CALIB_MIN_RATIO: max RMS >= 2 x rest RMS
const VENT=200, PASO_RMS=20;                      // RMS window = config.WINDOW (200 ms); 50 values/s for the plot
const MUSCULOS=['biceps brachii','triceps brachii','flexor carpi radialis','tibialis anterior','other'];   // = config.MUSCLES
const LADOS=['right','left'], ESFUERZOS=['light','medium','strong'], CONDICIONES=['fresh','fatigued'];   // = config.SIDES / EFFORTS / CONDITIONS
const N_PLAN=10;                                  // = config.SAMPLES_PER_PLACEMENT (docs/protocol.md)
const PLAN=[['light','fresh'],['light','fresh'],['light','fresh'],['medium','fresh'],['medium','fresh'],
            ['medium','fresh'],['strong','fresh'],['strong','fresh'],['medium','fatigued'],['medium','fatigued']];
const GUIA={light:'~20 % del máximo',medium:'~50 % del máximo',strong:'lo más fuerte posible'};
const RE_SUJ=/^P\d{3}$/, RE_OP=/^OP\d{2}$/, RE_PL=/^E\d{2}$/;
const VER_R=FSR*5, VER_RMS=10*FSR/PASO_RMS;      // visible: 5 s raw, 10 s RMS

const $=id=>document.getElementById(id);
let desdeR=0, fallos=0, vivoR=[], vivoRms=[], ult=new Float64Array(VENT), nUlt=0, cRms=0;
let smp=null;      // running sample      {meta, ini, v:[], lab}
let calCap=null;   // running calibration {ids, t, ini, v:[], lab}
let tasa={n:0,t:Date.now(),fs:0};

// localStorage may fail (private mode): the page still works without it
const ls={get:(k,d)=>{try{const v=localStorage.getItem('semgia_'+k);return v===null?d:JSON.parse(v);}catch(e){return d;}},
          set:(k,v)=>{try{localStorage.setItem('semgia_'+k,JSON.stringify(v));}catch(e){}}};

// ---------------- calculations ----------------
// RMS of a window after subtracting its own mean (same as semgia.processing.features)
function rmsDe(a,i0,n){
  let m=0; for(let i=0;i<n;i++) m+=a[i0+i]; m/=n;
  let s=0; for(let i=0;i<n;i++){ const d=a[i0+i]-m; s+=d*d; } return Math.sqrt(s/n);
}
function nuevaMuestra(v){                         // live RMS every 20 ms over the last 200 ms
  ult[nUlt%VENT]=v; nUlt++;
  if(nUlt>=VENT&&++cRms>=PASO_RMS){ cRms=0; vivoRms.push(rmsDe(ult,0,VENT)); }
}
const calDe=p=>ls.get('cal_'+p,null);             // {rest,max} of a placement
function activacion(rms,c){ return c?Math.max(0,Math.min(150,100*(rms-c.rest)/(c.max-c.rest))):null; }
function cuantil(a,q){ const b=[...a].sort((x,y)=>x-y); return b.length?b[Math.min(b.length-1,Math.floor(q*(b.length-1)))]:0; }
function pasoDe(n,pasos){                          // step + seconds left at sample index n
  let fin=0; for(const [lab,s] of pasos){ fin+=s*FSR; if(n<fin) return {lab:lab,resta:(fin-n)/FSR}; }
  return {lab:pasos[pasos.length-1][0],resta:0};
}
// Calibration result: rest = median RMS of the rest step, max = 95th percentile of the max step
// (200 ms windows every 20 ms, first CAL_SALTAR samples of each step skipped)
function resultadoCal(v){
  const rep=[],mx=[]; let ini=0;
  for(const [st,s] of PASOS_CAL){
    const fin=ini+s*FSR;
    for(let i=ini+CAL_SALTAR;i+VENT<=fin;i+=PASO_RMS){ const r=rmsDe(v,i,VENT); if(st===1) rep.push(r); if(st===2) mx.push(r); }
    ini=fin;
  }
  const rest=cuantil(rep,.5), max=cuantil(mx,.95);
  return {rest:rest,max:max,ok:rest>0&&max>=CAL_MIN_RATIO*rest};
}

// ---------------- data from the ESP32 ----------------
async function sondear(){
  try{
    const r=await fetch('/datos?desdeR='+desdeR,{cache:'no-store'});
    procesar(await r.json()); fallos=0;
  }catch(e){ if(++fallos>3){ banner('Sin conexión con el ESP32: ¿conectado a la red SEMGIA-EMG?','#f87171'); abortar('se perdió la conexión'); } }
  setTimeout(sondear,150);
}
function procesar(j){
  if(j.ridx<desdeR){ vivoR=[]; abortar('el ESP32 se reinició'); }
  else if(j.r0!==desdeR&&desdeR>0) abortar('se perdieron datos (conexión lenta o pestaña en segundo plano)');
  let k=j.r0;
  for(const v of j.r){
    vivoR.push(v); nuevaMuestra(v);
    if(smp&&k>=smp.ini&&smp.v.length<N_MUESTRA) smp.v.push(v);
    if(calCap&&k>=calCap.ini&&calCap.v.length<N_CAL) calCap.v.push(v);
    k++;
  }
  desdeR=j.ridx;
  tasa.n+=j.r.length;
  const ahora=Date.now(); if(ahora-tasa.t>=2000){ tasa.fs=Math.round(tasa.n*1000/(ahora-tasa.t)); tasa.n=0; tasa.t=ahora; }
  banner('Conectado al ESP32 · '+(tasa.fs?tasa.fs+' muestras/s':'midiendo…'),'#4ade80');
  if(vivoR.length>VER_R) vivoR.splice(0,vivoR.length-VER_R);
  if(vivoRms.length>VER_RMS) vivoRms.splice(0,vivoRms.length-VER_RMS);
  if(smp&&smp.v.length>=N_MUESTRA) terminarMuestra();
  if(calCap&&calCap.v.length>=N_CAL) terminarCalibracion();
  actualizarUI();
}
function banner(t,c){ const b=$('banner'); b.textContent=t; b.style.background=c; }
const f0=v=>v.toFixed(0);

function actualizarUI(){
  const r=vivoRms[vivoRms.length-1], c=calDe(ids().p);
  if(r!==undefined){ $('vRms').textContent=r.toFixed(1); const a=activacion(r,c); $('vPct').textContent=a===null?'–':Math.round(a)+' %'; }
  if(vivoR.length) $('vRaw').textContent=vivoR[vivoR.length-1];
  $('vCal').textContent=c?c.rest.toFixed(1)+' / '+c.max.toFixed(1):'–';
  actualizarCue();
}

// ---------------- plots ----------------
const OSC={bg:'#1e293b',grid:'#334155',tx:'#94a3b8',linea:'#38bdf8',mut:'#94a3b8',amar:'#facc15'};
function ejes(ctx,W,H,m,lo,hi,etqY,nx,etqX){
  const pw=W-m.l-m.r, ph=H-m.t-m.b, Y=v=>m.t+ph*(1-(v-lo)/(hi-lo));
  ctx.fillStyle=OSC.bg; ctx.fillRect(0,0,W,H); ctx.font='12px system-ui'; ctx.lineWidth=1;
  for(let g=0;g<=4;g++){ const v=lo+(hi-lo)*g/4,y=Y(v);
    ctx.strokeStyle=OSC.grid; ctx.beginPath(); ctx.moveTo(m.l,y); ctx.lineTo(m.l+pw,y); ctx.stroke();
    ctx.fillStyle=OSC.tx; ctx.textAlign='right'; ctx.fillText(v.toFixed(0),m.l-6,y+4); }
  ctx.textAlign='center'; for(let g=0;g<=nx;g++) ctx.fillText(etqX(g/nx),m.l+pw*g/nx,H-8);
  ctx.save(); ctx.translate(14,m.t+ph/2); ctx.rotate(-Math.PI/2); ctx.fillText(etqY,0,0); ctx.restore();
  return {pw:pw,ph:ph,Y:Y};
}
// min/max per pixel, newest sample at the right edge
function trazo(ctx,vals,slots,m,pw,Y){
  const N=vals.length, X=k=>m.l+pw*k/(slots-1), k0=slots-N; let px0=-1,mn=0,mx=0;
  ctx.strokeStyle=OSC.linea; ctx.lineWidth=1.4; ctx.beginPath();
  for(let k=0;k<=N;k++){
    const px=k<N?Math.round(X(k0+k)):-2;
    if(px!==px0){ if(px0>=0){ ctx.moveTo(px0,Y(mx)); ctx.lineTo(px0,Y(mn)); } if(k<N){ px0=px; mn=mx=vals[k]; } }
    else{ if(vals[k]<mn)mn=vals[k]; if(vals[k]>mx)mx=vals[k]; }
  }
  ctx.stroke();
}
function dibujarRms(ctx,W,H){
  const c=calDe(ids().p), m={l:58,r:12,t:10,b:24};
  let hi=10; for(const v of vivoRms) if(v>hi) hi=v; if(c) hi=Math.max(hi,c.max); hi*=1.1;
  const e=ejes(ctx,W,H,m,0,hi,'RMS',5,f=>(f*10-10).toFixed(0)+' s');
  if(c) for(const [v,t] of [[c.rest,'reposo'],[c.max,'máx. calibración']]){
    const y=e.Y(v); ctx.strokeStyle=OSC.amar; ctx.setLineDash([6,4]); ctx.beginPath(); ctx.moveTo(m.l,y); ctx.lineTo(m.l+e.pw,y); ctx.stroke();
    ctx.setLineDash([]); ctx.fillStyle=OSC.amar; ctx.textAlign='left'; ctx.fillText(t,m.l+6,y-4); }
  trazo(ctx,vivoRms,VER_RMS,m,e.pw,e.Y);
}
function dibujarRaw(ctx,W,H){
  let mu=0; for(const v of vivoR) mu+=v; mu=vivoR.length?mu/vivoR.length:0;
  const vals=vivoR.map(v=>v-mu); let a=10; for(const v of vals){ const x=Math.abs(v); if(x>a)a=x; } a*=1.1;
  const m={l:58,r:12,t:10,b:24}, e=ejes(ctx,W,H,m,-a,a,'EMG (ADC)',5,f=>(f*5-5).toFixed(0)+' s');
  trazo(ctx,vals,VER_R,m,e.pw,e.Y);
}
const cv=$('cv'), cx=cv.getContext('2d'), cvR=$('cvR'), cxR=cvR.getContext('2d');
function ajustar(c,x){ const d=window.devicePixelRatio||1, w=c.clientWidth, h=c.clientHeight;
  if(c.width!==Math.round(w*d)||c.height!==Math.round(h*d)){ c.width=Math.round(w*d); c.height=Math.round(h*d); }
  x.setTransform(d,0,0,d,0,0); return [w,h]; }
function render(){ dibujarRms(cx,...ajustar(cv,cx)); dibujarRaw(cxR,...ajustar(cvR,cxR)); requestAnimationFrame(render); }

// ---------------- IDs, counter, form ----------------
function ids(){ return {s:$('fSuj').value.trim().toUpperCase(),o:$('fOp').value.trim().toUpperCase(),p:$('fPl').value.trim().toUpperCase()}; }
function idsValidos(d){
  if(!RE_SUJ.test(d.s)){ msg('Sujeto debe ser como P001 (seudónimo, nunca el nombre).','err'); return false; }
  if(!RE_OP.test(d.o)){ msg('Operador debe ser como OP01.','err'); return false; }
  if(!RE_PL.test(d.p)){ msg('Colocación debe ser como E01 (número nuevo cada vez que se ponen electrodos).','err'); return false; }
  return true;
}
function msg(t,cls){ const m=$('msgRecol'); m.textContent=t; m.className=cls||''; }
const cuenta=p=>ls.get('cnt_'+p,0);
function mostrarContador(){
  const d=ids();
  $('vCnt').textContent=RE_PL.test(d.p)?(Math.min(cuenta(d.p)+1,99)+' de '+N_PLAN):'–';
  if(!smp&&!calCap&&RE_PL.test(d.p))
    msg(calDe(d.p)?d.p+': calibración guardada ✓ → «2· Tomar muestra»':d.p+': sin calibración todavía → «1· Calibrar colocación»',calDe(d.p)?'ok':'');
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

// ---------------- beeps ----------------
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
function listoParaGrabar(d){
  if(!idsValidos(d)) return false;
  if(fallos>3||!desdeR){ msg('Sin conexión con el ESP32.','err'); return false; }
  if(smp||calCap){ msg('Espere a que termine lo que se está grabando.','err'); return false; }
  return true;
}

// ---------------- calibration (once per placement) ----------------
$('bCal').onclick=()=>{
  const d=ids(); if(!listoParaGrabar(d)) return;
  if(calDe(d.p)&&!confirm(d.p+' ya tiene calibración. Si se volvieron a poner los electrodos, use una colocación NUEVA (E02…). ¿Calibrar '+d.p+' de nuevo?')) return;
  calCap={ids:d,t:new Date(),ini:desdeR,v:[],lab:-1};
  pitido(660,200); msg('Calibrando '+d.p+'…');
  $('cueStop').textContent='Cancelar calibración'; $('cue').hidden=false; actualizarCue();
};
function terminarCalibracion(){
  const c=calCap; calCap=null; $('cue').hidden=true;
  const r=resultadoCal(c.v), d=c.ids;
  if(!r.ok){ pitido(220,600);
    return msg('✗ Calibración rechazada: el máximo ('+r.max.toFixed(1)+') no llega a '+CAL_MIN_RATIO+'× el reposo ('+r.rest.toFixed(1)
      +'). Revise el sensor y que el sujeto contraiga al máximo. Calibre de nuevo.','err'); }
  bajarJSON({format:'semgia-calib-2',placement_id:d.p,subject_id:d.s,operator_id:d.o,
             start_time_utc:c.t.toISOString().slice(0,19)+'+00:00',sampling_rate_hz:FSR,
             rest_rms:+r.rest.toFixed(2),max_rms:+r.max.toFixed(2),values:c.v},
            'semgia_calib_'+d.p+'_'+sello()+'.json');
  ls.set('cal_'+d.p,{rest:r.rest,max:r.max});
  pitido(880,150,2); mostrarContador();
  msg('✓ Calibración de '+d.p+' descargada (reposo '+r.rest.toFixed(1)+', máx. '+r.max.toFixed(1)+'). Ahora: «2· Tomar muestra».','ok');
}

// ---------------- samples (24 s) ----------------
$('bMuestra').onclick=()=>{
  const d=ids(); if(!listoParaGrabar(d)) return;
  const n=cuenta(d.p), plan=PLAN[Math.min(n,PLAN.length-1)], u=ls.get('meta',{});
  $('mMus').value=u.muscle||MUSCULOS[0]; $('mLado').value=u.side||LADOS[0];
  $('mSens').value=u.sensor_id||'DFRobot-SEN0240'; $('mElec').value=u.electrode_type||'dry (built-in)';
  $('mPNot').value=u.placement_notes||''; $('mNot').value='';
  $('mEsf').value=plan[0]; $('mCond').value=plan[1];
  $('dlgIds').textContent=d.s+' · '+d.o+' · colocación '+d.p+' · muestra '+(n+1)+' de '+N_PLAN;
  $('dlgPlan').textContent='Plan (protocolo) para la muestra '+(n+1)+': '+plan[0]+' · '+plan[1]
    +(plan[1]==='fatigued'?' → antes: contracción fuerte ~60 s, luego grabar enseguida.':'');
  $('dlgAviso').textContent=(calDe(d.p)?'':'Aviso: '+d.p+' no tiene calibración en este navegador. ')
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
  smp={meta:meta,ini:desdeR,v:[],lab:-1};          // starts with the next sample from the ESP32
  pitido(660,200); msg('Grabando muestra…');
  $('cueStop').textContent='Cancelar muestra'; $('cue').hidden=false; actualizarCue();
};
$('cueStop').onclick=()=>abortar('cancelada por el operador');
function terminarMuestra(){
  const m=smp; smp=null; $('cue').hidden=true;
  // labels 0/1 are NOT in the file: import_web.py computes them from the row number (timer)
  bajarJSON({format:'semgia-sample-1',metadata:m.meta,values:m.v.slice(0,N_MUESTRA)},
            'semgia_sample_'+m.meta.placement_id+'_'+sello()+'.json');
  const p=m.meta.placement_id, n=cuenta(p)+1;
  ls.set('cnt_'+p,n); pitido(880,150,2); mostrarContador();
  msg('✓ Muestra '+n+' de '+N_PLAN+' ('+p+') descargada. Descanse ~10 s. En el PC: python scripts/import_web.py','ok');
}
function abortar(motivo){
  if(!smp&&!calCap) return;
  const que=smp?'Muestra':'Calibración'; smp=null; calCap=null; $('cue').hidden=true; pitido(220,600);
  msg('✗ '+que+' NO guardada: '+motivo+'. Repítala.','err');
}

// ---------------- full-screen cue ----------------
const CUE_SMP={0:['REPOSO','relaje el músculo','#15803d'],1:['¡CONTRAIGA!','','#b91c1c']};
const CUE_CAL={0:['PREPÁRESE','brazo apoyado y relajado','#1e40af'],1:['REPOSO','relaje el músculo por completo','#15803d'],
               2:['¡MÁXIMO!','contraiga lo más fuerte posible','#b91c1c']};
function actualizarCue(){
  const x=smp||calCap; if(!x) return;
  const n=x.v.length, f=pasoDe(n,smp?PASOS:PASOS_CAL), [txt,sub,col]=(smp?CUE_SMP:CUE_CAL)[f.lab];
  if(f.lab!==x.lab){ if(x.lab!==-1) pitido(f.lab===(smp?1:2)?1047:523,300); x.lab=f.lab; }   // high = contract
  $('cue').style.background=col; $('cueTxt').textContent=txt; $('cueSeg').textContent=Math.ceil(f.resta)+' s';
  $('cueBar').style.width=(100*n/(smp?N_MUESTRA:N_CAL))+'%';
  if(smp){
    const d=smp.meta, a=activacion(vivoRms[vivoRms.length-1]||0,calDe(d.placement_id));
    $('cueInfo').textContent='Muestra '+(cuenta(d.placement_id)+1)+' de '+N_PLAN+' · '+d.placement_id+' · '+d.effort+(d.condition==='fatigued'?' · fatigado':'');
    $('cueSub').textContent=f.lab?GUIA[d.effort]+(a===null?'':' · activación '+Math.round(a)+' %'):sub;
  }else{
    $('cueInfo').textContent='Calibración · colocación '+calCap.ids.p;
    $('cueSub').textContent=sub;
  }
}
function sello(){ return new Date().toISOString().slice(0,19).replace(/[-:]/g,'')+'Z'; }
function descargar(blob,nombre){
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=nombre;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href),2000);
}
function bajarJSON(obj,nombre){ descargar(new Blob([JSON.stringify(obj)],{type:'application/json'}),nombre); }
window.addEventListener('beforeunload',e=>{ if(smp||calCap){ e.preventDefault(); e.returnValue=''; } });

mostrarContador(); sondear(); render();
</script></body></html>)rawliteral";
