'use strict';
const DemoLayout = (() => {
  function metrics(width,height) {
    const mobile=width<700 || (height<500 && width<1100);
    const landscape=mobile&&width>height,dx=mobile?(landscape?150:132):264,dy=mobile?(landscape?90:104):180;
    return {cols:mobile?(landscape?5:3):5,rows:mobile?(landscape?3:5):5,
      w:mobile?(landscape?126:112):208,h:mobile?(landscape?70:78):124,dx,dy,mobile,
      bias:Math.max(.4,Math.min(3.5,width/Math.max(180,height-300)*dy/dx))};
  }
  function neighborhood(focus,edges) {
    return [...new Set(edges.filter(e=>e.from===focus||e.to===focus)
      .flatMap(e=>[e.from,e.to]).filter(id=>id!==focus))];
  }
  function focusLayout(nodes,edges,focus,m) {
    const center=nodes.find(n=>n.id===focus).home;
    const neighbors=neighborhood(focus,edges);
    const slots=[]; let cols=m.cols,rows=m.rows;
    // Keep all direct neighbors: a narrow device may use a denser arrangement.
    while(cols*rows<neighbors.length+1) { if(cols<=rows)cols+=2;else rows+=2; }
    for(let y=-Math.floor(rows/2);y<=Math.floor(rows/2);y++)
      for(let x=-Math.floor(cols/2);x<=Math.floor(cols/2);x++)
        if(x||y) slots.push({x,y});
    slots.sort((a,b)=>(a.x*a.x+(a.y*m.bias)**2)-(b.x*b.x+(b.y*m.bias)**2)||a.y-b.y||a.x-b.x);
    const positions={[focus]:{...center}},occupied=new Set(['0,0']);
    neighbors.forEach((id,i)=>{
      const p=slots[i];occupied.add(`${p.x},${p.y}`);
      positions[id]={x:center.x+p.x*m.dx,y:center.y+p.y*m.dy};
    });
    // Place background classes on free lattice cells, outside the focus window.
    // Manual exploration reveals this complete, collision-free temporary map.
    for(const node of nodes.filter(n=>!positions[n.id])) {
      const x=Math.round((node.home.x-center.x)/m.dx),y=Math.round((node.home.y-center.y)/m.dy);
      const candidates=[];
      for(let r=0;r<16;r++) {
        for(let cy=y-r;cy<=y+r;cy++) for(let cx=x-r;cx<=x+r;cx++) {
          if(Math.abs(cx)<=(cols-1)/2&&Math.abs(cy)<=(rows-1)/2)continue;
          if(!occupied.has(`${cx},${cy}`))candidates.push({x:cx,y:cy,d:(cx-x)**2+(cy-y)**2});
        }
        if(candidates.length)break;
      }
      candidates.sort((a,b)=>a.d-b.d||a.y-b.y||a.x-b.x);
      const p=candidates[0];occupied.add(`${p.x},${p.y}`);
      positions[node.id]={x:center.x+p.x*m.dx,y:center.y+p.y*m.dy};
    }
    return {positions,neighbors,dense:neighbors.length+1>m.cols*m.rows};
  }
  function extent(positions,ids,m) {
    const points=ids.map(id=>positions[id]);
    return {left:Math.min(...points.map(p=>p.x-m.w/2)),right:Math.max(...points.map(p=>p.x+m.w/2)),
      top:Math.min(...points.map(p=>p.y-m.h/2)),bottom:Math.max(...points.map(p=>p.y+m.h/2))};
  }
  function cameraFor(positions,ids,focus,m,width,height,centered=true) {
    const bounds=extent(positions,ids,m),c=positions[focus];
    const x=centered?c.x:(bounds.left+bounds.right)/2,y=centered?c.y:(bounds.top+bounds.bottom)/2;
    const w=centered?2*Math.max(x-bounds.left,bounds.right-x):bounds.right-bounds.left;
    const h=centered?2*Math.max(y-bounds.top,bounds.bottom-y):bounds.bottom-bounds.top;
    return {x,y,k:Math.min(m.mobile?1.35:1.65,(width-20)/Math.max(w+12,1),(height-(m.mobile?36:48))/Math.max(h+8,1))};
  }
  function validate(model) {
    const nodes=new Set(model.nodes.map(n=>n.id)),covered=new Set();
    if(nodes.size!==model.nodes.length)throw Error('Duplicate classes');
    for(const view of model.views) {
      const local=new Set(view.nodes),degree=new Map();
      for(const id of view.edges) {
        const edge=model.edges.find(e=>e.id===id);
        if(!edge||!nodes.has(edge.from)||!nodes.has(edge.to)||!local.has(edge.from)||!local.has(edge.to))
          throw Error('View relationship has an unknown endpoint');
        covered.add(id);
        for(const endpoint of [edge.from,edge.to])degree.set(endpoint,(degree.get(endpoint)||0)+1);
      }
      if([...degree.values()].some(count=>count>model.maxRelations))throw Error('Split views above 20 relationships');
    }
    if(covered.size!==model.edges.length)throw Error('A relationship is missing from the linked diagrams');
  }
  return {metrics,neighborhood,focusLayout,extent,cameraFor,validate};
})();
if (typeof module!=='undefined')module.exports=DemoLayout;
