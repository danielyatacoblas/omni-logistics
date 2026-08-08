'use strict';
const $ = (id) => document.getElementById(id);
const api = (p, o) => fetch(p, o).then(r => r.json());

/* ── Iconos profesionales (SVG inline estilo Lucide, sin CDN ni emojis) ── */
const ICONS = {
  scan:'<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>',
  cpu:'<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
  clock:'<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  film:'<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18M3 7.5h4M3 12h18M3 16.5h4M17 3v18M17 7.5h4M17 16.5h4"/>',
  play:'<polygon points="6 3 20 12 6 21 6 3"/>',
  stop:'<rect width="14" height="14" x="5" y="5" rx="2"/>',
  undo:'<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
  trash:'<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6M14 11v6"/>',
  users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  user:'<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  route:'<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
  truck:'<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M14 9h4l4 4v4a1 1 0 0 1-1 1h-1"/><circle cx="7.5" cy="18.5" r="2.5"/><circle cx="17.5" cy="18.5" r="2.5"/>',
  layers:'<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 12.5-9.17 4.16a2 2 0 0 1-1.66 0L2 12.5"/><path d="m22 17.5-9.17 4.16a2 2 0 0 1-1.66 0L2 17.5"/>',
  download:'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
  alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4M12 17h.01"/>',
  activity:'<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  timer:'<line x1="10" x2="14" y1="2" y2="2"/><line x1="12" x2="12" y1="14" y2="9"/><circle cx="12" cy="14" r="8"/>',
  package:'<path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73Z"/><path d="M3.3 7 12 12l8.7-5"/><path d="M12 22V12"/>',
  dock:'<path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/><path d="M9 21v-6h6v6"/><path d="M9 10h.01M15 10h.01"/>',
  shield:'<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1 1 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
  flame:'<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
  zap:'<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
  cone:'<path d="M16.05 10.966a5 2.5 0 0 1-8.1 0"/><path d="m16.923 14.049 4.48 2.04a1 1 0 0 1 .001 1.831l-8.574 3.9a2 2 0 0 1-1.66 0l-8.574-3.91a1 1 0 0 1 0-1.83l4.484-2.04"/><path d="M16.949 14.14a5 2.5 0 1 1-9.9 0L10.063 3.5a2 2 0 0 1 3.874 0z"/>',
  settings:'<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
  chart:'<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9M13 17V5M8 17v-3"/>',
  'map-pin':'<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  'mouse-pointer':'<path d="M12.586 12.586 19 19"/><path d="M3.688 3.037a.497.497 0 0 0-.651.651l6.5 15.999a.501.501 0 0 0 .947-.062l1.569-6.083a2 2 0 0 1 1.448-1.479l6.124-1.579a.5.5 0 0 0 .063-.947z"/>',
  x:'<path d="M18 6 6 18M6 6l12 12"/>',
};
function svg(n){ return `<svg viewBox="0 0 24 24">${ICONS[n]||''}</svg>`; }
function hydrateIcons(root){ (root||document).querySelectorAll('i[data-ico]').forEach(el=>{ if(!el.firstChild) el.innerHTML=svg(el.dataset.ico); }); }

const PALETTE = ['#12A06E','#2D6CDF','#E19100','#7C5CE0','#E5484D','#0EA5A5','#F26A21'];
const SEV = { critical:'#E5484D', warning:'#E19100', info:'#2D6CDF', ok:'#12A06E' };
const MODCOL = { 'Ocupación':'#12A06E', 'Muelle':'#2D6CDF', 'Seguridad':'#E5484D', 'Trazabilidad':'#7C5CE0', 'Incendio':'#E5484D' };
const GAUGE_C = 2 * Math.PI * 52;

/* Config por apartado: herramienta, título, gráfica propia */
const UC = {
  ocupacion:    { tool:'zone', drawLbl:'Dibujar zona',  ph:'zona de almacenaje', title:'Ocupación por zona',
                  gaugeCol:'#12A06E', need:()=>st.zones.length>0, msg:'Primero dibuja al menos una zona de almacenaje',
                  chart:{ title:'Pallets detectados en el tiempo',
                          series:[{k:'pallets',c:'#12A06E',l:'Pallets'}] } },
  muelle:       { tool:'line', drawLbl:'Dibujar línea', ph:'línea de muelle', title:'Muelle: carga / descarga',
                  gaugeCol:'#2D6CDF', need:()=>!!st.line, msg:'Primero dibuja la línea del muelle',
                  chart:{ title:'Cruces acumulados del muelle',
                          series:[{k:'in',c:'#12A06E',l:'Cargado (IN)'},{k:'out',c:'#E19100',l:'Descargado (OUT)'}] } },
  seguridad:    { tool:'zone', drawLbl:'Marcar pasillo', ph:'pasillo a vigilar (opcional)', title:'Seguridad industrial',
                  gaugeCol:'#E5484D', need:()=>true, msg:'',
                  chart:{ title:'Personas y montacargas en escena',
                          series:[{k:'persons',c:'#E19100',l:'Personas'},{k:'forklifts',c:'#2D6CDF',l:'Montacargas'},{k:'events',c:'#E5484D',l:'Alertas acum.'}] } },
  trazabilidad: { tool:'zone', drawLbl:'Dibujar zona',  ph:'zona (opcional)', title:'Trazabilidad de montacargas',
                  gaugeCol:'#7C5CE0', need:()=>true, msg:'',
                  chart:{ title:'Montacargas activos en el tiempo',
                          series:[{k:'forklifts',c:'#2D6CDF',l:'Montacargas'},{k:'persons',c:'#E19100',l:'Personas'}] } },
};

