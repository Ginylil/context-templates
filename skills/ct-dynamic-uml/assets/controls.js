function stop(){clearTimeout(timer);timer=null;text('play','Play ▷');$('play').setAttribute('aria-label','Play walkthrough');}
function syncParticipants(){
  const strip=$('participant-headings');if(strip.hidden)return;
  const head=strip.querySelector('svg');
  head.style.width=svg.getBoundingClientRect().width+'px';
  head.style.transform=`translateX(${-$('canvas-scroll').scrollLeft}px)`;
  strip.scrollLeft=0;
}
// Zoom scales the SVG's pixel width; the document keeps owning vertical scrolling.
const ZOOM_MIN=.5,ZOOM_MAX=3,FOCUS_MAX=2;let zoom=1,zoomMode='focus';
const defaultZoomMode=()=>model.type==='sequence'?'manual':'focus';
function fitWidth(){
  const frame=$('canvas-scroll'),zoomed=frame.classList.contains('zoomed'),width=svg.style.width;
  frame.classList.remove('zoomed');svg.style.width='';const fit=svg.getBoundingClientRect().width;
  if(zoomed){frame.classList.add('zoomed');svg.style.width=width;}
  return fit;
}
function setZoom(value){
  zoom=Math.max(ZOOM_MIN,Math.min(ZOOM_MAX,value));if(Math.abs(zoom-1)<.01)zoom=1;
  const frame=$('canvas-scroll');
  if(zoom===1){frame.classList.remove('zoomed');svg.style.width='';}
  else{const fit=fitWidth();frame.classList.add('zoomed');svg.style.width=fit*zoom+'px';}
  text('zoom-level',`${Math.round(zoom*100)}%`);$('zoom-out').disabled=zoom<=ZOOM_MIN;$('zoom-in').disabled=zoom>=ZOOM_MAX;
  syncParticipants();
}
function syncZoomMode(){
  $('zoom-focus').hidden=model.type==='sequence';$('zoom-focus').setAttribute('aria-pressed',String(zoomMode==='focus'));
}
// The active step's elements plus every directly connected node and relationship.
function focusElements(step){
  const active=new Set(step.nodes),links=model.edges.filter(e=>step.edges.includes(e.id)||active.has(e.from)||active.has(e.to));
  const nodes=new Set([...step.nodes,...links.flatMap(e=>[e.from,e.to])]);
  return [...[...nodes].map(id=>nodeEls.get(id)),...links.map(e=>edgeEls.get(e.id))].filter(Boolean);
}
function focusZoom(){
  const boxes=focusElements(steps()[index]).map(e=>e.getBBox());if(!boxes.length)return 1;
  const pad=24,w=Math.max(...boxes.map(b=>b.x+b.width))-Math.min(...boxes.map(b=>b.x))+pad*2;
  const h=Math.max(...boxes.map(b=>b.y+b.height))-Math.min(...boxes.map(b=>b.y))+pad*2;
  const unit=fitWidth()/model.width,toolbar=document.querySelector('.toolbar').getBoundingClientRect().height;
  const fitted=Math.min(($('canvas-scroll').clientWidth-32)/(w*unit),(innerHeight-toolbar-32)/(h*unit));
  return Math.max(1,Math.min(FOCUS_MAX,Math.floor(fitted*20)/20));
}
function centerFocus(){
  const frame=$('canvas-scroll'),f=frame.getBoundingClientRect(),b=focusElements(steps()[index]).map(e=>e.getBoundingClientRect());
  if(b.length)frame.scrollLeft+=(Math.min(...b.map(r=>r.left))+Math.max(...b.map(r=>r.right))-f.left-f.right)/2;
}
function applyZoom(){
  if(zoomMode==='focus')setZoom(overview||model.type==='sequence'?1:focusZoom());else setZoom(zoom);
}
function zoomBy(factor,point){
  const frame=$('canvas-scroll'),before=svg.getBoundingClientRect(),bounds=frame.getBoundingClientRect();
  const top=Math.max(before.top,document.querySelector('.toolbar').getBoundingClientRect().bottom),bottom=Math.min(before.bottom,innerHeight);
  const x=point?.x??(bounds.left+bounds.right)/2,y=point?.y??(top+bottom)/2;
  const fx=(x-before.left)/before.width,fy=(y-before.top)/before.height;
  zoomMode='manual';syncZoomMode();setZoom(factor===0?1:zoom*factor);
  const after=svg.getBoundingClientRect();
  frame.scrollLeft+=after.left+fx*after.width-x;
  window.scrollBy({top:after.top+fy*after.height-y,behavior:'auto'});
  syncParticipants();
}
function toggleFocus(){
  zoomMode=zoomMode==='focus'?'manual':'focus';syncZoomMode();
  if(zoomMode==='focus')followActive();
}
function sizeCanvas(){
  layoutSequence();
  const toolbarHeight=document.querySelector('.toolbar').getBoundingClientRect().height;
  document.documentElement.style.setProperty('--toolbar-height',toolbarHeight+'px');
  syncParticipants();
  $('details-sidebar').style.maxHeight=Math.max(120,innerHeight-toolbarHeight-16)+'px';
}
function followActive(){
  if($('details-modal').open)return;
  sizeCanvas();applyZoom();
  const frame=$('canvas-scroll'),toolbar=document.querySelector('.toolbar'),strip=$('participant-headings');
  const step=steps()[index],sequence=model.type==='sequence';
  const elements=(sequence&&step.edges.length?step.edges.map(id=>edgeEls.get(id)):step.nodes.map(id=>nodeEls.get(id)));
  const union=rects=>({left:Math.min(...rects.map(b=>b.left)),right:Math.max(...rects.map(b=>b.right)),top:Math.min(...rects.map(b=>b.top)),bottom:Math.max(...rects.map(b=>b.bottom))});
  let box=union(elements.map(e=>e.getBoundingClientRect()));
  const bounds=frame.getBoundingClientRect(),headerHeight=strip.hidden?0:strip.getBoundingClientRect().height;
  const viewportTop=toolbar.getBoundingClientRect().height+headerHeight+16,viewportBottom=innerHeight-16;
  // Focus framing keeps the active step's neighbors in view whenever they fit.
  const focused=!sequence&&!overview&&zoomMode==='focus';
  if(focused){
    const context=union(focusElements(step).map(e=>e.getBoundingClientRect()));
    if(context.right-context.left<=bounds.width-32&&context.bottom-context.top<=viewportBottom-viewportTop)box=context;
  }
  // Show the surrounding exchange too when its visible arrows fit in the window.
  if(sequence&&!overview){
    const context=sequenceNeighbors(step).filter(e=>e&&edgeEls.get(e.id).style.display!=='none')
      .map(e=>edgeEls.get(e.id).getBoundingClientRect());
    const top=Math.min(box.top,...context.map(b=>b.top)),bottom=Math.max(box.bottom,...context.map(b=>b.bottom));
    if(bottom-top<=viewportBottom-viewportTop){box.top=top;box.bottom=bottom;}
  }
  // A distant structural transition may span several screens; follow its destination then.
  if(!sequence&&(box.right-box.left>bounds.width-32||box.bottom-box.top>viewportBottom-viewportTop)){
    const destination=step.edges.length?edgeMap.get(step.edges.at(-1)).to:step.nodes.at(-1);
    box=nodeEls.get(destination).getBoundingClientRect();
  }
  if(box.top<viewportTop)window.scrollBy({top:box.top-viewportTop,behavior:'auto'});
  else if(box.bottom>viewportBottom)window.scrollBy({top:box.bottom-viewportBottom,behavior:'auto'});
  const left=bounds.left+16,right=bounds.right-16;
  if(focused||box.left<left||box.right>right)frame.scrollLeft+=(box.left+box.right-left-right)/2;
  syncParticipants();
}
function go(i){index=Math.max(0,Math.min(i,steps().length-1));if(index===0)$('canvas-scroll').scrollTop=0;update();followActive();}
function scheduleNext(delay){
  deadline=performance.now()+delay;
  timer=setTimeout(()=>{timer=null;go(index+1);if(index===steps().length-1)stop();else scheduleNext(Number($('pace').value)*1000);},delay);
}
function startPlayback(delay=Number($('pace').value)*1000){
  if($('details-modal').open||document.hidden)return;
  text('play','Pause Ⅱ');$('play').setAttribute('aria-label','Pause walkthrough');followActive();scheduleNext(delay);
}
function play(){if($('details-modal').open)return;if(timer!==null){stop();return;}if(index===steps().length-1)go(0);startPlayback();}
function openDetails(){
  closePicker(false);
  if($('details-modal').open)return;
  resumeAfterDetails=timer!==null;resumeDelay=resumeAfterDetails?Math.max(1,deadline-performance.now()):0;
  detailsTrigger=document.activeElement;stop();
  text('modal-playback-note',resumeAfterDetails?'Playback paused · resumes when you close.':'Playback is paused.');
  $('modal-content').append($('details-panel'));document.body.classList.add('modal-open');
  $('info').setAttribute('aria-expanded','true');$('details-modal').showModal();
}
function restoreDetails(){
  document.body.classList.remove('modal-open');$('info').setAttribute('aria-expanded','false');
  if(sidebar)$('details-sidebar').append($('details-panel'));
  detailsTrigger?.focus({preventScroll:true});
  const resume=resumeAfterDetails;resumeAfterDetails=false;
  if(resume&&!document.hidden)startPlayback(resumeDelay);
}
function toggleSidebar(){
  sidebar=!sidebar;$('sidebar-toggle').setAttribute('aria-pressed',String(sidebar));
  $('workspace').classList.toggle('with-sidebar',sidebar);$('details-sidebar').hidden=!sidebar;
  (sidebar?$('details-sidebar'):$('modal-content')).append($('details-panel'));
  followActive();
}
function update(){layoutSequence();const s=steps()[index];text('counter',`${String(index+1).padStart(2,'0')} / ${String(steps().length).padStart(2,'0')}`);text('step-label',`Step ${String(index+1).padStart(2,'0')} · ${model.scenarios[scenario].label}`);text('step-title',s.title);text('step-body',s.body);text('current-step',s.title);text('announcement',`Step ${index+1} of ${steps().length}: ${s.title}. ${s.body}`);$('prev').disabled=index===0;$('next').disabled=index===steps().length-1;$('progress').style.width=`${(index+1)/steps().length*100}%`;
for(const [id,g]of nodeEls){g.classList.toggle('active',s.nodes.includes(id));g.classList.toggle('selected',selected?.kind==='Node'&&selected.id===id);g.classList.toggle('dim',!overview&&!s.nodes.includes(id)&&!(selected?.kind==='Node'&&selected.id===id));}
for(const [id,g]of edgeEls){const isActive=s.edges.includes(id),isSelected=selected?.kind==='Relationship'&&selected.id===id;g.classList.toggle('active',isActive);g.classList.toggle('selected',isSelected);g.classList.toggle('dim',!overview&&!isActive&&!isSelected);const mk=marker(edgeMap.get(id),isSelected?'selected':isActive?'active':'normal');if(mk)g.querySelector('.visible').setAttribute(...mk);}
if($('step-track').dataset.scenario!==String(scenario)){$('step-track').dataset.scenario=String(scenario);$('step-track').replaceChildren();steps().forEach((step,i)=>{const b=document.createElement('button');b.textContent=i+1;b.setAttribute('aria-label',`Step ${i+1}: ${step.title}`);b.setAttribute('aria-current',String(i===index));b.addEventListener('click',()=>{stop();go(i);});$('step-track').append(b);});}$('step-track').querySelectorAll('button').forEach((b,i)=>b.setAttribute('aria-current',String(i===index)));}
function populateView(){
  for(const id of ['assumptions','sources','legend'])$(id).replaceChildren();
text('kicker',model.kicker||'Explore a system');text('title',model.title);text('lede',model.lede);text('type',model.type+' diagram');text('canvas-label',model.canvasLabel||'Walkthrough / one idea at a time');text('evidence',model.evidence);
buildPicker();
for(const a of model.assumptions){const li=document.createElement('li');li.textContent=a;$('assumptions').append(li);}
for(const source of model.sources){const li=document.createElement('li'),a=document.createElement('a');a.textContent=source.label;a.href=source.href;a.rel='noopener noreferrer';li.append(a);$('sources').append(li);}
if(!model.sources.length){const li=document.createElement('li');li.textContent='Illustrative model. No external system claims.';$('sources').append(li);}
for(const item of model.legend){const span=document.createElement('span'),i=document.createElement('i');if(item.dashed)i.className='dashed';span.append(i,document.createTextNode(item.label));$('legend').append(span);}
}
function setScenario(value){stop();scenario=value;syncPicker();go(0);}
function syncPicker(){
  $('scenario').value=String(scenario);text('scenario-value',model.scenarios[scenario].label);
  [...$('scenario-menu').children].forEach((o,i)=>o.setAttribute('aria-selected',String(i===scenario)));
}
function buildPicker(){
  closePicker(false);$('scenario-menu').replaceChildren();
  model.scenarios.forEach((s,i)=>{const o=document.createElement('div');o.setAttribute('role','option');o.tabIndex=-1;o.dataset.index=i;o.textContent=s.label;o.onclick=()=>{setScenario(i);closePicker(true);};$('scenario-menu').append(o);});syncPicker();
}
function focusOption(i){const options=[...$('scenario-menu').children];pickerFocus=(i+options.length)%options.length;options[pickerFocus].focus({preventScroll:true});options[pickerFocus].scrollIntoView({block:'nearest'});}
function openPicker(){
  if($('details-modal').open)return;
  $('scenario-menu').hidden=false;$('scenario').setAttribute('aria-expanded','true');
  const below=$('scenario').getBoundingClientRect().bottom;
  $('scenario-menu').style.maxHeight=Math.max(48,Math.min(280,innerHeight-below-16))+'px';
  focusOption(scenario);
}
function closePicker(focus){$('scenario-menu').hidden=true;$('scenario').setAttribute('aria-expanded','false');if(focus)$('scenario').focus({preventScroll:true});}
function findOption(key){
  const now=performance.now();typeahead=now-typeaheadAt>700?key:typeahead+key;typeaheadAt=now;
  const i=model.scenarios.findIndex(s=>s.label.toLocaleLowerCase().startsWith(typeahead.toLocaleLowerCase()));if(i>=0)focusOption(i);
}
$('scenario').onclick=()=> $('scenario-menu').hidden?openPicker():closePicker(true);
$('scenario').onkeydown=e=>{if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){e.preventDefault();openPicker();if(e.key==='Home')focusOption(0);if(e.key==='End')focusOption(model.scenarios.length-1);}else if(e.key.length===1&&e.key!==' '&&!e.ctrlKey&&!e.metaKey&&!e.altKey){e.preventDefault();openPicker();findOption(e.key);}};
$('scenario-menu').onkeydown=e=>{
  if(['ArrowDown','ArrowUp','Home','End','Enter',' ','Escape','Tab'].includes(e.key)){
    if(e.key!=='Tab')e.preventDefault();e.stopPropagation();
    if(e.key==='ArrowDown')focusOption(pickerFocus+1);if(e.key==='ArrowUp')focusOption(pickerFocus-1);
    if(e.key==='Home')focusOption(0);if(e.key==='End')focusOption(model.scenarios.length-1);
    if(e.key==='Enter'||e.key===' '){setScenario(pickerFocus);closePicker(true);}
    if(e.key==='Escape'||e.key==='Tab')closePicker(true);
  }else if(e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey){e.preventDefault();findOption(e.key);}
};
document.addEventListener('pointerdown',e=>{if(!$('scenario-picker').contains(e.target))closePicker(false);});
$('scenario-picker').addEventListener('focusout',e=>{if(!$('scenario-picker').contains(e.relatedTarget))closePicker(false);});
function loadView(next){
  stop();model=next;document.title=model.title;index=0;scenario=0;selected=null;overview=false;zoom=1;zoomMode=defaultZoomMode();
  $('overview').setAttribute('aria-pressed','false');$('open-subflow').hidden=true;
  text('inspect-title','Explore the diagram');text('inspect-body','Select any node or relationship to see its purpose.');
  nodeMap.clear();edgeMap.clear();nodeEls.clear();edgeEls.clear();
  model.nodes.forEach(n=>nodeMap.set(n.id,n));model.edges.forEach(e=>edgeMap.set(e.id,e));
  svg.replaceChildren();$('participant-headings').replaceChildren();$('participant-headings').hidden=true;
  $('step-track').removeAttribute('data-scenario');$('canvas-scroll').scrollTop=0;$('canvas-scroll').scrollLeft=0;
  $('flow-navigation').hidden=!flowStack.length;
  text('flow-path',[...flowStack.map(f=>f.model.title),model.title].join(' / '));
  populateView();draw();update();sizeCanvas();syncZoomMode();setZoom(1);
}
$('open-subflow').onclick=()=>{
  const node=selected?.kind==='Node'?nodeMap.get(selected.id):null;if(!node?.subflow)return;
  const child=model.subflows.find(f=>f.id===node.subflow);
  flowStack.push({model,index,scenario,node:node.id,overview,zoom,zoomMode,pageScroll:scrollY,scrollTop:$('canvas-scroll').scrollTop,scrollLeft:$('canvas-scroll').scrollLeft});
  resumeAfterDetails=false;if($('details-modal').open)$('details-modal').close();
  loadView(child);$('flow-back').focus({preventScroll:true});followActive();
};
$('flow-back').onclick=()=>{
  const saved=flowStack.pop();if(!saved)return;loadView(saved.model);
  scenario=saved.scenario;overview=saved.overview;zoom=saved.zoom;zoomMode=saved.zoomMode;syncZoomMode();
  $('overview').setAttribute('aria-pressed',String(overview));syncPicker();go(saved.index);
  $('canvas-scroll').scrollTop=saved.scrollTop;$('canvas-scroll').scrollLeft=saved.scrollLeft;syncParticipants();window.scrollTo({top:saved.pageScroll,behavior:'auto'});
  nodeEls.get(saved.node)?.focus({preventScroll:true});
};
$('prev').onclick=()=>{stop();go(index-1);};$('next').onclick=()=>{stop();go(index+1);};$('reset').onclick=()=>{stop();selected=null;scenario=0;syncPicker();overview=false;zoom=1;zoomMode=defaultZoomMode();syncZoomMode();$('open-subflow').hidden=true;$('overview').setAttribute('aria-pressed','false');text('inspect-title','Explore the diagram');text('inspect-body','Select any node or relationship to see its purpose.');go(0);};$('play').onclick=play;$('info').onclick=openDetails;$('close-details').onclick=()=> $('details-modal').close();$('details-modal').addEventListener('close',restoreDetails);$('sidebar-toggle').onclick=toggleSidebar;$('pace').oninput=()=>{text('pace-value',$('pace').value+'s');if(timer){stop();play();}};$('overview').onclick=()=>{overview=!overview;$('overview').setAttribute('aria-pressed',String(overview));update();followActive();};
document.addEventListener('keydown',e=>{if($('details-modal').open||e.defaultPrevented||/INPUT|SELECT|TEXTAREA|BUTTON|A/.test(e.target.tagName)||e.target.closest('[role=button]'))return;if(e.key==='ArrowRight'){e.preventDefault();stop();go(index+1);}else if(e.key==='ArrowLeft'){e.preventDefault();stop();go(index-1);}else if(e.key===' '){e.preventDefault();play();}else if(!e.ctrlKey&&!e.metaKey&&!e.altKey&&['+','=','-','_','0'].includes(e.key)){e.preventDefault();zoomBy(e.key==='0'?0:['+','='].includes(e.key)?1.25:.8);}});
$('zoom-in').onclick=()=>zoomBy(1.25);$('zoom-out').onclick=()=>zoomBy(.8);$('zoom-fit').onclick=()=>zoomBy(0);$('zoom-focus').onclick=toggleFocus;
// Ctrl/Cmd + wheel (and trackpad pinch) zooms around the pointer.
$('canvas-scroll').addEventListener('wheel',e=>{if(!e.ctrlKey&&!e.metaKey)return;e.preventDefault();zoomBy(Math.exp(-Math.max(-60,Math.min(60,e.deltaY))/200),{x:e.clientX,y:e.clientY});},{passive:false});
$('canvas-scroll').addEventListener('scroll',syncParticipants,{passive:true});
$('participant-headings').addEventListener('focusin',e=>{
  const node=e.target.closest('[data-node]');if(!node)return;
  const box=node.getBoundingClientRect(),bounds=$('canvas-scroll').getBoundingClientRect();
  if(box.left<bounds.left+16||box.right>bounds.right-16)$('canvas-scroll').scrollLeft+=(box.left+box.right-bounds.left-bounds.right)/2;
  syncParticipants();
});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});window.addEventListener('resize',()=>{if(!$('details-modal').open)followActive();});populateView();draw();update();sizeCanvas();
zoomMode=defaultZoomMode();syncZoomMode();applyZoom();if(zoomMode==='focus')centerFocus();
