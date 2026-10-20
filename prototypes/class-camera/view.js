'use strict';
DemoLayout.validate(DemoModel);
const byId=id=>document.getElementById(id),SVG_NS='http://www.w3.org/2000/svg';
const CC={model:DemoModel,view:DemoModel.views[0],focus:'order',step:0,playing:false,mode:'focus',
  positions:{},routes:{},camera:{x:0,y:0,k:1},animation:0,animating:false,timer:0,
  metrics:DemoLayout.metrics(innerWidth,innerHeight),nodeEls:new Map(),edgeEls:new Map(),neighbors:[],dense:false};
const nodesById=new Map(DemoModel.nodes.map(n=>[n.id,n]));
const edgesById=new Map(DemoModel.edges.map(e=>[e.id,e]));
const stage=byId('stage'),svg=byId('diagram'),world=byId('world');
function element(tag,attrs={},text) {
  const result=document.createElementNS(SVG_NS,tag);
  for(const [name,value]of Object.entries(attrs))result.setAttribute(name,value);
  if(text!==undefined)result.textContent=text;return result;
}
function add(parent,tag,attrs,text){const child=element(tag,attrs,text);parent.append(child);return child;}
function localNodes(){return CC.view.nodes.map(id=>nodesById.get(id));}
function localEdges(){return CC.view.edges.map(id=>edgesById.get(id));}
function drawView() {
  world.replaceChildren();CC.nodeEls.clear();CC.edgeEls.clear();CC.routes={};
  const defs=add(world,'defs');
  for(const [name,d,fill,refX]of [['diamond','M0 6 L6 1 L12 6 L6 11 Z','#efa86d',0],
    ['triangle','M1 1 L12 6 L1 11 Z','#202420',12]]) {
    const marker=add(defs,'marker',{id:name,viewBox:'0 0 14 12',refX,refY:6,markerWidth:13,markerHeight:12,orient:'auto',markerUnits:'userSpaceOnUse'});
    add(marker,'path',{d,fill,stroke:'#efa86d','stroke-width':1.4});
  }
  for(const edge of localEdges()) {
    const g=add(world,'g',{class:'edge',tabindex:0,role:'button','data-edge':edge.id,
      'aria-label':`${nodesById.get(edge.from).label} ${edge.label} ${nodesById.get(edge.to).label}. ${edge.kind}. Inspect relationship.`});
    add(g,'path',{class:'hit'});const path=add(g,'path',{class:'stroke'});
    if(edge.kind==='composition')path.setAttribute('marker-start','url(#diamond)');
    if(edge.kind==='inheritance')path.setAttribute('marker-end','url(#triangle)');
    add(g,'text',{class:'label','text-anchor':'middle'},edge.label);
    for(const key of ['sourceMultiplicity','targetMultiplicity'])if(edge[key])add(g,'text',{class:`multiplicity ${key}`},edge[key]);
    const inspect=()=>showDetails(`${nodesById.get(edge.from).label} → ${nodesById.get(edge.to).label}`,edge.detail,
      [`Relationship: ${edge.kind}`,`Diagram: ${CC.view.label}`,
        ...(edge.sourceMultiplicity?[`${nodesById.get(edge.from).label}: ${edge.sourceMultiplicity}; ${nodesById.get(edge.to).label}: ${edge.targetMultiplicity}`]:[])]);
    g.addEventListener('click',()=>{if(!CC.suppressClick)inspect();});
    g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();inspect();}});
    CC.edgeEls.set(edge.id,g);
  }
  const {w,h}=CC.metrics;
  for(const node of localNodes()) {
    const g=add(world,'g',{class:'node',tabindex:0,role:'button','data-node':node.id,
      'aria-label':`${node.label}. Focus class and show its direct relationships.`});
    add(g,'rect',{x:-w/2,y:-h/2,width:w,height:h,rx:5});
    const title=add(g,'text',{class:'title',x:0,y:-h/2+(CC.metrics.mobile?21:25),'text-anchor':'middle'},node.label);
    title.style.fontSize=Math.min(CC.metrics.mobile?13:16,(w-16)/(node.label.length*.62))+'px';
    add(g,'line',{x1:-w/2,y1:-h/2+(CC.metrics.mobile?30:36),x2:w/2,y2:-h/2+(CC.metrics.mobile?30:36)});
    add(g,'text',{class:'member',x:-w/2+10,y:CC.metrics.mobile?8:3},node.fields[0]);
    add(g,'line',{x1:-w/2,y1:CC.metrics.mobile?14:15,x2:w/2,y2:CC.metrics.mobile?14:15});
    add(g,'text',{class:'member',x:-w/2+10,y:CC.metrics.mobile?28:39},node.methods[0]);
    const focus=()=>focusClass(node.id);
    g.addEventListener('click',()=>{if(!CC.suppressClick)focus();});
    g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();focus();}});
    CC.nodeEls.set(node.id,g);
    CC.positions[node.id]??={...node.home};
  }
  byId('view').value=CC.view.id;
}
function paint() {
  const width=stage.clientWidth,height=stage.clientHeight;
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
  const c=CC.camera;
  world.setAttribute('transform',`translate(${width/2} ${height/2}) scale(${c.k}) translate(${-c.x} ${-c.y})`);
  const visible=new Set([CC.focus,...CC.neighbors]);
  for(const [id,g]of CC.nodeEls) {
    const p=CC.positions[id];g.setAttribute('transform',`translate(${p.x} ${p.y})`);
    g.classList.toggle('current',id===CC.focus);g.classList.toggle('context',!visible.has(id));
    g.classList.toggle('offstage',CC.mode==='focus'&&!visible.has(id));
  }
  const labels=[];
  const touchesClass=(x,y,w)=>Object.values(CC.positions).some(p=>
    x+w/2>p.x-CC.metrics.w/2-2&&x-w/2<p.x+CC.metrics.w/2+2&&
    y+3>p.y-CC.metrics.h/2-2&&y-11<p.y+CC.metrics.h/2+2);
  for(const edge of localEdges()) {
    const g=CC.edgeEls.get(edge.id),active=edge.from===CC.focus||edge.to===CC.focus;
    g.classList.toggle('active',active);g.classList.toggle('context',!active);
    g.classList.toggle('offstage',CC.mode==='focus'&&!active);
    const points=CC.animating?DemoRouting.transient(CC.positions[edge.from],CC.positions[edge.to],CC.metrics):CC.routes[edge.id];
    if(!points)continue;
    const path=points.map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ');
    g.querySelectorAll('path').forEach(p=>p.setAttribute('d',path));
    const candidates=points.slice(1).map((p,i)=>({a:points[i],b:p,length:Math.abs(p.x-points[i].x)+Math.abs(p.y-points[i].y)}));
    candidates.sort((a,b)=>b.length-a.length);
    const text=g.querySelector('.label');let placed=false;
    for(const segment of candidates.filter(s=>s.a.y===s.b.y&&s.length>edge.label.length*7+12)) {
      const x=(segment.a.x+segment.b.x)/2,y=segment.a.y+4,w=edge.label.length*7;
      if(labels.some(b=>Math.abs(b.x-x)<(b.w+w)/2+8&&Math.abs(b.y-y)<19))continue;
      if(touchesClass(x,y,w))continue;
      text.setAttribute('x',x);text.setAttribute('y',y);labels.push({x,y,w});placed=true;break;
    }
    text.style.display=placed?'':'none';
    for(const [key,p,q]of [['sourceMultiplicity',points[0],points[1]],['targetMultiplicity',points.at(-1),points.at(-2)]]) {
      const t=g.querySelector(`.${key}`);
      if(t){
        const dx=Math.sign(q.x-p.x),dy=Math.sign(q.y-p.y),w=edge[key].length*7;
        const x=p.x+(dx?dx*8:10),y=p.y+(dy>0?18:dy<0?-10:-8),left=dx<0?x-w:x;
        t.setAttribute('x',x);t.setAttribute('y',y);t.setAttribute('text-anchor',dx<0?'end':'start');
        // Keep cardinalities out of class interiors. The inspector retains their
        // full values when a narrow endpoint gap cannot hold a visible label.
        t.style.display=touchesClass(left+w/2,y,w)?'none':'';
      }
    }
  }
  stage.classList.toggle('moving',CC.animating);
  byId('scale').textContent=`${Math.round(c.k*100)}%`;
  byId('follow').setAttribute('aria-pressed',String(CC.mode==='focus'));
  byId('resume').hidden=CC.mode==='focus';
  byId('play').textContent=CC.playing?'Pause Ⅱ':CC.mode==='focus'?'Play tour ▷':'Resume tour ▷';
  byId('mode').textContent=CC.mode==='focus'?`Following ${nodesById.get(CC.focus).label}`:CC.mode==='map'?'View map · paused':'Exploring · tour paused';
  byId('density').textContent=`${CC.metrics.cols} × ${CC.metrics.rows} window${CC.dense?' · denser to show all neighbors':''}`;
  paintMinimap();
}
function paintMinimap() {
  const mini=byId('minimap'),m=CC.metrics,b=DemoLayout.extent(CC.positions,CC.view.nodes,m);
  const k=Math.min(184/(b.right-b.left+80),94/(b.bottom-b.top+80));
  const ox=(200-(b.right-b.left)*k)/2-b.left*k,oy=(110-(b.bottom-b.top)*k)/2-b.top*k;
  CC.mini={k,ox,oy};mini.setAttribute('viewBox','0 0 200 110');mini.replaceChildren();
  for(const id of CC.view.nodes){const p=CC.positions[id];add(mini,'rect',{
    x:ox+(p.x-m.w/2)*k,y:oy+(p.y-m.h/2)*k,width:Math.max(3,m.w*k),height:Math.max(2,m.h*k),
    fill:id===CC.focus?'#efa86d':'#687f69'});}
  const width=stage.clientWidth/CC.camera.k,height=stage.clientHeight/CC.camera.k;
  add(mini,'rect',{class:'roi',x:ox+(CC.camera.x-width/2)*k,y:oy+(CC.camera.y-height/2)*k,width:width*k,height:height*k});
}
function settleRoutes() {
  CC.routes={};
  for(const edge of localEdges())CC.routes[edge.id]=DemoRouting.route(CC.positions[edge.from],CC.positions[edge.to],CC.positions,CC.metrics);
}