const st = { usecase:'ocupacion', video:null, tool:null, line:null, zones:[], draft:[],
  streaming:false, statusTimer:null, dangerPct:7, lastTl:[], fireEvents:0, audio:null,
  modelInfo:[], modelDefaults:{}, cfg:loadCfg(), runNow:new Set() };

function loadCfg(){ try{ return JSON.parse(localStorage.getItem('omni_logi_cfg'))||{}; }catch(e){ return {}; } }
function saveCfg(){ localStorage.setItem('omni_logi_cfg', JSON.stringify(st.cfg)); }
function ucCfg(){
  const uc=st.usecase;
  if(!st.cfg[uc]) st.cfg[uc]={ models:null, charts:{activity:true, objects:true, panel:true} };
  return st.cfg[uc];
}
function activeModels(){ return ucCfg().models || st.modelDefaults[st.usecase] || []; }

/* ── sirena de incendio (WebAudio, sin archivos) ── */
function siren(){
  try{
    st.audio = st.audio || new (window.AudioContext||window.webkitAudioContext)();
    const ctx=st.audio, t0=ctx.currentTime;
    for(let i=0;i<3;i++){
      const o=ctx.createOscillator(), g=ctx.createGain();
      o.type='square'; o.connect(g); g.connect(ctx.destination);
      const a=t0+i*0.45;
      o.frequency.setValueAtTime(880,a); o.frequency.linearRampToValueAtTime(640,a+0.4);
      g.gain.setValueAtTime(0.0001,a); g.gain.exponentialRampToValueAtTime(0.12,a+0.03);
      g.gain.exponentialRampToValueAtTime(0.0001,a+0.42);
      o.start(a); o.stop(a+0.44);
    }
  }catch(e){}
}

