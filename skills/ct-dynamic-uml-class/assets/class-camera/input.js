'use strict';
const pointers=new Map();let gestureMoved=false;
function midpoint(points){return {x:(points[0].x+points[1].x)/2,y:(points[0].y+points[1].y)/2};}
function distance(points){return Math.hypot(points[0].x-points[1].x,points[0].y-points[1].y);}
stage.addEventListener('pointerdown',event=>{
  if(event.target.closest('button,select,#minimap')||(event.pointerType==='mouse'&&event.button>1))return;
  if(!pointers.size){gestureMoved=false;CC.suppressClick=false;}
  pointers.set(event.pointerId,{x:event.clientX,y:event.clientY,startX:event.clientX,startY:event.clientY});
  // A click retains its original class/edge target. Capture after a drag starts.
  if(!event.target.closest('.node,.edge'))stage.setPointerCapture(event.pointerId);
  if(pointers.size===2){gestureMoved=true;CC.suppressClick=true;takeControl();}
});
stage.addEventListener('pointermove',event=>{
  if(!pointers.has(event.pointerId))return;
  const before=[...pointers.values()].slice(0,2),previous=pointers.get(event.pointerId);
  const next={...previous,x:event.clientX,y:event.clientY};
  pointers.set(event.pointerId,next);
  if(pointers.size>=2) {
    const after=[...pointers.values()].slice(0,2),a=midpoint(before),b=midpoint(after);
    takeControl();zoomAt(distance(after)/Math.max(distance(before),1),a.x,a.y);panBy(b.x-a.x,b.y-a.y);
    gestureMoved=true;
  }else{
    if(!gestureMoved&&Math.hypot(next.x-next.startX,next.y-next.startY)<4)return;
    if(!gestureMoved){takeControl();stage.setPointerCapture(event.pointerId);}
    gestureMoved=true;panBy(next.x-previous.x,next.y-previous.y);
  }
  CC.suppressClick=true;stage.classList.add('dragging');event.preventDefault();
});
function endPointer(event) {
  pointers.delete(event.pointerId);
  if(stage.hasPointerCapture(event.pointerId))stage.releasePointerCapture(event.pointerId);
  if(!pointers.size){stage.classList.remove('dragging');setTimeout(()=>CC.suppressClick=false,0);}
}
stage.addEventListener('pointerup',endPointer);stage.addEventListener('pointercancel',endPointer);
stage.addEventListener('lostpointercapture',event=>{
  pointers.delete(event.pointerId);if(!pointers.size)stage.classList.remove('dragging');
});
stage.addEventListener('wheel',event=>{
  event.preventDefault();takeControl();
  const unit=event.deltaMode===1?16:event.deltaMode===2?stage.clientHeight:1;
  const dx=event.deltaX*unit,dy=event.deltaY*unit;
  if(!event.ctrlKey&&!event.metaKey&&(byId('wheel-mode').value==='pan'||event.shiftKey)) {
    panBy(-dx,-dy);
  }else{
    zoomAt(Math.exp(-Math.max(-120,Math.min(120,dy))*(event.ctrlKey ? .008 : .003)),event.clientX,event.clientY);
  }
},{passive:false});
stage.addEventListener('keydown',event=>{
  if(event.target.closest('button,select,.node,.edge,#minimap')||event.ctrlKey||event.metaKey||event.altKey)return;
  if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)) {
    event.preventDefault();takeControl();
    panBy(event.key==='ArrowLeft'?60:event.key==='ArrowRight'?-60:0,event.key==='ArrowUp'?60:event.key==='ArrowDown'?-60:0);
  }else if(['+','=','-','_'].includes(event.key)){event.preventDefault();zoomCenter(['+','='].includes(event.key)?1.25:.8);}
  else if(event.key==='0'){event.preventDefault();showMap();}
  else if(event.key.toLowerCase()==='f'){event.preventDefault();pauseTour();focusLayout();}
  else if(event.key===' '){event.preventDefault();toggleTour();}
});
const mini=byId('minimap');let miniPointer=null;
function panFromMini(event) {
  const r=mini.getBoundingClientRect(),x=(event.clientX-r.left)*200/r.width,y=(event.clientY-r.top)*110/r.height;
  takeControl();CC.camera.x=(x-CC.mini.ox)/CC.mini.k;CC.camera.y=(y-CC.mini.oy)/CC.mini.k;paint();
}
mini.addEventListener('pointerdown',event=>{
  event.stopPropagation();event.preventDefault();miniPointer=event.pointerId;mini.setPointerCapture(event.pointerId);panFromMini(event);
});
mini.addEventListener('pointermove',event=>{if(event.pointerId===miniPointer)panFromMini(event);});
for(const type of ['pointerup','pointercancel','lostpointercapture'])mini.addEventListener(type,()=>miniPointer=null);
mini.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();showMap();}});
byId('zoom-in').onclick=()=>zoomCenter(1.25);byId('zoom-out').onclick=()=>zoomCenter(.8);
byId('follow').onclick=()=>{pauseTour();focusLayout();};byId('map').onclick=showMap;
byId('resume').onclick=()=>startTour();byId('play').onclick=()=>toggleTour();
byId('prev').onclick=()=>goStep(Math.max(0,CC.step-1),false);
byId('next').onclick=()=>goStep(Math.min(DemoModel.tour.length-1,CC.step+1),false);
byId('view').onchange=()=>{
  const id=byId('view').value,index=DemoModel.tour.findIndex(s=>s.view===id);
  if(index>=0)goStep(index,false);else{changeView(id);focusClass(CC.view.nodes[0]);}
};
byId('scenario').onchange=()=>goStep(DemoModel.tour.findIndex(s=>s.scenario===byId('scenario').value),false);
byId('inspect-class').onclick=()=>{const node=nodesById.get(CC.focus);showDetails(node.label,node.detail,[...node.fields,...node.methods]);};
byId('linked').onclick=()=>{
  const views=DemoModel.views.filter(v=>v.nodes.includes(CC.focus)),current=views.findIndex(v=>v.id===CC.view.id);
  const focus=CC.focus;changeView(views[(current+1)%views.length].id);focusClass(focus);
};
byId('info').onclick=()=>showDetails('Explore the model at your pace.',
  'Drag with a mouse or one/two fingers to pan. The mini-map moves the visible region. Manual movement pauses the tour; Resume tour restores following.',[
    'Mouse mode: a wheel zooms at the pointer. Shift + wheel pans.',
    'Trackpad mode: two-finger scrolling pans; pinch still zooms. Browsers do not reliably identify the wheel hardware, so choose the intended scroll behavior explicitly.',
    'Keyboard in the diagram: arrows pan; + / − zoom; 0 shows the view map; F restores focus; Space plays or pauses.',
    'More than 20 relationships for one class within a diagram: use linked views while retaining every class and relationship.',
    'All direct neighbors in the selected diagram remain visible. Smaller screens use smaller cards when needed.',
    'Reduced motion: camera and class positions change immediately. Playback remains opt-in.'
  ]);
byId('close').onclick=()=>byId('details').close();
document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseTour();});
window.addEventListener('blur',()=>{pointers.clear();stage.classList.remove('dragging');});
