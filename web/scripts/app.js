// QEL public reading adaptation, 2026-09-17; see README.md for exact changes.

(() => {
  const DATA = window.Q6_DATA;
  const $ = (sel) => document.querySelector(sel);
  const el = (tag, cls, txt) => { const x=document.createElement(tag); if(cls) x.className=cls; if(txt!=null) x.textContent=txt; return x; };
  const pitchColors = Object.fromEntries(["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"].map(p=>[p,"#83b7d5"]));
  const noteBase = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11};
  let state = { nodeIndex:0, verseIndex:0, wordIndex:0, playing:false, animT:0, rotation:0, zoom:1, drag:false, lastX:0, lastY:0, muted:{}, audio:null, master:null, scheduled:[], selectedMode:'node'};
  const canvas = $('#qmapCanvas'); const ctx = canvas.getContext('2d');
  function resize(){ const dpr=Math.min(devicePixelRatio||1,2); const r=canvas.getBoundingClientRect(); canvas.width=Math.max(300,Math.floor(r.width*dpr)); canvas.height=Math.max(240,Math.floor(r.height*dpr)); ctx.setTransform(dpr,0,0,dpr,0,0);} window.addEventListener('resize', resize); resize();
  const versesByRef = Object.fromEntries(DATA.core_verses.map(v=>[v.reference,v]));
  function nodeVerses(node){ return node.references.map(r=>versesByRef[r]).filter(Boolean); }
  function allEventsForNode(node){ return nodeVerses(node).flatMap(v=>v.word_motifs.flatMap(w=>w.events||[])); }
  function getSelectedNode(){return DATA.qmap_nodes[state.nodeIndex] || DATA.qmap_nodes[0];}
  function getSelectedVerse(){const n=getSelectedNode(); return nodeVerses(n)[state.verseIndex] || nodeVerses(n)[0] || DATA.core_verses[0];}
  function getSelectedWord(){const v=getSelectedVerse(); return (v.word_motifs||[])[state.wordIndex] || (v.word_motifs||[])[0];}
  function instFamily(inst){
    if(!inst) return 'strings_field';
    if(inst.includes('harp')) return 'harp_letter'; if(inst.includes('flute')) return 'flute_vowel_color'; if(inst.includes('pipe')) return 'pipe_ornament'; if(inst.includes('tambourine')) return 'tambourine_attack'; if(inst.includes('cymbal')) return 'cymbal_cadence'; if(inst.includes('voice')) return 'voice_cantillation'; if(inst.includes('lyre')) return 'lyre_witness'; if(inst.includes('trumpet')) return 'trumpet_luminary'; if(inst.includes('water')) return 'water_bowl'; return inst;
  }
  // Public reading adaptation: historical audio generation is disabled.
  // The recovered original remains in the historical source collection.
  function playTone(){ return; }
  function playEvents(){ return; }
  function stopAudio(){ return; }
  function playSelected(){ const w=getSelectedWord(); if(w && state.selectedMode==='word') playEvents(w.events||[]); else playEvents(allEventsForNode(getSelectedNode())); }
  function pitchToFreq(p, octave=3){ const pc=noteBase[p]??0; const midi=12*(octave+1)+pc; return 440*Math.pow(2,(midi-69)/12); }
  function draw(){
    const r=canvas.getBoundingClientRect(), w=r.width, h=r.height, cx=w/2, cy=h/2; ctx.clearRect(0,0,w,h); state.animT += .01;
    const min=Math.min(w,h); const base=min*.35*state.zoom;
    // background grid
    ctx.save(); ctx.translate(cx,cy); ctx.rotate(state.rotation*.2); ctx.strokeStyle='rgba(120,255,245,.08)'; ctx.lineWidth=1;
    for(let rr=base*.25; rr<base*1.35; rr+=base*.15){ ctx.beginPath(); ctx.arc(0,0,rr,0,Math.PI*2); ctx.stroke(); }
    for(let a=0;a<Math.PI*2;a+=Math.PI/12){ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(Math.cos(a)*base*1.35,Math.sin(a)*base*1.35);ctx.stroke();}
    ctx.restore();
    // source field glow
    const grad=ctx.createRadialGradient(cx,cy,0,cx,cy,base*.45); grad.addColorStop(0,'rgba(255,255,220,.95)'); grad.addColorStop(.14,'rgba(120,255,245,.55)'); grad.addColorStop(1,'rgba(120,255,245,0)'); ctx.fillStyle=grad; ctx.beginPath(); ctx.arc(cx,cy,base*.45,0,Math.PI*2); ctx.fill();
    // connections and nodes
    const nodes=DATA.qmap_nodes; const positions=[];
    for(let i=0;i<nodes.length;i++){
      const n=nodes[i]; const day=(nodeVerses(n)[0]?.day)||0; const ring=(.28+day*.08)*base; const angle = state.rotation + (i/nodes.length)*Math.PI*2 - Math.PI/2; const z=Math.sin(angle+state.animT*.2); const x=cx+Math.cos(angle)*ring*(1+.08*z); const y=cy+Math.sin(angle)*ring*.72*(1+.08*z); positions.push({x,y,angle,ring,z});
    }
    ctx.strokeStyle='rgba(255,255,255,.16)'; ctx.lineWidth=2; ctx.beginPath(); positions.forEach((p,i)=>{if(i===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y)}); ctx.stroke();
    positions.forEach((p,i)=>{ const n=nodes[i]; const active=i===state.nodeIndex; const color=pitchColors[n.aggregate_pitch] || '#78fff5';
      // thread to center
      ctx.strokeStyle=active?color:'rgba(120,255,245,.14)'; ctx.lineWidth=active?2.5:1; ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(p.x,p.y); ctx.stroke();
      const radius=(active?15:10)*(1+p.z*.12); ctx.fillStyle=color; ctx.shadowColor=color; ctx.shadowBlur=active?24:10; ctx.beginPath(); ctx.arc(p.x,p.y,radius,0,Math.PI*2); ctx.fill(); ctx.shadowBlur=0;
      ctx.fillStyle='rgba(0,0,0,.75)'; ctx.font='10px system-ui'; ctx.textAlign='center'; ctx.fillText(String(i).padStart(2,'0'),p.x,p.y+3);
      if(active){ ctx.strokeStyle=color; ctx.lineWidth=2; ctx.beginPath(); ctx.arc(p.x,p.y,radius+8+Math.sin(state.animT*5)*4,0,Math.PI*2); ctx.stroke(); }
    });
    // active label
    const n=getSelectedNode(); ctx.fillStyle='rgba(5,7,11,.65)'; ctx.fillRect(16,16,Math.min(520,w-32),70); ctx.fillStyle='#e8f4ff'; ctx.font='bold 17px system-ui'; ctx.textAlign='left'; ctx.fillText(`${n.id} · ${n.name}`,28,42); ctx.fillStyle='#8ea4b8'; ctx.font='12px system-ui'; ctx.fillText(`${n.scope} · pitch ${n.aggregate_pitch} · ${n.character_events} character events · ${n.note_events} notes`,28,64);
    requestAnimationFrame(draw);
  }
  function selectNode(i){ state.nodeIndex=(i+DATA.qmap_nodes.length)%DATA.qmap_nodes.length; state.verseIndex=0; state.wordIndex=0; state.selectedMode='node'; renderAll(); }
  canvas.addEventListener('pointerdown', e=>{state.drag=true; state.lastX=e.clientX; state.lastY=e.clientY;});
  window.addEventListener('pointerup',()=>state.drag=false); window.addEventListener('pointermove',e=>{ if(state.drag){state.rotation += (e.clientX-state.lastX)*.007; state.lastX=e.clientX; state.lastY=e.clientY;}});
  canvas.addEventListener('wheel',e=>{ e.preventDefault(); state.zoom=Math.max(.55,Math.min(1.8,state.zoom+(e.deltaY<0?.06:-.06)));},{passive:false});
  canvas.addEventListener('click', e=>{ if(state.drag) return; const rect=canvas.getBoundingClientRect(); const x=e.clientX-rect.left,y=e.clientY-rect.top; const w=rect.width,h=rect.height,cx=w/2,cy=h/2,base=Math.min(w,h)*.35*state.zoom; let best=-1,bd=9999; DATA.qmap_nodes.forEach((n,i)=>{const day=(nodeVerses(n)[0]?.day)||0; const ring=(.28+day*.08)*base; const angle=state.rotation+(i/DATA.qmap_nodes.length)*Math.PI*2-Math.PI/2; const px=cx+Math.cos(angle)*ring; const py=cy+Math.sin(angle)*ring*.72; const d=Math.hypot(px-x,py-y); if(d<bd){bd=d;best=i;}}); if(bd<42) selectNode(best); });
  function renderMetrics(){ const g=DATA.global_metrics; $('#globalMetrics').innerHTML=['core_verse_count','core_calc_words','core_calc_letters','core_gematria_mass','core_raw_bits','core_character_events','core_note_events','core_ornament_events','witness_group_count','unique_witness_reference_count','whole_word_instrument_families_found'].map(k=>`<div class="metric"><span>${k.replaceAll('_',' ')}</span><b>${g[k]}</b></div>`).join(''); }
  function renderNodes(){ const box=$('#nodeList'); box.innerHTML=''; DATA.qmap_nodes.forEach((n,i)=>{ const it=el('div','item'+(i===state.nodeIndex?' active':'')); it.innerHTML=`<div class="title">${i.toString().padStart(2,'0')} · ${n.name}</div><div class="meta">${n.scope} · pitch ${n.aggregate_pitch} · ${n.character_events} chars</div>`; it.onclick=()=>selectNode(i); box.appendChild(it);}); }
  function renderDetails(){ const n=getSelectedNode(); const vs=nodeVerses(n); const v=getSelectedVerse(); $('#nodeTitle').textContent=`${n.id} · ${n.name}`; $('#nodeMeta').innerHTML=`<span class="tag on">${n.scope}</span><span class="tag">${n.function}</span><span class="tag">pitch ${n.aggregate_pitch}</span><span class="tag">${n.raw_bits} bits</span>`; $('#sourceText').textContent=v?.source_text||''; $('#calcText').textContent=v?`${v.reference}\ncalc: ${v.calc_text}\ntotal: ${v.calc_total_value} · pitch ${v.verse_pitch} · words ${v.calc_word_count} · letters ${v.calc_letter_count} · raw bits ${v.raw_bit_count}`:'';
    const vsel=$('#verseSelect'); vsel.innerHTML=''; vs.forEach((vv,i)=>{const o=el('option');o.value=i;o.textContent=`${vv.reference} · ${vv.verse_pitch} · ${vv.calc_total_value}`;vsel.appendChild(o);}); vsel.value=state.verseIndex;
    const wl=$('#wordList'); wl.innerHTML=''; (v?.word_motifs||[]).forEach((w,i)=>{ const it=el('div','item'+(i===state.wordIndex?' active':'')); it.innerHTML=`<div class="title">${i+1}. ${w.raw_word}</div><div class="meta">${w.calc_token} · ${w.word_value} · ${w.word_pitch} · ${w.events?.length||0} events</div>`; it.onclick=()=>{state.wordIndex=i; state.selectedMode='word'; renderDetails();}; wl.appendChild(it); });
    const w=getSelectedWord(); const ev=$('#eventList'); ev.innerHTML=''; (w?.events||[]).slice(0,80).forEach((e,i)=>{ const it=el('div','item'); it.innerHTML=`<div class="title">${i+1}. ${e.raw_character||'rest'} · ${e.pitch||''} · ${e.instrument||''}</div><div class="meta">${e.unicode||''} ${e.character_type||''} · ${e.event_kind||''} · ${e.frequency_hz||''}Hz</div>`; // Audio playback is disabled in this public reading edition.
 ev.appendChild(it); }); }
  function renderInstrumentToggles(){ const keys=Object.keys(DATA.instrument_palette_v4||{}); const box=$('#instrumentToggles'); box.innerHTML=''; keys.forEach(k=>{const b=el('button',state.muted[k]?'':'active',k.replaceAll('_',' ')); b.onclick=()=>{state.muted[k]=!state.muted[k]; renderInstrumentToggles();}; box.appendChild(b);}); }
  function renderInstrumentResearch(){ const box=$('#instrumentResearch'); box.innerHTML=''; (DATA.whole_word_instrument_research_v4||[]).forEach(f=>{ const it=el('div','item'); it.innerHTML=`<div class="title">${f.family.replaceAll('_',' ')}</div><div class="meta">${f.match_count} matches · ${f.unique_reference_count} refs · ${f.sample_refs.slice(0,5).join(', ')}</div>`; it.onclick=()=>{ $('#searchInput').value=f.family.split('_')[0]; runSearch(); }; box.appendChild(it); }); }
  function renderRefs(){ const box=$('#refImages'); box.textContent='The recovered historical source refers to illustrative images that are not included in this public reading edition. No replacement historical evidence is implied.'; }
  function runSearch(){ const q=$('#searchInput').value.trim().toLowerCase(); const box=$('#searchResults'); box.innerHTML=''; if(!q){box.innerHTML='<div class="small">Search verse text, raw Hebrew, instrument family, node name.</div>'; return;} const hits=[]; DATA.core_verses.forEach((v,idx)=>{ if((v.reference+' '+v.source_text+' '+v.calc_text).toLowerCase().includes(q)) hits.push({type:'verse', idx, text:v.reference, meta:`${v.verse_pitch} · ${v.calc_total_value}`}); }); DATA.qmap_nodes.forEach((n,idx)=>{ if((n.name+' '+n.function+' '+n.scope).toLowerCase().includes(q)) hits.push({type:'node', idx, text:n.name, meta:n.scope}); }); (DATA.whole_word_instrument_research_v4||[]).forEach((f,idx)=>{ if(JSON.stringify(f).toLowerCase().includes(q)) hits.push({type:'instrument', idx, text:f.family, meta:`${f.unique_reference_count} refs`}); }); hits.slice(0,80).forEach(h=>{const it=el('div','item');it.innerHTML=`<div class="title">${h.type}: ${h.text}</div><div class="meta">${h.meta}</div>`;it.onclick=()=>{ if(h.type==='node') selectNode(h.idx); if(h.type==='verse'){ const ref=DATA.core_verses[h.idx].reference; const ni=DATA.qmap_nodes.findIndex(n=>n.references.includes(ref)); if(ni>=0){state.nodeIndex=ni; state.verseIndex=nodeVerses(DATA.qmap_nodes[ni]).findIndex(v=>v.reference===ref); renderAll();}}};box.appendChild(it);}); }
  function exportSelection(){ const payload={node:getSelectedNode(), verses:nodeVerses(getSelectedNode()), selected_word:getSelectedWord()}; const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='q6_selected_qmap_node.json'; a.click(); URL.revokeObjectURL(a.href); }
  function nextNode(){ selectNode(state.nodeIndex+1); }
  function prevNode(){ selectNode(state.nodeIndex-1); }
  function renderAll(){ renderNodes(); renderDetails(); $('#timeline').value=state.nodeIndex; $('#timelineLabel').textContent=`${state.nodeIndex+1}/${DATA.qmap_nodes.length}`; }
  $('#playBtn').onclick=playSelected; $('#playWeekBtn').onclick=()=>playEvents(DATA.core_verses.flatMap(v=>v.word_motifs.flatMap(w=>w.events||[])), 5000); $('#stopBtn').onclick=()=>{stopAudio(); state.playing=false; $('#playBtn').classList.remove('active')}; $('#prevBtn').onclick=prevNode; $('#nextBtn').onclick=nextNode; $('#exportBtn').onclick=exportSelection; $('#timeline').max=DATA.qmap_nodes.length-1; $('#timeline').oninput=e=>selectNode(Number(e.target.value)); $('#verseSelect').onchange=e=>{state.verseIndex=Number(e.target.value); state.wordIndex=0; renderDetails();}; $('#searchInput').addEventListener('input',runSearch);
  renderMetrics(); renderInstrumentToggles(); renderInstrumentResearch(); renderRefs(); renderAll(); runSearch(); draw();
})();
