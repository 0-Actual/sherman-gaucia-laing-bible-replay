const fs=require('fs');
const path=require('path');
const vm=require('vm');
const root=__dirname;
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const app=fs.readFileSync(path.join(root,'scripts/app.js'),'utf8');
const dataText=fs.readFileSync(path.join(root,'scripts/q6_data.js'),'utf8');
const assert=(ok,msg)=>{if(!ok)throw new Error(msg);};
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
const selectors=[...app.matchAll(/\$\('#([^']+)'\)/g)].map(m=>m[1]);
assert(selectors.every(id=>ids.includes(id)),'Missing DOM ID');
assert(!/https?:\/\//.test(html+app),'External URL in active HTML/app');
assert(!/AudioContext|createOscillator|fetch\(|XMLHttpRequest|WebSocket/.test(app),'Active media or network API');
for(const m of html.matchAll(/(?:src|href)="([^"]+)"/g)){assert(fs.existsSync(path.join(root,m[1])),'Missing asset '+m[1]);}
const ctx=new Proxy({createRadialGradient:()=>({addColorStop(){}})}, {get:(obj,key)=>key in obj?obj[key]:(()=>{})});
class Element {
 constructor(tag='div'){this.tag=tag;this.children=[];this._inner='';this.value='1';this.textContent='';this.listeners={};this.classList={add(){},remove(){}};}
 set innerHTML(v){this._inner=v;this.children=[];}
 get innerHTML(){return this._inner;}
 appendChild(c){this.children.push(c);return c;}
 addEventListener(name,fn){this.listeners[name]=fn;}
 getBoundingClientRect(){return {width:640,height:480,left:0,top:0};}
 getContext(){return ctx;}
 click(){if(this.onclick)this.onclick();}
}
const elements=Object.fromEntries(ids.map(id=>[id,new Element()]));
elements.searchInput.value='';
const context={console,Blob,devicePixelRatio:1,URL:{createObjectURL(){return 'blob:local-test'},revokeObjectURL(){}},document:{querySelector(sel){assert(sel.startsWith('#'),'Unexpected selector');assert(elements[sel.slice(1)],'Unresolved selector '+sel);return elements[sel.slice(1)];},createElement(tag){return new Element(tag);}},requestAnimationFrame(){},setTimeout(){}};
context.window=context;
context.addEventListener=()=>{};
context.AudioContext=()=>{throw new Error('Audio unexpectedly attempted')};
context.fetch=()=>{throw new Error('Network unexpectedly attempted')};
vm.createContext(context);
vm.runInContext(dataText,context,{timeout:3000});
vm.runInContext(app,context,{timeout:3000});
const data=context.Q6_DATA;
assert(data.core_verses.length===34,'Verse count');
assert(elements.nodeList.children.length===8,'Node count');
assert(elements.sourceText.textContent===data.core_verses[0].source_text,'Initial verse display');
elements.nextBtn.click();
assert(elements.sourceText.textContent!==data.core_verses[0].source_text,'Next navigation');
elements.prevBtn.click();
assert(elements.sourceText.textContent===data.core_verses[0].source_text,'Previous navigation');
elements.searchInput.value='Genesis 1:1';
elements.searchInput.listeners.input();
assert(elements.searchResults.children.length>0,'Search produces results');
elements.exportBtn.click();
elements.playBtn.click();
elements.playWeekBtn.click();
assert(elements.refImages.textContent.includes('not included'),'Omitted image notice');
const report={status:'PASS',checked_at_utc:new Date().toISOString(),checks:['JavaScript syntax checked separately','Required DOM IDs present','Referenced local scripts/style exist','No external HTML/app URLs','No active network/audio API','34 verse records parsed','8 nodes displayed','Initial verse rendered','Next and Previous navigation','Text search','Local JSON export callback','Disabled audio callbacks inert','Omitted image notice'],browser_visual_test_performed:false,method:'Node VM with bounded DOM/canvas stubs; not a browser rendering or playback test',new_hashes_or_signatures:false};
fs.writeFileSync(path.join(root,'VALIDATION.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
