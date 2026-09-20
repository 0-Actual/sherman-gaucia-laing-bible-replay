import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const root=process.env.QEL_WEB_TEST_ROOT || path.dirname(fileURLToPath(import.meta.url));
function openReader(){
  const elements=new Map(), windowEvents=new Map(), exports=[];
  function element(tag='div'){
    const events=new Map();
    const e={tag,children:[],value:'',textContent:'',style:{},classList:{remove(){},add(){}},
      addEventListener(name,fn){events.set(name,fn);},
      emit(name,event={}){events.get(name)?.(event);},
      appendChild(child){this.children.push(child);},click(){this.onclick?.();},
      getBoundingClientRect(){return {left:0,top:0,width:800,height:600};},
      getContext(){return new Proxy({}, {get(_t,k){if(k==='createRadialGradient') return ()=>({addColorStop(){}}); return ()=>{};},set(){return true;}});}};
    let html='';Object.defineProperty(e,'innerHTML',{get(){return html;},set(v){html=v;e.children=[];}});
    return e;
  }
  const html=readFileSync(path.join(root,'web/index.html'),'utf8');
  for(const match of html.matchAll(/id="([^"]+)"/g)) elements.set('#'+match[1],element());
  const window={addEventListener(name,fn){windowEvents.set(name,fn);}};
  const context=vm.createContext({window,document:{querySelector:s=>{assert.ok(elements.has(s),s);return elements.get(s);},createElement:element},
    devicePixelRatio:1,requestAnimationFrame(){},Blob,URL:{createObjectURL(blob){exports.push(blob);return 'blob:test';},revokeObjectURL(){}},
    fetch(){throw Error('Unexpected network request');},WebSocket(){throw Error('Unexpected socket');},AudioContext(){throw Error('Unexpected audio');}});
  vm.runInContext(readFileSync(path.join(root,'web/scripts/q6_data.js'),'utf8'),context);
  const original=JSON.stringify(window.Q6_DATA);
  vm.runInContext(readFileSync(path.join(root,'web/scripts/app.js'),'utf8'),context);
  return {elements,exports,data:window.Q6_DATA,original,windowEvent(name,event){windowEvents.get(name)?.(event);},
    title(){return elements.get('#nodeTitle').textContent;},
    selectVerse(reference){elements.get('#searchInput').value=reference;elements.get('#searchInput').emit('input');
      const hit=elements.get('#searchResults').children.find(x=>x.innerHTML.includes('verse: '+reference+'</div>'));
      assert.ok(hit,'Search result for '+reference);hit.onclick();},
    position(index,rotation=0){const node=window.Q6_DATA.qmap_nodes[index];const verse=window.Q6_DATA.core_verses.find(v=>v.reference===node.references[0]);
      const ring=(.28+(verse?.day||0)*.08)*210,angle=rotation+index/window.Q6_DATA.qmap_nodes.length*Math.PI*2-Math.PI/2;
      return {clientX:400+Math.cos(angle)*ring,clientY:300+Math.sin(angle)*ring*.72};}};
}

