'use strict';
function pauseTour() {
  clearTimeout(CC.timer);CC.timer=0;CC.playing=false;
  byId('play').textContent=CC.mode==='focus'?'Play tour ▷':'Resume tour ▷';
}
function changeView(id) {
  pauseTour();stopMotion();CC.view=DemoModel.views.find(v=>v.id===id);
  CC.focus=CC.view.nodes.includes(CC.focus)?CC.focus:CC.view.nodes[0];
  CC.positions=Object.fromEntries(localNodes().map(n=>[n.id,{...n.home}]));drawView();
}
function goStep(index,playing=false) {
  clearTimeout(CC.timer);CC.step=index;CC.playing=playing;
  const step=DemoModel.tour[index];
  if(CC.view.id!==step.view){changeView(step.view);CC.playing=playing;}
  CC.focus=step.focus;focusLayout();
  byId('announcement').textContent=`Step ${index+1}. ${step.title} ${CC.neighbors.length} direct neighbors in ${CC.view.label}.`;
  if(playing)CC.timer=setTimeout(()=>{
    if(index<DemoModel.tour.length-1)goStep(index+1,true);
    else{pauseTour();paint();byId('announcement').textContent='Tour complete.';}
  },4500);
}
function startTour() {if(!document.hidden)goStep(CC.step===DemoModel.tour.length-1?0:CC.step,true);}
function toggleTour(){if(CC.playing){pauseTour();paint();}else startTour();}
function updateStory() {
  const step=DemoModel.tour[CC.step],node=nodesById.get(CC.focus);
  const onStep=step.view===CC.view.id&&step.focus===CC.focus;
  byId('step-count').textContent=`${String(CC.step+1).padStart(2,'0')} / ${DemoModel.tour.length} · ${CC.view.label}`;
  byId('story-title').textContent=onStep?step.title:`Explore ${node.label}.`;
  byId('story-body').textContent=onStep?step.body:node.detail;
  const total=DemoModel.edges.filter(e=>e.from===node.id||e.to===node.id).length;
  const local=localEdges().filter(e=>e.from===node.id||e.to===node.id).length;
  const views=DemoModel.views.filter(v=>v.nodes.includes(node.id));
  byId('relations').textContent=total>20?`${local} here · ${total} relationships across ${views.length} diagrams`:
    `${local} direct relationships · ${CC.view.nodes.length} classes in this view`;
  byId('linked').hidden=views.length<2;
  byId('prev').disabled=CC.step===0;byId('next').disabled=CC.step===DemoModel.tour.length-1;
  [...byId('steps').children].forEach((button,i)=>button.setAttribute('aria-current',i===CC.step?'step':'false'));
}
function showDetails(title,body,items) {
  pauseTour();paint();byId('details-title').textContent=title;byId('details-body').textContent=body;
  byId('details-list').replaceChildren();
  for(const item of items){const li=document.createElement('li');li.textContent=item;byId('details-list').append(li);}
  byId('details').showModal();
}
for(const view of DemoModel.views){const option=document.createElement('option');option.value=view.id;option.textContent=view.label;byId('view').append(option);}
DemoModel.tour.forEach((step,i)=>{const button=document.createElement('button');button.textContent=String(i+1);
  button.setAttribute('aria-label',`Step ${i+1}: ${step.title}`);button.onclick=()=>goStep(i,false);byId('steps').append(button);});
drawView();focusLayout(false);
