'use strict';
function stopMotion() {
  cancelAnimationFrame(CC.animation);CC.animation=0;CC.animating=false;
}
function moveTo(positions,camera,animate=true) {
  stopMotion();
  CC.targetPositions=structuredClone(positions);
  const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const duration=animate&&!reduce?950:0,origin=structuredClone(CC.positions),before={...CC.camera},start=performance.now();
  CC.animating=duration>0;
  function frame(now) {
    const t=duration?Math.min(1,(now-start)/duration):1,ease=t*t*(3-2*t);
    for(const [id,p]of Object.entries(positions)) {
      const from=origin[id]||p;
      CC.positions[id]={x:from.x+(p.x-from.x)*ease,y:from.y+(p.y-from.y)*ease};
    }
    for(const key of ['x','y','k'])CC.camera[key]=before[key]+(camera[key]-before[key])*ease;
    if(t===1){CC.animating=false;CC.animation=0;settleRoutes();}
    paint();
    if(t<1)CC.animation=requestAnimationFrame(frame);
  }
  frame(start);
}
function focusLayout(animate=true) {
  const layout=DemoLayout.focusLayout(localNodes(),localEdges(),CC.focus,CC.metrics);
  CC.neighbors=layout.neighbors;CC.dense=layout.dense;CC.mode='focus';
  const camera=DemoLayout.cameraFor(layout.positions,[CC.focus,...CC.neighbors],CC.focus,CC.metrics,stage.clientWidth,stage.clientHeight);
  moveTo(layout.positions,camera,animate);updateStory();
}
function takeControl() {
  pauseTour();
  if(CC.mode==='explore')return;
  const moving=CC.animating,origin=structuredClone(CC.positions),target=CC.targetPositions;
  stopMotion();CC.mode='explore';
  // Stop camera travel immediately; let a partly completed rearrangement settle
  // without overriding the reader's camera or leaving overlapping class cards.
  if(moving&&target) {
    const start=performance.now(),duration=matchMedia('(prefers-reduced-motion: reduce)').matches?0:240;
    CC.animating=true;
    function finish(now) {
      const t=duration?Math.min(1,(now-start)/duration):1;
      for(const [id,p]of Object.entries(target))CC.positions[id]={
        x:origin[id].x+(p.x-origin[id].x)*t,y:origin[id].y+(p.y-origin[id].y)*t};
      if(t===1){CC.animating=false;CC.animation=0;settleRoutes();}
      paint();if(t<1)CC.animation=requestAnimationFrame(finish);
    }
    CC.animation=requestAnimationFrame(finish);
  }else{settleRoutes();paint();}
}
function panBy(dx,dy) {
  CC.camera.x-=dx/CC.camera.k;CC.camera.y-=dy/CC.camera.k;paint();
}
function zoomAt(factor,clientX,clientY) {
  const r=stage.getBoundingClientRect(),x=clientX-r.left-r.width/2,y=clientY-r.top-r.height/2;
  const before=CC.camera.k,after=Math.max(.12,Math.min(3.5,before*factor));
  CC.camera.x+=x/before-x/after;CC.camera.y+=y/before-y/after;CC.camera.k=after;paint();
}
function zoomCenter(factor) {
  takeControl();const r=stage.getBoundingClientRect();zoomAt(factor,r.left+r.width/2,r.top+r.height/2);
}
function showMap(animate=true) {
  pauseTour();CC.mode='map';CC.neighbors=[];CC.dense=false;
  const positions=Object.fromEntries(localNodes().map(n=>[n.id,{...n.home}]));
  const camera=DemoLayout.cameraFor(positions,CC.view.nodes,CC.focus,CC.metrics,stage.clientWidth,stage.clientHeight,false);
  moveTo(positions,camera,animate);updateStory();
}
function focusClass(id) {
  pauseTour();CC.focus=id;
  const step=DemoModel.tour.findIndex(s=>s.view===CC.view.id&&s.focus===id);
  if(step>=0)CC.step=step;
  focusLayout();byId('announcement').textContent=`Focused ${nodesById.get(id).label}, ${CC.neighbors.length} direct neighbors in ${CC.view.label}.`;
}
let resizeFrame=0;
new ResizeObserver(()=>{
  cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{
    const previous=CC.metrics,next=DemoLayout.metrics(innerWidth,innerHeight);
    const changed=next.w!==previous.w||next.h!==previous.h;
    if(changed&&CC.mode==='explore') {
      const positions=CC.animating?CC.targetPositions:CC.positions;
      stopMotion();
      CC.positions=Object.fromEntries(Object.entries(positions).map(([id,p])=>[id,{
        x:CC.camera.x+(p.x-CC.camera.x)*next.dx/previous.dx,
        y:CC.camera.y+(p.y-CC.camera.y)*next.dy/previous.dy}]));
      CC.targetPositions=structuredClone(CC.positions);
    }
    CC.metrics=next;
    if(changed)drawView();
    if(CC.mode==='focus')focusLayout(false);
    else if(CC.mode==='map')showMap(false);
    else{stopMotion();settleRoutes();paint();}
  });
}).observe(stage);
