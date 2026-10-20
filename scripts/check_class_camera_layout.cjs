const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.join(__dirname,'../skills/ct-dynamic-uml/assets/class-camera');
const prepare = require(path.join(root,'adapter.js'));
const model = prepare(require('../skills/ct-dynamic-uml/assets/examples/class.json'));
const layout = require(path.join(root,'layout.js'));
const routing = require(path.join(root,'routing.js'));

layout.validate(model);
assert.equal(model.nodes.length,48);
assert.equal(model.edges.filter(e=>e.from==='order'||e.to==='order').length,27);
const broken=structuredClone(model);
broken.views=[{id:'unsplit',nodes:model.nodes.map(n=>n.id),edges:model.edges.map(e=>e.id)}];
assert.throws(()=>layout.validate(broken),/Split views/);
const source=JSON.stringify(model);
for(const [width,height,grid]of [[1440,900,[5,5]],[390,844,[3,5]],[844,390,[5,3]]]) {
  const metrics=layout.metrics(width,height);
  assert.deepEqual([metrics.cols,metrics.rows],grid);
  for(const view of model.views) {
    const nodes=model.nodes.filter(n=>view.nodes.includes(n.id)),edges=model.edges.filter(e=>view.edges.includes(e.id));
    for(const node of nodes) {
      const result=layout.focusLayout(nodes,edges,node.id,metrics);
      assert.deepEqual(new Set(result.neighbors),new Set(edges.filter(e=>e.from===node.id||e.to===node.id)
        .flatMap(e=>[e.from,e.to]).filter(id=>id!==node.id)));
      for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++) {
        const a=result.positions[nodes[i].id],b=result.positions[nodes[j].id];
        assert(Math.abs(a.x-b.x)>=metrics.w || Math.abs(a.y-b.y)>=metrics.h,'Class cards cannot overlap');
      }
      const camera=layout.cameraFor(result.positions,[node.id,...result.neighbors],node.id,metrics,width,Math.max(200,height-250));
      assert(Number.isFinite(camera.k)&&camera.k>0);
      assert.equal(camera.x,result.positions[node.id].x);assert.equal(camera.y,result.positions[node.id].y);
    }
    // Route every relationship through a representative complete focus layout.
    const positions=layout.focusLayout(nodes,edges,'order',metrics).positions;
    for(const edge of edges) {
      const route=routing.route(positions[edge.from],positions[edge.to],positions,metrics);
      for(let i=1;i<route.length;i++) {
        const a=route[i-1],b=route[i];assert(a.x===b.x||a.y===b.y,'Routes are orthogonal');
        for(const position of Object.values(positions)) {
          const l=position.x-metrics.w/2,r=position.x+metrics.w/2,t=position.y-metrics.h/2,d=position.y+metrics.h/2;
          const intersects=a.x===b.x?a.x>l+.1&&a.x<r-.1&&Math.max(a.y,b.y)>t+.1&&Math.min(a.y,b.y)<d-.1:
            a.y>t+.1&&a.y<d-.1&&Math.max(a.x,b.x)>l+.1&&Math.min(a.x,b.x)<r-.1;
          assert(!intersects,`Relationship ${edge.id} crosses a class`);
        }
      }
    }
  }
}
// All-neighbor policy: a <=20-relation view must never silently omit neighbors.
const denseNodes=Array.from({length:21},(_,i)=>({id:`n${i}`,home:{x:i*280,y:0}}));
const denseEdges=denseNodes.slice(1).map(n=>({from:'n0',to:n.id}));
const dense=layout.focusLayout(denseNodes,denseEdges,'n0',layout.metrics(390,844));
assert.equal(dense.neighbors.length,20);assert.equal(dense.dense,true);
assert.equal(JSON.stringify(model),source,'Presentation cannot mutate the source model');
console.log('48-class model, complete linked views, 20-relation limit, responsive windows, all-neighbor policy, collision-free cards and routes passed.');