test('global alphabetic count excludes all three historical apostrophes',()=>{
  const r=openReader();assert.match(r.elements.get('#globalMetrics').innerHTML,/>core calc letters<\/span><b>3210<\/b>/);
  assert.equal(r.data.global_metrics.core_calc_letters,3213);
});
test('instrument metrics distinguish four recorded matches from eleven configured families',()=>{
  const r=openReader(),metrics=r.elements.get('#globalMetrics').innerHTML;
  assert.match(metrics,/>instrument families with recorded matches<\/span><b>4<\/b>/);
  assert.match(metrics,/>instrument families configured<\/span><b>11<\/b>/);
  assert.doesNotMatch(metrics,/whole word instrument families found/);
  assert.equal(r.data.global_metrics.whole_word_instrument_families_found,11);
  assert.equal(JSON.stringify(r.data),r.original);
});
test('all 34 displayed verse counts match an independent ASCII-letter oracle',()=>{
  const r=openReader();assert.equal(r.data.core_verses.length,34);
  for(const verse of r.data.core_verses){
    assert.ok([...verse.calc_text].filter(c=>/\p{L}/u.test(c)).every(c=>/[A-Za-z]/.test(c)));
    const expected=[...verse.calc_text].filter(c=>(c>='A'&&c<='Z')||(c>='a'&&c<='z')).length;
    r.selectVerse(verse.reference);assert.match(r.elements.get('#calcText').textContent,new RegExp('letters '+expected+'(?: | ·)'));
    assert.equal(r.elements.get('#sourceText').textContent,verse.source_text);
  }
});
test('all three corrected counts expose historical values instead of silently rewriting them',()=>{
  const r=openReader();for(const [ref,value,old] of [['Genesis 1:2',108,109],['Genesis 1:26',187,188],['Genesis 1:27',75,76]]){
    r.selectVerse(ref);assert.ok(r.elements.get('#calcText').textContent.includes(`letters ${value} (historical count ${old}; punctuation excluded)`));}
  assert.equal(JSON.stringify(r.data),r.original);
});
test('node export preserves original records and includes corrected counts',async()=>{
  const r=openReader();r.selectVerse('Genesis 1:2');r.elements.get('#exportBtn').onclick();
  const out=JSON.parse(await r.exports[0].text());const v=out.derived_letter_counts.verses.find(v=>v.reference==='Genesis 1:2');
  assert.equal(v.alphabetic_letters,108);assert.equal(v.historical_recorded_letters,109);
  assert.equal(out.verses.find(v=>v.reference==='Genesis 1:2').calc_letter_count,109);
  assert.equal(out.derived_letter_counts.selection_letters,out.derived_letter_counts.verses.reduce((n,v)=>n+v.alphabetic_letters,0));
  assert.match(out.historical_data_notice,/historical/);assert.equal(JSON.stringify(r.data),r.original);
});
test('drag ending on a different node does not select it after pointerup',()=>{
  const r=openReader(),c=r.elements.get('#qmapCanvas'),initial=r.title();
  c.emit('pointerdown',{pointerId:1,button:0,clientX:100,clientY:100});
  r.windowEvent('pointermove',{pointerId:1,clientX:200,clientY:100});
  r.windowEvent('pointerup',{pointerId:1,clientX:200,clientY:100});c.emit('click',r.position(1,.7));
  assert.equal(r.title(),initial);
});
test('a fresh deliberate click after dragging still selects a node',()=>{
  const r=openReader(),c=r.elements.get('#qmapCanvas');c.emit('pointerdown',{pointerId:1,button:0,clientX:100,clientY:100});
  r.windowEvent('pointermove',{pointerId:1,clientX:200,clientY:100});r.windowEvent('pointerup',{pointerId:1,clientX:200,clientY:100});
  c.emit('click',r.position(1,.7));const point=r.position(2,.7);c.emit('pointerdown',{pointerId:2,button:0,...point});
  r.windowEvent('pointerup',{pointerId:2,...point});c.emit('click',point);assert.ok(r.title().startsWith(r.data.qmap_nodes[2].id));
});
test('drag returning to origin remains a drag',()=>{
  const r=openReader(),c=r.elements.get('#qmapCanvas'),initial=r.title();c.emit('pointerdown',{pointerId:1,button:0,clientX:100,clientY:100});
  r.windowEvent('pointermove',{pointerId:1,clientX:200,clientY:100});r.windowEvent('pointermove',{pointerId:1,clientX:100,clientY:100});
  r.windowEvent('pointerup',{pointerId:1,clientX:100,clientY:100});c.emit('click',r.position(1));assert.equal(r.title(),initial);
});
test('small pointer jitter permits an intentional click',()=>{
  const r=openReader(),c=r.elements.get('#qmapCanvas'),point=r.position(2);c.emit('pointerdown',{pointerId:1,button:0,...point});
  r.windowEvent('pointermove',{pointerId:1,clientX:point.clientX+1,clientY:point.clientY});
  r.windowEvent('pointerup',{pointerId:1,clientX:point.clientX+1,clientY:point.clientY});c.emit('click',r.position(2,.007));
  assert.ok(r.title().startsWith(r.data.qmap_nodes[2].id));
});
test('pointer cancellation cannot cause selection',()=>{
  const r=openReader(),c=r.elements.get('#qmapCanvas'),initial=r.title();c.emit('pointerdown',{pointerId:1,button:0,clientX:100,clientY:100});
  r.windowEvent('pointercancel',{pointerId:1});c.emit('click',r.position(2));assert.equal(r.title(),initial);
});
test('existing navigation, search and disabled audio remain functional',()=>{
  const r=openReader();r.elements.get('#nextBtn').onclick();assert.ok(r.title().startsWith(r.data.qmap_nodes[1].id));
  r.elements.get('#prevBtn').onclick();assert.ok(r.title().startsWith(r.data.qmap_nodes[0].id));
  for(const id of ['#playBtn','#playWeekBtn','#stopBtn']) assert.doesNotThrow(()=>r.elements.get(id).onclick());
  r.selectVerse('Genesis 2:3');assert.match(r.elements.get('#calcText').textContent,/Genesis 2:3/);
});
