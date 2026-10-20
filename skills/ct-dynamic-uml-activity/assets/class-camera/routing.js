'use strict';
const DemoRouting = (() => {
  // An orthogonal visibility graph routes through gaps, never class interiors.
  function route(a,b,positions,m) {
    const horizontal=Math.abs(b.x-a.x)>=Math.abs(b.y-a.y);
    const sign=horizontal?Math.sign(b.x-a.x)||1:Math.sign(b.y-a.y)||1;
    const portStart=horizontal?{x:a.x+sign*m.w/2,y:a.y}:{x:a.x,y:a.y+sign*m.h/2};
    const portEnd=horizontal?{x:b.x-sign*m.w/2,y:b.y}:{x:b.x,y:b.y-sign*m.h/2};
    const start=horizontal?{x:portStart.x+sign*14,y:portStart.y}:{x:portStart.x,y:portStart.y+sign*14};
    const end=horizontal?{x:portEnd.x-sign*14,y:portEnd.y}:{x:portEnd.x,y:portEnd.y-sign*14};
    const boxes=Object.values(positions).map(p=>({l:p.x-m.w/2,r:p.x+m.w/2,t:p.y-m.h/2,b:p.y+m.h/2}));
    const xs=[...new Set([start.x,end.x,...boxes.flatMap(r=>[r.l-14,r.r+14])])].sort((a,b)=>a-b);
    const ys=[...new Set([start.y,end.y,...boxes.flatMap(r=>[r.t-14,r.b+14])])].sort((a,b)=>a-b);
    const blocked=(p,q)=>boxes.some(r=>p.x===q.x?
      p.x>r.l+.1&&p.x<r.r-.1&&Math.max(p.y,q.y)>r.t+.1&&Math.min(p.y,q.y)<r.b-.1:
      p.y>r.t+.1&&p.y<r.b-.1&&Math.max(p.x,q.x)>r.l+.1&&Math.min(p.x,q.x)<r.r-.1);
    const key=(x,y)=>`${x},${y}`,sx=xs.indexOf(start.x),sy=ys.indexOf(start.y);
    const ex=xs.indexOf(end.x),ey=ys.indexOf(end.y),first=key(sx,sy);
    const open=[{x:sx,y:sy,cost:0,score:0}],best=new Map([[first,0]]),previous=new Map();
    while(open.length) {
      open.sort((a,b)=>a.score-b.score);const current=open.shift(),identity=key(current.x,current.y);
      if(current.x===ex&&current.y===ey) {
        const points=[];let cursor=identity;
        while(cursor){const [x,y]=cursor.split(',').map(Number);points.unshift({x:xs[x],y:ys[y]});cursor=previous.get(cursor);}
        const simplified=points.filter((p,i)=>i===0||i===points.length-1||
          !((points[i-1].x===p.x&&p.x===points[i+1].x)||(points[i-1].y===p.y&&p.y===points[i+1].y)));
        return [portStart,...simplified,portEnd];
      }
      if(current.cost>best.get(identity))continue;
      for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
        const x=current.x+dx,y=current.y+dy;
        if(x<0||y<0||x>=xs.length||y>=ys.length)continue;
        const p={x:xs[current.x],y:ys[current.y]},q={x:xs[x],y:ys[y]};
        if(blocked(p,q))continue;
        const cost=current.cost+Math.abs(p.x-q.x)+Math.abs(p.y-q.y),next=key(x,y);
        if(cost>=(best.get(next)??Infinity))continue;
        best.set(next,cost);previous.set(next,identity);
        open.push({x,y,cost,score:cost+Math.abs(q.x-end.x)+Math.abs(q.y-end.y)});
      }
    }
    throw Error('No collision-free class relationship route');
  }
  function transient(a,b,m) {
    const sign=Math.sign(b.x-a.x)||1;
    return [{x:a.x+sign*m.w/2,y:a.y},{x:(a.x+b.x)/2,y:a.y},
      {x:(a.x+b.x)/2,y:b.y},{x:b.x-sign*m.w/2,y:b.y}];
  }
  return {route,transient};
})();
if(typeof module!=='undefined')module.exports=DemoRouting;
