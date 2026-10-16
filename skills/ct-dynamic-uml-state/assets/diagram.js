'use strict';
let model=JSON.parse(document.getElementById('diagram-data').textContent);
const $=id=>document.getElementById(id), ns='http://www.w3.org/2000/svg';
const svg=$('diagram'); let index=0,scenario=0,timer=null,overview=false,selected=null,sidebar=false;
let deadline=0,resumeAfterDetails=false,resumeDelay=0,detailsTrigger=null;
const nodeMap=new Map(model.nodes.map(n=>[n.id,n]));
const edgeMap=new Map(model.edges.map(e=>[e.id,e]));
const nodeEls=new Map(),edgeEls=new Map(),flowStack=[];
let pickerFocus=0,typeahead='',typeaheadAt=0;
function el(tag,attrs={},text){const e=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,String(v));if(text!==undefined)e.textContent=text;return e}
function append(parent,tag,attrs,text){const e=el(tag,attrs,text);parent.append(e);return e}
function steps(){return model.scenarios[scenario].steps}
function text(id,value){$(id).textContent=value}
function drawDefs(){const defs=append(svg,'defs');for(const [id,color]of [['normal','#9eb9a5'],['active','#efa86d'],['selected','#a5cdb3']]){for(const kind of ['call','open','triangle','diamond','hollow']){const isDiamond=['diamond','hollow'].includes(kind);const m=append(defs,'marker',{id:`${id}-${kind}`,viewBox:'0 0 14 14',refX:isDiamond?0:13,refY:7,markerWidth:isDiamond?12:10,markerHeight:10,orient:'auto',markerUnits:'userSpaceOnUse'});append(m,'path',{d:isDiamond?'M0 7 L7 2 L14 7 L7 12 Z':kind==='open'?'M2 2 L12 7 L2 12': 'M2 2 L12 7 L2 12 Z',fill:kind==='call'||kind==='diamond'?color:kind==='open'?'none':'#202420',stroke:color,'stroke-width':1.5});}}}
function marker(edge,state){const k=edge.kind;if(k==='composition'||k==='aggregation')return ['marker-start',`url(#${state}-${k==='composition'?'diamond':'hollow'})`];if(k==='inheritance')return ['marker-end',`url(#${state}-triangle)`];if(k==='association')return null;return ['marker-end',`url(#${state}-${k==='call'?'call':'open'})`]}
function activate(g,kind,id){g.setAttribute('tabindex','0');g.setAttribute('role','button');g.setAttribute('aria-label',`${kind}: ${(kind==='Node'?nodeMap:edgeMap).get(id).label}`);const select=()=>{selected={kind,id};const item=(kind==='Node'?nodeMap:edgeMap).get(id);text('inspect-title',item.label);text('inspect-body',item.detail||'No additional detail supplied.');$('open-subflow').hidden=!(kind==='Node'&&item.subflow);text('open-subflow',model.type==='state'?'Explore state detail ↓':'Explore subprocess ↓');update();if(!sidebar)openDetails();};g.addEventListener('click',select);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();select();}})}
function nodeSize(n){const w=n.w||180;const h=['initial','final'].includes(n.kind)?24:['fork','join'].includes(n.kind)?8:n.kind==='class'?64+22*((n.fields||[]).length+(n.methods||[]).length):n.h||66;return {w:['initial','final'].includes(n.kind)?24:w,h};}
function bounds(n){const s=nodeSize(n);return {...s,x:n.x-s.w/2,y:n.y-s.h/2}}
function anchor(n,toward){const s=nodeSize(n),dx=toward.x-n.x,dy=toward.y-n.y;if(['fork','join'].includes(n.kind))return {x:Math.max(n.x-s.w/2,Math.min(n.x+s.w/2,toward.x)),y:n.y+(dy>=0?4:-4)};if(!dx&&!dy)return {x:n.x,y:n.y};const a=['initial','final'].includes(n.kind)?12/Math.hypot(dx,dy):n.kind==='decision'?1/(Math.abs(dx)/(s.w/2)+Math.abs(dy)/(s.h/2)):Math.min(dx?Math.abs(s.w/2/dx):Infinity,dy?Math.abs(s.h/2/dy):Infinity);return {x:n.x+dx*a,y:n.y+dy*a}}
function port(n,side){const b=bounds(n);return {top:{x:n.x,y:b.y},bottom:{x:n.x,y:b.y+b.h},left:{x:b.x,y:n.y},right:{x:b.x+b.w,y:n.y}}[side];}
function drawNode(n,root=svg){const g=append(root,'g',{class:'node','data-node':n.id});nodeEls.set(n.id,g);const b=bounds(n);if(n.kind==='decision'){append(g,'path',{class:'shape',d:`M${n.x} ${b.y} L${b.x+b.w} ${n.y} L${n.x} ${b.y+b.h} L${b.x} ${n.y} Z`});}else if(n.kind==='initial'||n.kind==='final'){append(g,'circle',{class:n.kind==='initial'?'solid':'shape',cx:n.x,cy:n.y,r:12});if(n.kind==='final')append(g,'circle',{class:'solid',cx:n.x,cy:n.y,r:7});}else{append(g,'rect',{class:['fork','join'].includes(n.kind)?'solid':'shape',x:b.x,y:b.y,width:b.w,height:b.h,rx:['state','action','terminal'].includes(n.kind)?n.kind==='terminal'?33:13:4});}
if(!['initial','final','fork','join'].includes(n.kind)){if(n.kind==='class'){append(g,'text',{class:'node-title',x:n.x,y:b.y+27,'text-anchor':'middle'},n.label);append(g,'line',{class:'separator',x1:b.x,y1:b.y+40,x2:b.x+b.w,y2:b.y+40});let y=b.y+59;for(const field of n.fields||[]){append(g,'text',{class:'member',x:b.x+12,y},field);y+=22;}append(g,'line',{class:'separator',x1:b.x,y1:y-8,x2:b.x+b.w,y2:y-8});for(const method of n.methods||[]){append(g,'text',{class:'member',x:b.x+12,y:y+11},method);y+=22;}}else{append(g,'text',{class:'node-title',x:n.x,y:n.y+(n.role?-3:5),'text-anchor':'middle'},n.label);if(n.role)append(g,'text',{class:'member',x:n.x,y:n.y+19,'text-anchor':'middle'},n.role);if(n.kind==='component'){append(g,'rect',{x:b.x+b.w-26,y:b.y+7,width:15,height:20,fill:'none',stroke:'#a5cdb3'});for(const y of [b.y+11,b.y+21])append(g,'rect',{x:b.x+b.w-30,y,width:7,height:4,fill:'#29332b',stroke:'#a5cdb3'});}}}if(n.kind==='state'&&n.subflow)append(g,'text',{class:'member',x:b.x+b.w-16,y:b.y+19,'text-anchor':'middle'},'+');if(n.kind==='subprocess'){for(const x of [b.x+12,b.x+b.w-12])append(g,'line',{class:'separator',x1:x,y1:b.y,x2:x,y2:b.y+b.h});}activate(g,'Node',n.id);}
function drawEdge(e,i){const a=nodeMap.get(e.from),b=nodeMap.get(e.to);let coords;if(model.type==='sequence'){const y=142+i*68;if(a.id===b.id)coords=[{x:a.x,y},{x:a.x+72,y},{x:a.x+72,y:y+30},{x:a.x,y:y+30}];else coords=[{x:a.x,y},{x:b.x,y}];}else{const middle=e.via||[];coords=[e.fromPort?port(a,e.fromPort):anchor(a,middle[0]||b),...middle,e.toPort?port(b,e.toPort):anchor(b,middle[middle.length-1]||a)];}
const g=append(svg,'g',{class:'edge','data-edge':e.id});edgeEls.set(e.id,g);const d=coords.map((p,j)=>`${j?'L':'M'}${p.x} ${p.y}`).join(' ');append(g,'path',{class:'hit',d});const path=append(g,'path',{class:'visible',d});if(['return','dependency'].includes(e.kind))path.setAttribute('stroke-dasharray','6 5');const mk=marker(e,'normal');if(mk)path.setAttribute(...mk);const mid=e.labelAt||{x:(coords[0].x+coords.at(-1).x)/2,y:(coords[0].y+coords.at(-1).y)/2-10};if(model.type==='state'){
const segment=e.labelOn.segment,at=e.labelOn.at??0.5,a=coords[segment],b=coords[segment+1];
const x=a.x+(b.x-a.x)*at,y=a.y+(b.y-a.y)*at;
const label=append(g,'g',{class:'transition-label','data-label-segment':segment,transform:`translate(${x} ${y})${a.x===b.x?' rotate(-90)':''}`});
const t=append(label,'text',{x:0,y:0,'text-anchor':'middle','dominant-baseline':'middle'},e.label);
const width=t.getComputedTextLength()+16;
const backing=el('rect',{class:'transition-label-bg',x:-width/2,y:-10,width,height:20,rx:3});label.insertBefore(backing,t);
}else append(g,'text',{x:mid.x,y:mid.y,'text-anchor':'middle'},e.label);if(model.type==='sequence'){append(g,'circle',{class:'number-disc',cx:coords[0].x,cy:coords[0].y,r:10});append(g,'text',{class:'message-number',x:coords[0].x,y:coords[0].y+3.5,'text-anchor':'middle',style:'stroke:none'},i+1);}else{const first=coords[0],last=coords.at(-1),horizontal=Math.abs(last.x-first.x)>Math.abs(last.y-first.y);for(const [key,p,direction]of [['sourceMultiplicity',first,1],['targetMultiplicity',last,-1]])if(e[key])append(g,'text',{x:horizontal?p.x+direction*16*Math.sign(last.x-first.x):p.x-18,y:horizontal?p.y+20:p.y+direction*20*Math.sign(last.y-first.y),'text-anchor':'middle'},e[key]);}activate(g,'Relationship',e.id);}
function draw(){$('canvas-scroll').classList.toggle('sequence-view',model.type==='sequence');$('canvas-scroll').classList.toggle('flowchart-view',model.type==='flowchart');$('canvas-scroll').classList.toggle('state-view',model.type==='state');$('canvas-scroll').style.setProperty('--flow-width',model.width+'px');$('canvas-scroll').style.setProperty('--readable-width',(model.width*10/11)+'px');svg.setAttribute('viewBox',model.type==='sequence'?`0 90 ${model.width} ${model.height-90}`:`0 0 ${model.width} ${model.height}`);append(svg,'title',{id:'svg-title'},model.title);append(svg,'desc',{id:'svg-description'},model.lede+' Use the walkthrough and inspector for a text explanation.');drawDefs();if(model.type==='sequence')for(const n of model.nodes)append(svg,'line',{class:'lifeline','data-lifeline':n.id,x1:n.x,x2:n.x,y1:88,y2:model.height-20});model.edges.forEach(drawEdge);if(model.type==='sequence'){const strip=$('participant-headings');strip.hidden=false;const head=append(strip,'svg',{viewBox:`0 0 ${model.width} 90`,role:'group','aria-label':'Participants'});append(head,'rect',{width:model.width,height:90,fill:'#202420'});model.nodes.forEach(n=>drawNode(n,head));}else model.nodes.forEach(n=>drawNode(n));}
// Reposition only the rendered view. The source model and message chronology stay unchanged.
function wrapSVGText(t,value,width,x,y,size){
  t.style.fontSize=size+'px';t.replaceChildren();
  const lines=[];let line='';
  for(const word of value.split(/\s+/)){
    const candidate=line?line+' '+word:word;t.textContent=candidate;
    if(line&&t.getComputedTextLength()>width){lines.push(line);line=word;}else line=candidate;
    t.textContent=line;
    while(t.getComputedTextLength()>width&&line.length>1){
      let cut=line.length-1;t.textContent=line.slice(0,cut);
      while(cut>1&&t.getComputedTextLength()>width){cut--;t.textContent=line.slice(0,cut);}
      lines.push(line.slice(0,cut));line=line.slice(cut);t.textContent=line;
    }
  }
  if(line)lines.push(line);t.replaceChildren();
  lines.forEach((value,i)=>append(t,'tspan',{x,y:y+(i-(lines.length-1)/2)*(size+2)},value));
}
function sequenceNeighbors(step){
  const indices=step.edges.map(id=>model.edges.findIndex(e=>e.id===id));
  return indices.length?[model.edges[Math.min(...indices)-1],model.edges[Math.max(...indices)+1]]:[];
}
function layoutSequence(){
  if(model.type!=='sequence')return;
  const frame=$('canvas-scroll'),head=$('participant-headings').querySelector('svg');
  frame.classList.toggle('folded',!overview);
  const ordered=[...model.nodes].sort((a,b)=>a.x-b.x),current=steps()[index];
  const visible=new Set(overview?ordered.map(n=>n.id):current.nodes);
  if(!overview)for(const id of current.edges){const edge=edgeMap.get(id);visible.add(edge.from);visible.add(edge.to);}
  const width=overview?model.width:Math.max(1,Math.floor(frame.clientWidth-32));
  const small=width<500,density=Math.max(0,Math.min(1,(width-320)/400));
  const gap=8+16*density,dotWidth=20+12*density,margin=8+8*density;
  const makeTokens=shown=>{
    const list=[];
    for(const node of ordered){
      if(shown.has(node.id))list.push({node});
      else if(list.at(-1)?.omitted)list.at(-1).omitted.push(node);
      else list.push({omitted:[node]});
    }
    // At sidebar widths, keep the internal omission cue and give names room.
    if(!overview&&width<260){if(list[0]?.omitted)list.shift();if(list.at(-1)?.omitted)list.pop();}
    return list;
  };
  const fits=shown=>{
    const list=makeTokens(shown);
    const needed=list.reduce((sum,t)=>sum+(t.node?Math.min(t.node.w||180,128):dotWidth),0)+gap*(list.length-1)+margin*2;
    return needed<=width;
  };
  if(!overview){
    // Prefer surrounding messages, then fill remaining room with nearby participants.
    const [previous,next]=sequenceNeighbors(current);
    const context=[previous?.from,next?.from,previous?.to,next?.to].filter(Boolean);
    const anchors=ordered.map((n,i)=>visible.has(n.id)?i:-1).filter(i=>i>=0);
    const nearby=ordered.map((n,i)=>({id:n.id,distance:Math.min(...anchors.map(a=>Math.abs(a-i)))}))
      .sort((a,b)=>a.distance-b.distance).map(n=>n.id);
    for(const id of new Set([...context,...nearby])){
      if(visible.has(id))continue;
      const expanded=new Set([...visible,id]);if(fits(expanded))visible.add(id);
    }
  }
  const tokens=makeTokens(visible),count=visible.size,omitted=tokens.filter(t=>t.omitted).length;
  const allowance=(width-margin*2-gap*(tokens.length-1)-dotWidth*omitted)/count;
  for(const token of tokens)token.width=token.node?Math.min(token.node.w||180,small?128:220,Math.max(24,allowance)):dotWidth;
  const used=tokens.reduce((sum,t)=>sum+t.width,0)+gap*(tokens.length-1);
  const positions=new Map();let cursor=(width-used)/2;
  for(const token of tokens){token.x=cursor+token.width/2;cursor+=token.width+gap;if(token.node)positions.set(token.node.id,token.x);}
  svg.setAttribute('viewBox',`0 90 ${width} ${model.height-90}`);head.setAttribute('viewBox',`0 0 ${width} 90`);
  head.querySelector('rect').setAttribute('width',width);
  head.querySelector('.sequence-omissions')?.remove();
  const omissions=el('g',{class:'sequence-omissions'});head.insertBefore(omissions,head.querySelector('[data-node]'));
  if(!overview)for(const token of tokens.filter(t=>t.omitted)){
    const names=token.omitted.map(n=>n.label).join(', ');
    const g=append(omissions,'g',{class:'sequence-omission',role:'button',tabindex:0,'aria-label':`${token.omitted.length} omitted participants: ${names}. Show overview.`,'data-omitted':token.omitted.map(n=>n.id).join(' ')});
    append(g,'title',{},`Omitted: ${names}. Show all in Overview.`);
    append(g,'rect',{x:token.x-22,y:23,width:44,height:44,fill:'transparent'});
    append(g,'text',{x:token.x,y:51,'text-anchor':'middle','aria-hidden':'true'},'…');
    const expand=()=>{overview=true;$('overview').setAttribute('aria-pressed','true');update();followActive();$('overview').focus({preventScroll:true});};
    g.addEventListener('click',expand);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();expand();}});
  }
  for(const n of ordered){
    const g=nodeEls.get(n.id),shown=visible.has(n.id);g.style.display=shown?'':'none';
    const line=svg.querySelector(`[data-lifeline="${n.id}"]`);line.style.display=shown?'':'none';
    if(!shown)continue;
    const token=tokens.find(t=>t.node?.id===n.id),x=overview?n.x:positions.get(n.id),w=overview?(n.w||180):token.width;
    const shape=g.querySelector('.shape');shape.setAttribute('x',x-w/2);shape.setAttribute('width',w);
    line.setAttribute('x1',x);line.setAttribute('x2',x);
    const title=g.querySelector('.node-title'),role=g.querySelector('.member'),showRole=overview||w>=128;
    if(role)role.style.display=showRole?'':'none';
    wrapSVGText(title,n.label,w-16,x,n.y+(showRole?-3:5),small&&!overview?12:14);
    if(role&&showRole)wrapSVGText(role,n.role,w-16,x,n.y+19,12);
  }
  model.edges.forEach((edge,i)=>{
    const g=edgeEls.get(edge.id),shown=visible.has(edge.from)&&visible.has(edge.to);g.style.display=shown?'':'none';if(!shown)return;
    const y=142+i*68,a=overview?nodeMap.get(edge.from).x:positions.get(edge.from),b=overview?nodeMap.get(edge.to).x:positions.get(edge.to);
    const loop=overview?72:Math.min(72,Math.max(16,width-a-12));
    const points=edge.from===edge.to?[{x:a,y},{x:a+loop,y},{x:a+loop,y:y+30},{x:a,y:y+30}]:[{x:a,y},{x:b,y}];
    const d=points.map((p,j)=>`${j?'L':'M'}${p.x} ${p.y}`).join(' ');g.querySelectorAll('path').forEach(path=>path.setAttribute('d',d));
    const label=g.querySelector('text'),disc=g.querySelector('circle'),number=g.querySelector('.message-number');
    disc.setAttribute('cx',a);number.setAttribute('x',a);
    const midpoint=edge.from===edge.to?a+loop/2:(a+b)/2;
    if(overview){label.style.fontSize='11px';label.replaceChildren(document.createTextNode(edge.label));label.setAttribute('x',edge.labelAt?.x??a);label.setAttribute('y',edge.labelAt?.y??(edge.from===edge.to?y+5:y-10));if(!edge.labelAt)label.setAttribute('x',edge.from===edge.to?a:(a+b)/2);}
    else{
      const maxWidth=Math.max(16,Math.min(width-16,Math.max(100,Math.abs(b-a)-12)));
      label.textContent=edge.label;label.style.fontSize='11px';
      const actual=Math.min(maxWidth,label.getComputedTextLength());
      const x=Math.max(actual/2+8,Math.min(width-actual/2-8,midpoint));
      wrapSVGText(label,edge.label,maxWidth,x,y-10,11);
    }
  });
  if(!overview)frame.scrollLeft=0;
  text('canvas-label',overview?`Overview / all ${ordered.length} participants`:`Walkthrough / ${visible.size} of ${ordered.length} participants${omitted?' · … omitted':''}`);
  const hint=document.querySelector('.mobile-hint');hint.style.display=overview&&frame.scrollWidth>frame.clientWidth+1?'inline':'none';
}