/* ── init ──────────────────────────────────────────────────────────────── */
(async function init(){
  hydrateIcons();
  const [d, m] = await Promise.all([api('/api/videos?usecase=ocupacion'), api('/api/models')]);
  $('devicePill').textContent = d.device;
  st.dangerPct = d.safe_dist_pct || 7;
  st.modelInfo = m.models||[]; st.modelDefaults = m.defaults||{};
  fillVideos(d.videos);
  tickClock(); setInterval(tickClock, 1000);
  applyUsecase();
  if (d.videos.length) await loadVideo(d.videos[0]);
})();
function tickClock(){ $('clock').textContent = new Date().toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit',second:'2-digit'}); }
function fillVideos(vids){
  const sel=$('videoSelect');
  sel.innerHTML = vids.length
    ? vids.map(v=>`<option value="${v}">${v.split('/').pop()}</option>`).join('')
    : '<option value="">(coloca .mp4 en videos/'+({ocupacion:'01_ocupacion',muelle:'02_muelle',seguridad:'03_seguridad',trazabilidad:'04_trazabilidad'}[st.usecase]||'')+')</option>';
}

/* ── apartado (rail) ───────────────────────────────────────────────────── */
document.querySelectorAll('.rail-btn').forEach(b=>b.onclick=async()=>{
  if(st.streaming){ toast('Detén el proceso para cambiar de módulo'); return; }
  document.querySelectorAll('.rail-btn').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  st.usecase=b.dataset.uc; st.tool=null; st.draft=[];
  applyUsecase();
  const d=await api('/api/videos?usecase='+st.usecase);
  fillVideos(d.videos);
  if(d.videos.length) await loadVideo(d.videos[0]);
  else {
    // sin videos en este apartado: no heredar NADA del anterior
    st.video=null; st.zones=[]; st.line=null; st.draft=[];
    $('frameImg').style.display='none'; $('placeholder').style.display='flex';
    renderChips(); redraw();
  }
});
function applyUsecase(){
  const u=UC[st.usecase];
  $('drawLbl').textContent=u.drawLbl;
  $('phCfg').textContent=u.ph;
  $('ucTitle').textContent=u.title;
  $('stageModule').textContent=u.title;
  $('drawBtn').dataset.active='0';
  $('drawBtn').style.display=u.tool?'':'none';
  document.querySelectorAll('.mod-panel').forEach(p=>{ const on=p.dataset.mod===st.usecase; p.style.display=(on&&ucCfg().charts.panel)?'':'none'; if(on)p.classList.add('fade'); });
  // el fuego SOLO existe en el apartado seguridad
  $('fireCard').style.display = st.usecase==='seguridad' ? '' : 'none';
  $('gaugeProg').setAttribute('stroke', u.gaugeCol);
  $('chartTitle').textContent=u.chart.title;
  $('chartLegend').innerHTML=u.chart.series.map(s=>`<span><i style="background:${s.c}"></i>${s.l}</span>`).join('');
  buildCfgPop();
  applyChartVisibility();
  renderChips(); redraw(); resetModuleUI();
}
function applyChartVisibility(){
  const c=ucCfg().charts;
  $('chartCard').style.display=c.activity?'flex':'none';
  $('objCard').style.display=c.objects?'':'none';
}
function resetStats(){
  setGauge(0,'0','%','—','Sin datos aún', UC[st.usecase].gaugeCol);
  ['tA','tB','tC'].forEach(id=>{ const el=$(id); el.textContent='0'; el.dataset.n='0'; });
  st.lastTl=[]; drawFlow([]);
}

/* Reset TOTAL al cambiar de apartado: cada apartado es independiente,
   nada del anterior (fuego, alertas, contadores, stream) debe quedar. */
function resetModuleUI(){
  resetStats();
  // detener cualquier proceso/poll anterior
  if(st.statusTimer){ clearInterval(st.statusTimer); st.statusTimer=null; }
  fetch('/api/stop',{method:'POST'}).catch(()=>{});
  st.streaming=false; stopStream();
  $('startBtn').disabled=false; $('stopBtn').disabled=true;
  $('procOverlay').style.display='none';
  $('progressBar').style.width='0%';
  $('stageFps').style.display='none'; $('stageLive').style.display='none';
  $('liveDot').className='dot'; $('liveTxt').textContent='En espera';
  // incendio: banner + tarjeta a estado base
  st.fireEvents=0; st.runNow=new Set();
  $('fireBanner').style.display='none';
  $('fireDot').style.background='#12A06E'; $('fireDot').style.boxShadow='0 0 0 4px rgba(18,160,110,.16)';
  $('fireLbl').textContent='Sin fuego ni humo'; $('fireLbl').style.color='#12A06E';
  $('fireSub').textContent='monitoreo continuo activo';
  $('fireCard').classList.remove('on');
  // listas y paneles a cero
  renderAlerts([]); renderObjects([],0);
  renderOcc([]); renderTrace([]); renderSafety({},[]);
  ['ioIn','ioOut','ioThr'].forEach(id=>$(id).textContent='0');
  ['secFalls','secSpeed','secObs'].forEach(id=>{ const el=$(id); el.textContent='0'; el.dataset.n='0'; });
}

/* ── MODELOS del apartado: chips visibles para activar/desactivar ─────── */
const MODEL_ICO={pallet:'package',forklift:'truck',fire:'flame',ppe:'shield'};
function buildModelChips(runningSet){
  const act=new Set(activeModels());
  const run=runningSet||new Set();
  const def=new Set(st.modelDefaults[st.usecase]||[]);
  $('modelChips').innerHTML=st.modelInfo.map(m=>{
    const on=act.has(m.key), dis=!m.available;
    const cls='mchip'+(on?' on':'')+(dis?' dis':'')+(run.has(m.key)?' run':'');
    const tag=run.has(m.key)?'corriendo':(on?'activo':'off');
    return `<button class="${cls}" data-mk="${m.key}" ${dis?'disabled':''} title="${m.desc}${dis?' · sin pesos':''}${def.has(m.key)?' · recomendado aquí':''}">
      <i data-ico="${MODEL_ICO[m.key]||'cpu'}"></i><span class="ml">${m.label}</span>
      <span class="st">${tag}</span></button>`;
  }).join('');
  hydrateIcons($('modelChips'));
  $('modelsState').textContent = run.size ? `${run.size} corriendo` : `${act.size} activos`;
  $('modelsState').classList.toggle('live', run.size>0);
  $('modelChips').querySelectorAll('.mchip').forEach(el=>el.onclick=()=>{
    const k=el.dataset.mk; const cur=new Set(activeModels());
    if(cur.has(k)){ if(cur.size<=1){ toast('Debe quedar al menos un modelo activo'); return; } cur.delete(k); }
    else cur.add(k);
    ucCfg().models=[...cur]; saveCfg(); buildModelChips(st.runNow);
    if(st.streaming) toast('El cambio de modelos se aplica al volver a Procesar');
  });
}

/* ── config: filtro de gráficas ────────────────────────────────────────── */
$('cfgBtn').onclick=(e)=>{ e.stopPropagation(); const p=$('cfgPop'); p.style.display=p.style.display==='none'?'block':'none'; };
document.addEventListener('click',(e)=>{ if(!e.target.closest('.cfg-wrap')) $('cfgPop').style.display='none'; });
function buildCfgPop(){
  buildModelChips(st.runNow);
  const c=ucCfg().charts;
  $('cfgCharts').innerHTML=[
    ['activity','Gráfica de actividad'],['objects','Objetos activos'],['panel','Panel del apartado'],
  ].map(([k,l])=>`<label><input type="checkbox" data-ck="${k}" ${c[k]?'checked':''}/> <b>${l}</b></label>`).join('');
  $('cfgCharts').querySelectorAll('input').forEach(el=>el.onchange=()=>{
    ucCfg().charts[el.dataset.ck]=el.checked; saveCfg(); applyChartVisibility();
    document.querySelectorAll('.mod-panel').forEach(p=>{ if(p.dataset.mod===st.usecase) p.style.display=ucCfg().charts.panel?'':'none'; });
  });
}

/* ── carga de video ────────────────────────────────────────────────────── */
async function loadVideo(name){
  st.video=name; st.streaming=false; stopStream();
  $('placeholder').style.display='none';
  const img=$('frameImg'); img.style.display='block';
  img.onload=()=>{ sizeEditor(); redraw(); };
  img.src=`/api/video/${encodeURIComponent(name)}/frame?t=${Date.now()}`;
  const cfg=await api(`/api/video/${encodeURIComponent(name)}/zones`);
  st.line=cfg.line||null;
  st.zones=(cfg.zones||[]).map((z,i)=>({...z,color:z.color||PALETTE[i%PALETTE.length]}));
  st.draft=[]; renderChips(); redraw();
}
$('videoSelect').addEventListener('change', e=>{ if(e.target.value) loadVideo(e.target.value); });

/* ── geometría editor ──────────────────────────────────────────────────── */
function imgRect(){
  const img=$('frameImg'), vp=$('viewport');
  const cw=vp.clientWidth, ch=vp.clientHeight;
  const nw=img.naturalWidth||cw, nh=img.naturalHeight||ch;
  const s=Math.min(cw/nw, ch/nh), w=nw*s, h=nh*s;
  return { x:(cw-w)/2, y:(ch-h)/2, w, h };
}
function sizeEditor(){ const vp=$('viewport'), cv=$('editor'); cv.width=vp.clientWidth; cv.height=vp.clientHeight; }
window.addEventListener('resize', ()=>{ sizeEditor(); redraw(); drawFlow(st.lastTl||[]); });
function toNorm(cx,cy){ const r=imgRect(); return [(cx-r.x)/r.w,(cy-r.y)/r.h]; }
function toPx(nx,ny){ const r=imgRect(); return [r.x+nx*r.w, r.y+ny*r.h]; }
function visibleZones(){
  if(st.usecase==='seguridad') return st.zones.filter(z=>z.type==='pasillo');
  if(st.usecase==='ocupacion') return st.zones.filter(z=>z.type!=='pasillo');
  if(st.usecase==='trazabilidad') return st.zones;
  return [];
}

/* ── herramienta de dibujo ─────────────────────────────────────────────── */
$('drawBtn').onclick=()=>toggleTool();
function toggleTool(){
  const t=UC[st.usecase].tool; if(!t) return;
  st.tool=(st.tool===t)?null:t; st.draft=[];
  $('drawBtn').dataset.active=st.tool?'1':'0';
  const h=$('hint');
  if(st.tool==='line'){ h.style.display='block'; h.textContent='Haz clic en 2 puntos para la línea del muelle'; }
  else if(st.tool){ h.style.display='block'; h.textContent='Clic para marcar puntos · doble clic para cerrar la zona'; }
  else h.style.display='none';
  redraw();
}
$('editor').addEventListener('click', e=>{
  if(!st.tool||st.streaming) return;
  const r=$('editor').getBoundingClientRect();
  const [nx,ny]=toNorm(e.clientX-r.left, e.clientY-r.top);
  if(nx<0||nx>1||ny<0||ny>1) return;
  if(st.tool==='line'){ st.draft.push([nx,ny]); if(st.draft.length===2){ st.line={a:st.draft[0],b:st.draft[1]}; st.draft=[]; toggleTool(); afterEdit(); } }
  else st.draft.push([nx,ny]);
  redraw();
});
$('editor').addEventListener('dblclick', e=>{
  if(!st.tool||st.tool==='line'||st.streaming) return;
  if(st.draft.length<3){ toast('Marca al menos 3 puntos'); return; }
  const esPasillo = st.usecase==='seguridad';
  const name=prompt(esPasillo?'Nombre del pasillo (ej. "Ruta de evacuación"):':'Nombre de la zona (ej. "Rack A"):');
  if(!name) return;
  const color=esPasillo?'#E19100':PALETTE[st.zones.length%PALETTE.length];
  st.zones.push({ id:'z'+(st.zones.length+1)+'_'+Date.now().toString(36), name, type:esPasillo?'pasillo':'ocupacion', color, points:st.draft.slice() });
  st.draft=[]; toggleTool(); afterEdit();
});
$('undoBtn').onclick=()=>{
  if(st.draft.length){ st.draft.pop(); redraw(); return; }
  if(st.usecase==='muelle'){ st.line=null; }
  else { const vis=visibleZones(); if(vis.length){ st.zones=st.zones.filter(z=>z!==vis[vis.length-1]); } }
  afterEdit();
};
$('clearBtn').onclick=()=>{
  if(st.usecase==='muelle') st.line=null;
  else if(st.usecase==='seguridad') st.zones=st.zones.filter(z=>z.type!=='pasillo');
  else if(st.usecase==='ocupacion') st.zones=st.zones.filter(z=>z.type==='pasillo');
  else st.zones=[];
  st.draft=[]; afterEdit();
};
function afterEdit(){ renderChips(); redraw(); }

/* ── overlay del editor ────────────────────────────────────────────────── */
function redraw(){
  const cv=$('editor'); if(!cv.width) sizeEditor();
  const ctx=cv.getContext('2d'); ctx.clearRect(0,0,cv.width,cv.height);
  if(st.streaming) return;
  visibleZones().forEach(z=>drawPoly(ctx,z.points,z.color,z.name));
  if(st.usecase==='muelle' && st.line) drawLine(ctx,st.line.a,st.line.b,'#E5484D','MUELLE');
  if(st.draft.length){
    if(st.tool==='line'&&st.draft.length===1){ const [x,y]=toPx(...st.draft[0]); dot(ctx,x,y,'#12A06E'); }
    else drawPoly(ctx,st.draft,'#12A06E','',true);
  }
}
function drawPoly(ctx,pts,color,label,dashed){
  if(!pts.length) return; ctx.save();
  ctx.beginPath(); pts.forEach((p,i)=>{ const [x,y]=toPx(...p); i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
  if(!dashed) ctx.closePath();
  ctx.fillStyle=hexA(color,.16); ctx.fill();
  ctx.lineWidth=2.5; ctx.strokeStyle=color; if(dashed)ctx.setLineDash([7,5]); ctx.stroke();
  pts.forEach(p=>{ const [x,y]=toPx(...p); dot(ctx,x,y,color); });
  if(label){ const [x,y]=toPx(...pts[0]); ctx.setLineDash([]); ctx.fillStyle=color; ctx.font='700 12px Inter,sans-serif'; ctx.fillText(label,x+5,y-7); }
  ctx.restore();
}
function drawLine(ctx,a,b,color,label){
  const [x1,y1]=toPx(...a),[x2,y2]=toPx(...b); ctx.save();
  ctx.strokeStyle=color; ctx.lineWidth=3.5; ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
  dot(ctx,x1,y1,color); dot(ctx,x2,y2,color);
  ctx.fillStyle=color; ctx.font='700 11px Inter,sans-serif'; ctx.fillText(label,x1,y1-9); ctx.restore();
}
function dot(ctx,x,y,c){ ctx.beginPath(); ctx.arc(x,y,4.5,0,7); ctx.fillStyle=c; ctx.fill(); ctx.lineWidth=2; ctx.strokeStyle='#fff'; ctx.stroke(); }
function hexA(h,a){ h=h.replace('#',''); return `rgba(${parseInt(h.slice(0,2),16)},${parseInt(h.slice(2,4),16)},${parseInt(h.slice(4,6),16)},${a})`; }

function renderChips(){
  const wrap=$('zoneChips'); let html='';
  if(st.usecase==='muelle'){ if(st.line) html+=chip('Línea de muelle','#E5484D','scan','line',0); }
  else if(st.usecase==='seguridad'){
    const pas=visibleZones();
    if(!pas.length) html+=`<span class="chip" style="background:${hexA('#E5484D',.08)};color:#E5484D;border-color:${hexA('#E5484D',.3)}"><i data-ico="shield"></i>toda la escena · pasillos opcionales</span>`;
    pas.forEach((z)=>{ const idx=st.zones.indexOf(z); html+=chip(z.name,z.color,'route','zone',idx); });
  }
  else visibleZones().forEach((z)=>{ const idx=st.zones.indexOf(z); html+=chip(z.name,z.color,z.type==='pasillo'?'route':'package','zone',idx); });
  wrap.innerHTML=html; hydrateIcons(wrap);
  $('noZones').style.display=html?'none':'inline';
  wrap.querySelectorAll('.x').forEach(el=>el.onclick=()=>{ const{kind,idx}=el.dataset; if(kind==='line')st.line=null; else st.zones.splice(+idx,1); afterEdit(); });
}
function chip(text,color,icon,kind,idx){
  return `<span class="chip" style="background:${hexA(color,.1)};color:${color};border-color:${hexA(color,.35)}"><i data-ico="${icon}"></i>${text}<span class="x" data-kind="${kind}" data-idx="${idx}"><i data-ico="x"></i></span></span>`;
}

/* ── start / stop ──────────────────────────────────────────────────────── */
$('startBtn').onclick=start; $('stopBtn').onclick=stop;
async function start(){
  if(!st.video){ toast('Elige un video'); return; }
  if(!UC[st.usecase].need()){ toast(UC[st.usecase].msg); if(!st.tool) toggleTool(); return; }
  await saveZones();
  const models=activeModels();
  const r=await api('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({video:st.video,conf:0.35,usecase:st.usecase,models})});
  if(r.error){ toast(r.error); return; }
  st.streaming=true; st.fireEvents=0; $('fireBanner').style.display='none'; redraw();
  $('frameImg').style.display='none';
  const s=$('stream'); s.style.display='block'; s.src='/stream?t='+Date.now();
  $('startBtn').disabled=true; $('stopBtn').disabled=false;
  $('liveDot').className='dot on'; $('liveTxt').textContent='Procesando';
  $('stageLive').style.display='inline-flex'; $('stageFps').style.display='block';
  $('procTxt').textContent='Cargando modelos…';
  $('procModels').textContent=(r.models||models).join(' + ');
  $('procOverlay').style.display='flex';
  if(st.statusTimer) clearInterval(st.statusTimer);
  st.statusTimer=setInterval(poll,450);
}
async function stop(){ await fetch('/api/stop',{method:'POST'}); finishUI(); }
function stopStream(){ const s=$('stream'); s.style.display='none'; s.src=''; }
function finishUI(){
  st.streaming=false;
  st.runNow=new Set(); buildModelChips(st.runNow);
  $('procOverlay').style.display='none';
  $('startBtn').disabled=false; $('stopBtn').disabled=true;
  $('liveDot').className='dot'; $('liveTxt').textContent='Listo';
  $('stageLive').style.display='none';
  if(st.statusTimer){ clearInterval(st.statusTimer); st.statusTimer=null; }
  if(st.video) $('videoSelect').value=st.video;
}
function saveZones(){ return fetch(`/api/video/${encodeURIComponent(st.video)}/zones`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({line:st.line,zones:st.zones})}); }

/* ── gauge + tiles ─────────────────────────────────────────────────────── */
function setGauge(frac,val,unit,lbl,sub,col){
  frac=Math.max(0,Math.min(1,frac));
  $('gaugeProg').setAttribute('stroke', col);
  $('gaugeProg').style.strokeDashoffset = GAUGE_C*(1-frac);
  $('gaugeUnit').textContent=unit;
  $('gaugeLbl').textContent=lbl; $('gaugeSub').innerHTML=sub;
  animNum($('gaugeVal'), val);
}
function tiles(a,al,b,bl,c,cl){
  animNum($('tA'),a); $('tAl').textContent=al;
  animNum($('tB'),b); $('tBl').textContent=bl;
  animNum($('tC'),c); $('tCl').textContent=cl;
}
function animNum(el,target){
  const t=(''+target); if(isNaN(parseFloat(t))){ el.textContent=t; return; }
  const to=parseFloat(t), from=parseFloat(el.dataset.n||'0'); if(from===to){ el.textContent=t; return; }
  el.dataset.n=to; const dec=t.includes('.'); const t0=performance.now(), dur=380;
  function step(now){ const k=Math.min(1,(now-t0)/dur); const v=from+(to-from)*(1-Math.pow(1-k,3));
    el.textContent=dec?v.toFixed(1):Math.round(v); if(k<1) requestAnimationFrame(step); }
  requestAnimationFrame(step);
}

/* ── poll / render ─────────────────────────────────────────────────────── */
async function poll(){
  const s=await api('/api/status');
  if(st.streaming){
    if(s.has_frame){ $('procOverlay').style.display='none'; }
    else { $('procOverlay').style.display='flex'; $('procTxt').textContent=s.model_ready?'Procesando…':'Cargando modelos…'; }
  }
  $('progressBar').style.width=(100*(s.progress||0))+'%';
  $('stageFps').textContent=`${s.proc_fps||0} fps`;
  $('liveTxt').textContent=`${s.video_time||''} / ${s.duration||''}`;

  // chips de modelos: marcar cuáles están CORRIENDO ahora
  const runNew=new Set(st.streaming?(s.active_models||[]):[]);
  if([...runNew].sort().join()!==[...st.runNow].sort().join()){ st.runNow=runNew; buildModelChips(st.runNow); }

  const zones=s.zones||[], dock=s.dock||{}, sf=s.safety||{};
  if(st.usecase==='ocupacion'){
    const avg=zones.length?zones.reduce((a,z)=>a+z.pct,0)/zones.length:0;
    const totalP=zones.reduce((a,z)=>a+z.count,0), full=zones.filter(z=>z.status!=='ok').length;
    setGauge(avg/100, Math.round(avg), '%', 'Ocupación media', `${totalP} pallets · ${full} zona(s) en alerta`, '#12A06E');
    tiles(s.pallets_now||0,'Pallets ahora', zones.length,'Zonas', (s.alerts||[]).length,'Alertas');
  } else if(st.usecase==='muelle'){
    setGauge(Math.min((dock.throughput||0)/60,1), dock.throughput||0, 'p/min', 'Throughput', `IN ${dock.in||0} · OUT ${dock.out||0} · ${s.video_time||''}`, '#2D6CDF');
    tiles(dock.in||0,'Cargado', dock.out||0,'Descargado', dock.net||0,'Neto');
  } else if(st.usecase==='seguridad'){
    const risk=sf.risk||'ok'; const frac=risk==='critical'?1:risk==='warning'?.55:.12;
    const totalInc=(sf.incidents||0)+(sf.falls_total||0)+(sf.speed_events||0)+(sf.obstructions||0)+(sf.ppe_events||0);
    setGauge(frac, totalInc, 'eventos', risk==='critical'?'Riesgo crítico':risk==='warning'?'Riesgo moderado':'Sin riesgo',
      `${sf.falls_total||0} caídas · ${sf.speed_events||0} velocidad · ${sf.obstructions||0} obstrucc. · ${sf.ppe_events||0} EPP`, SEV[risk]);
    tiles(s.forklifts_now||0,'Montacargas', s.persons_now||0,'Personas', sf.ppe_now||0,'Sin EPP ahora');
  } else {
    setGauge(Math.min((s.unique_forklifts||0)/10,1), s.unique_forklifts||0, 'unid', 'Montacargas rastreados',
      `${s.unique_persons||0} personas · ${s.active_count||0} activos ahora`, '#7C5CE0');
    tiles(s.active_count||0,'Activos', s.unique_persons||0,'Personas', (s.alerts||[]).length,'Alertas');
  }

  renderOcc(zones);
  $('ioIn').textContent=dock.in??0; $('ioOut').textContent=dock.out??0; $('ioThr').textContent=dock.throughput??0;
  st.lastTl=s.timeline||[];
  drawFlow(st.lastTl);
  renderSafety(sf, s.aisles||[]);
  if(st.usecase==='seguridad') renderFire(s.fire||{});
  renderTrace(zones);
  renderObjects(s.active_objects||[], s.active_count||0);
  renderAlerts(s.alerts||[]);
  if(s.finished){ finishUI(); toast('Procesamiento terminado · CSV listo'); }
}

/* ── incendio: banner + tarjeta + sirena (solo apartado seguridad) ────── */
function renderFire(f){
  const active=!!f.active;
  const banner=$('fireBanner');
  banner.style.display=active?'flex':'none';
  if(active){
    const donde=f.zone?`Fuego en ${f.zone}`:(f.fire_now?'Fuego detectado en la escena':'Humo detectado en la escena');
    $('fireWhere').textContent=`${donde} · evacuar y verificar`;
    $('fireCount').textContent=(f.fire_now||0)+(f.smoke_now||0);
  }
  const c=active?'#E5484D':(f.smoke_now?'#E19100':'#12A06E');
  $('fireDot').style.background=c; $('fireDot').style.boxShadow=`0 0 0 4px ${hexA(c,.16)}`;
  $('fireLbl').textContent=active?(f.fire_now?'FUEGO ACTIVO':'HUMO DETECTADO'):'Sin fuego ni humo';
  $('fireLbl').style.color=c;
  $('fireSub').textContent=active
    ? `${f.fire_now||0} foco(s) de fuego · ${f.smoke_now||0} de humo${f.zone?` · ${f.zone}`:''}`
    : `monitoreo continuo activo · ${f.events||0} alarma(s) en el video`;
  $('fireCard').classList.toggle('on', active);
  if((f.events||0)>st.fireEvents){ st.fireEvents=f.events; siren(); toast('ALERTA DE INCENDIO'); }
}

function renderOcc(zones){
  const el=$('occBars');
  if(!zones.length){ el.innerHTML='<div class="empty-box">Dibuja zonas de almacenaje para medir su ocupación.</div>'; return; }
  el.innerHTML=zones.map(z=>{ const c=z.status==='critical'?'#E5484D':z.status==='warning'?'#E19100':'#12A06E';
    const free=(z.free!==undefined&&z.free>0)?` · ${z.free} libre${z.free===1?'':'s'}`:'';
    return `<div class="bar-row"><div class="bh"><span class="nm"><span class="dot-s" style="background:${c}"></span>${z.name}</span><span style="color:${c}">${z.count}/${z.capacity} · ${Math.round(z.pct)}%${free}</span></div><div class="track"><div class="fill" style="width:${z.pct}%;background:${c}"></div></div></div>`; }).join('');
}
function renderSafety(sf, aisles){
  const risk=sf.risk||'ok';
  const c=SEV[risk];
  $('riskDot').style.background=c; $('riskDot').style.boxShadow=`0 0 0 4px ${hexA(c,.16)}`;
  let lbl='Sin riesgo';
  if(sf.fallen_now) lbl='PERSONA CAÍDA';
  else if(sf.aisles_blocked) lbl='Pasillo obstruido';
  else if(risk==='critical') lbl='Contacto crítico';
  else if(sf.ppe_now&&risk!=='critical') lbl='EPP incompleto';
  else if(sf.speeding_now&&risk==='warning'&&!sf.pairs_now) lbl='Velocidad excesiva';
  else if(risk==='warning') lbl='Proximidad peligrosa';
  $('riskLbl').textContent=lbl; $('riskLbl').style.color=c;
  $('riskSub').textContent=`dist. mín ${sf.min_gap??'—'}% · ${sf.pairs_now||0} pares · ${sf.ppe_now||0} sin EPP`;
  $('riskBox').style.borderColor=risk==='ok'?'var(--line2)':hexA(c,.4);
  animNum($('secFalls'), sf.falls_total||0);
  animNum($('secSpeed'), sf.speed_events||0);
  animNum($('secObs'), sf.obstructions||0);
  const el=$('aisleList');
  if(!aisles||!aisles.length){ el.innerHTML='<div class="row" style="grid-template-columns:1fr;color:var(--mut)">Dibuja pasillos/rutas de evacuación para vigilar que estén libres.</div>'; return; }
  let h='<div class="row head"><span>Pasillo</span><span>Estado</span><span></span></div>';
  aisles.forEach(a=>{ const ac=a.blocked?'#E5484D':'#12A06E';
    h+=`<div class="row"><span class="zn"><span class="dot-s" style="background:${ac}"></span>${a.name}</span><span class="zp" style="color:${ac}">${a.blocked?`OBSTRUIDO (${a.blockers})`:'libre'}</span><span></span></div>`; });
  el.innerHTML=h;
}
function renderTrace(zones){
  const el=$('traceTable');
  if(!zones.length){ el.innerHTML='<div class="row" style="grid-template-columns:1fr;color:var(--mut)">Zonas opcionales: dibújalas para medir el tiempo de cada montacargas.</div>'; return; }
  let h='<div class="row head"><span>Zona</span><span>Prom.</span><span>Ahora</span></div>';
  zones.forEach(z=>{ h+=`<div class="row"><span class="zn"><span class="dot-s" style="background:${z.color}"></span>${z.name}</span><span class="zc">${z.dwell_avg}</span><span class="zp">${z.forklifts_now}</span></div>`; });
  el.innerHTML=h;
}
function renderObjects(list,count){
  $('activeCount').textContent=count;
  const el=$('activePeople');
  if(!list.length){ el.innerHTML='<div class="empty-box">Sin objetos en cuadro todavía.</div>'; return; }
  const ICO={forklift:'truck',person:'user',pallet:'package'}, COL={forklift:'#2D6CDF',person:'#E19100',pallet:'#12A06E'};
  el.innerHTML=list.slice(0,12).map(o=>{ const c=COL[o.cls]||'#2D6CDF';
    return `<div class="obj" style="border-left-color:${c}"><span class="oico" style="color:${c}"><i data-ico="${ICO[o.cls]||'route'}"></i></span><div class="oi"><div class="on">${o.cls_es} <span style="color:${c}">#${o.id}</span></div><div class="om"><span><i data-ico="timer"></i>${o.dwell}</span><span><i data-ico="map-pin"></i>${o.zone||'en tránsito'}</span></div></div></div>`; }).join('');
  hydrateIcons(el);
}
function renderAlerts(al){
  $('alertCount').textContent=al.length;
  $('noAlerts').style.display=al.length?'none':'block';
  $('alertRows').innerHTML=[...al].reverse().slice(0,40).map(a=>`<div class="al ${a.severity}"><span class="at">${a.video_time}</span><div class="ax"><div class="ai"><span style="color:${MODCOL[a.modulo]||'#2D6CDF'}">${a.modulo}</span> · ${a.tipo}</div><div class="ad">${a.detalle}</div></div></div>`).join('');
}

/* ── gráfica del apartado (series propias por caso de uso) ─────────────── */
function drawFlow(tl){
  const cv=$('flowChart'); if(!cv||!cv.clientWidth) return;
  const series=UC[st.usecase].chart.series;
  const dpr=window.devicePixelRatio||1;
  const w=cv.clientWidth, h=cv.clientHeight; cv.width=w*dpr; cv.height=h*dpr;
  const ctx=cv.getContext('2d'); ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,w,h);
  const pad={l:24,r:6,t:8,b:14}, gw=w-pad.l-pad.r, gh=h-pad.t-pad.b;
  const maxT=tl.length?Math.max(1,tl[tl.length-1].t):10;
  let maxV=4;
  if(tl.length) maxV=Math.max(2,...tl.map(p=>Math.max(...series.map(s=>p[s.k]||0))));
  const X=t=>pad.l+(t/maxT)*gw, Y=v=>pad.t+gh-(v/maxV)*gh;
  ctx.strokeStyle='#EEF1F5'; ctx.fillStyle='#AEB6C4'; ctx.font='9px Inter'; ctx.lineWidth=1;
  for(let i=0;i<=4;i++){ const v=maxV*i/4, y=Y(v); ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(w-pad.r,y); ctx.stroke(); ctx.fillText(Math.round(v),3,y+3); }
  for(let i=0;i<=4;i++){ const t=maxT*i/4; ctx.fillText(`${Math.round(t)}s`, X(t)-6, h-2); }
  if(!tl.length){
    ctx.fillStyle='#C6CDD8'; ctx.font='11px Inter'; ctx.textAlign='center';
    ctx.fillText('esperando datos… (0)', pad.l+gw/2, pad.t+gh/2); ctx.textAlign='left';
    return;
  }
  const zero={t:0}; series.forEach(s=>zero[s.k]=0);
  const serie=tl[0].t>0?[zero,...tl]:tl;
  // área bajo la primera serie
  const s0=series[0];
  ctx.beginPath(); ctx.moveTo(X(0),Y(0)); serie.forEach(p=>ctx.lineTo(X(p.t),Y(p[s0.k]||0))); ctx.lineTo(X(serie[serie.length-1].t),Y(0)); ctx.closePath();
  const g=ctx.createLinearGradient(0,pad.t,0,pad.t+gh); g.addColorStop(0,hexA(s0.c,.20)); g.addColorStop(1,hexA(s0.c,.02)); ctx.fillStyle=g; ctx.fill();
  series.forEach((s,i)=>line(ctx,serie,X,Y,p=>p[s.k]||0,s.c,i===0?2:1.5));
}
function line(ctx,tl,X,Y,f,color,lw){ ctx.beginPath(); tl.forEach((p,i)=>{const x=X(p.t),y=Y(f(p)); i?ctx.lineTo(x,y):ctx.moveTo(x,y);}); ctx.strokeStyle=color; ctx.lineWidth=lw; ctx.stroke(); }

/* ── export / toast ────────────────────────────────────────────────────── */
$('exportBtn').onclick=()=>{ window.location='/api/export?t='+Date.now(); };
let toastT=null;
function toast(msg){ const el=$('toast'); el.textContent=msg; el.classList.add('show'); clearTimeout(toastT); toastT=setTimeout(()=>el.classList.remove('show'),2600); }
