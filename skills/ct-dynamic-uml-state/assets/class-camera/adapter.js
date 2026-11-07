'use strict';
function prepareClassModel(source) {
  const views=source.views||[{id:'structure',label:'Class diagram',nodes:source.nodes.map(n=>n.id),edges:source.edges.map(e=>e.id)}];
  const tour=source.scenarios.flatMap(s=>s.steps.map(step=>{
    const view=views.find(v=>(!step.view||v.id===step.view)&&step.nodes.every(id=>v.nodes.includes(id))&&step.edges.every(id=>v.edges.includes(id)));
    return {view:view.id,focus:step.focus||step.nodes[0],title:step.title,body:step.body,scenario:s.id};
  }));
  return {...source,maxRelations:20,views,tour,
    nodes:source.nodes.map(n=>({...n,fields:n.fields||[],methods:n.methods||[],home:{x:n.x,y:n.y}}))};
}
const DemoModel=typeof document==='undefined'?null:prepareClassModel(JSON.parse(document.getElementById('diagram-data').textContent));
if(typeof module!=='undefined')module.exports=prepareClassModel;
