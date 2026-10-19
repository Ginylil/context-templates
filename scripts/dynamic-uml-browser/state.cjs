const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const fs = require('node:fs/promises');

module.exports = async function checkState({page, root, output}) {
  // Match the owner's short, wide window: state diagrams must not need two canvas scroll axes.
  await page.setViewportSize({width:1250,height:673});
  await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/state.html')).href);
  // Focus framing zooms in by default; Fit is the whole-diagram width contract.
  await page.locator('#zoom-fit').click();
  const canvasSizing=()=>page.locator('#canvas-scroll').evaluate(el=>({
    vertical:el.scrollHeight>el.clientHeight+1,horizontal:el.scrollWidth>el.clientWidth+1,top:el.scrollTop
  }));
  assert.deepEqual(await canvasSizing(),{vertical:false,horizontal:false,top:0});
  const branding=await page.locator('header .brand-logo').evaluate(el=>({
    width:el.getBoundingClientRect().width,background:getComputedStyle(el).backgroundColor,opacity:Number(getComputedStyle(el).opacity)
  }));
  assert.equal(branding.width,40);assert.equal(branding.background,'rgba(0, 0, 0, 0)');assert(branding.opacity<1);
  await page.screenshot({path:path.join(output,'state-scroll-after.png')});
  await page.screenshot({path:path.join(output,'state-page-scroll-after.png'),fullPage:true});
  const destinationVisible=()=>page.locator('.node.active').last().evaluate(el=>{
    const b=el.getBoundingClientRect(),frame=document.getElementById('canvas-scroll').getBoundingClientRect();
    const toolbar=document.querySelector('.toolbar').getBoundingClientRect();
    return b.top>=toolbar.bottom&&b.bottom<=innerHeight&&b.left>=frame.left&&b.right<=frame.right;
  });
  await page.locator('#scenario').click();await page.locator('#scenario-menu [role=option]').nth(1).click();
  await page.locator('#next').click();
  assert(await destinationVisible(),'Cancellation destination must be visible below sticky controls');
  assert(await page.evaluate(()=>scrollY>0),'State playback follows the page vertically');
  assert.equal((await canvasSizing()).vertical,false);
  await page.locator('#sidebar-toggle').click();
  assert.equal((await canvasSizing()).vertical,false,'Sidebar must not introduce a second canvas scroll axis');
  await page.locator('#sidebar-toggle').click();
  await page.setViewportSize({width:390,height:844});
  await page.locator('#reset').click();
  assert.deepEqual(await canvasSizing(),{vertical:false,horizontal:true,top:0});
  await page.locator('#next').click();
  assert(await destinationVisible(),'Narrow state view must pan to the transition destination');
  assert.equal((await canvasSizing()).vertical,false);
  await page.setViewportSize({width:1440,height:1000});
  console.log('State viewport: no inner vertical scroll, desktop width fits, mobile horizontal panning and page auto-follow passed.');
  // A transition label must sit on a real arrow segment, with room for its text.
  await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/state.html')).href);
  await page.locator('#overview').click();
  const labelChecks=await page.locator('[data-edge]').evaluateAll(edges=>edges.map(edge=>{
    const path=edge.querySelector('path.visible'), label=edge.querySelector('.transition-label'), text=label.querySelector('text');
    const center=label.transform.baseVal.consolidate().matrix;
    let distance=Infinity;
    for(let i=0;i<=path.getTotalLength();i+=0.25){const p=path.getPointAtLength(i);distance=Math.min(distance,Math.hypot(p.x-center.e,p.y-center.f));}
    const backing=label.querySelector('rect').getBBox(), width=text.getComputedTextLength();
    const points=[...path.getAttribute('d').matchAll(/[ML]([\d.e+-]+) ([\d.e+-]+)/g)].map(m=>({x:Number(m[1]),y:Number(m[2])}));
    const segment=Number(label.dataset.labelSegment), a=points[segment], b=points[segment+1];
    const room=Math.min(Math.hypot(center.e-a.x,center.f-a.y),Math.hypot(center.e-b.x,center.f-b.y));
    return {id:edge.dataset.edge,distance,fits:width+16<=backing.width+0.1&&room>=width/2+20};
  }));
  assert(labelChecks.every(c=>c.distance<0.5&&c.fits),JSON.stringify(labelChecks));
  await page.setViewportSize({width:1440,height:960});
  await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(250);
  await page.screenshot({path:path.join(output,'state-layout-after.png'),fullPage:true});
  await page.locator('#scenario').click();await page.locator('#scenario-menu [role=option]').nth(1).click();
  await page.locator('#step-track button').nth(1).click();await page.waitForTimeout(250);
  await page.screenshot({path:path.join(output,'state-cancel-after.png')});
  await page.setViewportSize({width:390,height:844});
  const mobileLabels=await page.locator('.transition-label text').evaluateAll(labels=>labels.map(t=>{
    const matrix=t.getScreenCTM();return parseFloat(getComputedStyle(t).fontSize)*Math.hypot(matrix.a,matrix.b);
  }));
  assert(mobileLabels.every(size=>size>=10),'State labels must not shrink to tiny mobile text');
  await page.setViewportSize({width:1440,height:1000});
  console.log('State transitions: label centers lie on arrows and mobile labels retain readable sizing.');
  // Exercise state drill-down and rotated labels using an explicit offline fixture.
  const statePage=await fs.readFile(path.join(root,'examples/dynamic-umls/state.html'),'utf8');
  const rootState=JSON.parse(await page.locator('#diagram-data').textContent());
  const detail={...rootState,id:'draft-detail',title:'State detail fixture',width:420,height:650,orientation:'vertical',
    nodes:[{id:'waiting',kind:'state',label:'Waiting',detail:'Illustrative fixture state.',x:180,y:150,w:140},
      {id:'working',kind:'state',label:'Working',detail:'Illustrative fixture state.',x:180,y:410,w:140}],
    edges:[{id:'start',kind:'transition',from:'waiting',to:'working',label:'start',detail:'Fixture transition.',fromPort:'bottom',toPort:'top',route:'forward',labelOn:{segment:0}},
      {id:'retry',kind:'transition',from:'working',to:'waiting',label:'retry',detail:'Fixture return.',fromPort:'left',toPort:'left',route:'loop',via:[{x:40,y:410},{x:40,y:150}],labelOn:{segment:1}}],
    scenarios:[{id:'start',label:'Begin work',steps:[{title:'Wait',body:'Waiting for the event.',nodes:['waiting'],edges:[]},{title:'Begin',body:'The event changes the state.',nodes:['waiting','working'],edges:['start']}]}]};
  rootState.nodes.find(n=>n.id==='draft').subflow='draft-detail';rootState.subflows=[detail];
  const fixture=path.join(output,'state-detail-fixture.html');
  await fs.writeFile(fixture,statePage.replace(/(<script id="diagram-data" type="application\/json">).*?(<\/script>)/s,(_,a,b)=>a+JSON.stringify(rootState)+b));
  await page.goto(pathToFileURL(fixture).href);
  await page.evaluate(()=>window.scrollTo(0,80));
  const parentPageScroll=await page.evaluate(()=>scrollY);
  await page.locator('[data-node=draft]').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#open-subflow').textContent(),'Explore state detail ↓');
  await page.locator('#open-subflow').click();
  await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
  assert.equal(await page.locator('#title').textContent(),detail.title);
  assert.equal(await page.locator('.transition-label').first().evaluate(el=>Math.abs(el.transform.baseVal.consolidate().matrix.b)),1);
  await page.locator('#next').click();assert.match(await page.locator('#counter').textContent(),/^02/);
  await page.locator('#flow-back').click();
  assert.equal(await page.locator('#title').textContent(),rootState.title);
  assert.equal(await page.locator('[data-node=draft]').evaluate(el=>el===document.activeElement),true);
  assert.equal(await page.evaluate(()=>scrollY),parentPageScroll,'Back must restore the parent page scroll');
};
