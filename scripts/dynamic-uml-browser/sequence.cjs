const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

module.exports = async function checkSequence({page, root, output}) {
  const canvasSizing=()=>page.locator('#canvas-scroll').evaluate(el=>({
    vertical:el.scrollHeight>el.clientHeight+1,horizontal:el.scrollWidth>el.clientWidth+1,top:el.scrollTop
  }));
  // Reproduce the owner's sequence scrollbar in a short window, then verify page auto-follow.
  await page.setViewportSize({width:1227,height:589});
  await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/sequence.html')).href);
  await page.evaluate(()=>window.scrollTo(0,80));
  assert.deepEqual(await canvasSizing(),{vertical:false,horizontal:false,top:0});
  await page.screenshot({path:path.join(output,'sequence-page-scroll-after.png')});
  await page.setViewportSize({width:1440,height:760});
  await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/sequence.html')).href);
  await page.locator('#step-track button').nth(4).click();
  const inViewport=()=>{
    const edge=document.querySelector('.edge.active').getBoundingClientRect();
    const frame=document.getElementById('canvas-scroll').getBoundingClientRect();
    const heads=document.querySelector('#participant-headings svg').getBoundingClientRect();
    return edge.top>=heads.bottom && edge.bottom<=Math.min(innerHeight,frame.bottom)
      && edge.left>=frame.left && edge.right<=frame.right
      && heads.top>=document.querySelector('.toolbar').getBoundingClientRect().bottom-1
      && document.getElementById('canvas-scroll').scrollTop===0;
  };
  assert(await page.evaluate(inViewport),'Step 5 must be visible below sticky participant headers');
  await page.screenshot({path:path.join(output,'sequence-after.png')});
  await page.locator('#info').click();
  await page.screenshot({path:path.join(output,'sequence-modal-after.png')});
  await page.keyboard.press('Escape');
  await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
  assert.equal(await page.locator('#play').textContent(),'Play ▷');
  await page.locator('#sidebar-toggle').click();
  await page.screenshot({path:path.join(output,'sequence-sidebar-after.png')});
  await page.locator('#sidebar-toggle').click();
  await page.locator('#reset').click();
  await page.evaluate(()=>{document.getElementById('pace').value='1';document.getElementById('pace').dispatchEvent(new Event('input'));});
  await page.locator('#play').click();
  await page.waitForFunction(()=>document.getElementById('counter').textContent.startsWith('05'),null,{timeout:6000});
  assert(await page.evaluate(inViewport),'Playback must bring the fifth message into the window');
  await page.locator('#info').click();
  const held=await page.locator('#counter').textContent();
  await page.waitForTimeout(1150);
  assert.equal(await page.locator('#counter').textContent(),held);
  await page.keyboard.press('Escape');
  await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
  assert.equal(await page.locator('#play').textContent(),'Pause Ⅱ');
  await page.waitForFunction(previous=>document.getElementById('counter').textContent!==previous,held,{timeout:2000});
  await page.locator('#play').click();
  // Preserve elapsed pacing rather than starting a new full interval on close.
  await page.locator('#reset').click();
  await page.evaluate(()=>{document.getElementById('pace').value='2';document.getElementById('pace').dispatchEvent(new Event('input'));});
  await page.locator('#play').click();
  await page.waitForTimeout(1200);
  await page.locator('#info').click();
  const pacedCounter=await page.locator('#counter').textContent();
  await page.waitForTimeout(350);
  await page.locator('#close-details').click();
  await page.waitForFunction(previous=>document.getElementById('counter').textContent!==previous,pacedCounter,{timeout:1500});
  await page.locator('#play').click();
  await page.setViewportSize({width:390,height:844});
  await page.locator('#step-track button').nth(4).click();
  assert(await page.evaluate(()=>{const e=document.querySelector('.edge.active').getBoundingClientRect(),f=document.getElementById('canvas-scroll').getBoundingClientRect(),h=document.querySelector('#participant-headings svg').getBoundingClientRect();return e.top>=h.bottom && e.bottom<=Math.min(innerHeight,f.bottom);}), 'Mobile message must be vertically visible');
  await page.screenshot({path:path.join(output,'sequence-mobile-after.png')});
  assert.deepEqual(await canvasSizing(),{vertical:false,horizontal:false,top:0});
  await page.locator('#overview').click();
  await page.locator('#canvas-scroll').evaluate(el=>el.scrollLeft=90);
  await page.waitForTimeout(100);
  const aligned=await page.locator('#participant-headings [data-node]').evaluateAll(nodes=>nodes.every(node=>{
    const model=JSON.parse(document.getElementById('diagram-data').textContent),n=model.nodes.find(n=>n.id===node.dataset.node);
    const matrix=document.getElementById('diagram').getScreenCTM(),shape=node.querySelector('.shape').getBoundingClientRect();
    return Math.abs(shape.x+shape.width/2-(matrix.a*n.x+matrix.e))<1;
  }));
  assert(aligned,'Participant headers must remain aligned after horizontal panning');
  assert.deepEqual(await canvasSizing(),{vertical:false,horizontal:true,top:0});
  console.log('Short-window regression: manual and playing step 5 visible; Escape resumes prior playback; headers retained.');
  // Long-sequence review: traverse every message on a multi-screen, six-participant page.
  const longUrl=pathToFileURL(path.join(root,'examples/dynamic-umls/sequence-long.html')).href;
  const visibleMessage=()=>{
    const edge=document.querySelector('.edge.active'),text=edge.getBoundingClientRect();
    const heads=document.querySelector('#participant-headings').getBoundingClientRect();
    const frame=document.getElementById('canvas-scroll'),bounds=frame.getBoundingClientRect();
    const font=edge.querySelector('text'),matrix=font.getScreenCTM();
    return text.top>=heads.bottom&&text.bottom<=innerHeight-1&&text.left>=bounds.left&&text.right<=bounds.right
      && heads.top>=document.querySelector('.toolbar').getBoundingClientRect().bottom-1
      && frame.scrollTop===0&&frame.scrollHeight<=frame.clientHeight+1&&frame.scrollWidth<=frame.clientWidth+1
      && [...document.querySelectorAll('#participant-headings [data-node]')].filter(n=>getComputedStyle(n).display!=='none').every(n=>{const r=n.getBoundingClientRect(),box=n.querySelector('.shape').getBBox();return r.left>=bounds.left&&r.right<=bounds.right&&[...n.querySelectorAll('text')].filter(t=>getComputedStyle(t).display!=='none').every(t=>{const b=t.getBBox();return b.x>=box.x-1&&b.x+b.width<=box.x+box.width+1&&b.y>=box.y-1&&b.y+b.height<=box.y+box.height+1;});})
      && parseFloat(getComputedStyle(font).fontSize)*Math.hypot(matrix.a,matrix.b)>=10-0.01;
  };
  for(const viewport of [{width:1271,height:658},{width:800,height:658},{width:390,height:844}]){
    await page.setViewportSize(viewport);await page.goto(longUrl);
    const longModel=JSON.parse(await page.locator('#diagram-data').textContent());
    assert.equal(longModel.edges.length,32);assert.equal(longModel.nodes.length,6);
    await page.locator('#reset').click();
    for(let i=0;i<32;i++){
      if(i)await page.locator('#next').click();
      assert(await page.evaluate(visibleMessage),`Long sequence step ${i+1}: active arrow, endpoints and headers must fit without horizontal scrolling at ${viewport.width}px`);
      if([0,15,31].includes(i)){
        await page.waitForTimeout(250);
        await page.screenshot({path:path.join(output,`sequence-long-${viewport.width}-step-${i+1}.png`)});
      }
    }
    await page.locator('#step-track button').nth(27).click();
    const shown=await page.locator('#participant-headings [data-node]:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.node));
    if(viewport.width===1271)assert.deepEqual(shown,longModel.nodes.map(n=>n.id),'Show all participants when they fit');
    else if(viewport.width===800){
      // Scrollbar gutters change the usable canvas width across browser/OS setups.
      // Assert density and neighboring-call context, not the identity of a filler.
      assert(shown.length>=4,'Fill available width instead of always hiding inactive participants');
      assert(['browser','app','store'].every(id=>shown.includes(id)),'Retain current and neighboring message endpoints');
    }else assert.deepEqual(shown,['app','store'],'Keep the active endpoints readable on a narrow phone');
    assert.deepEqual(shown,longModel.nodes.filter(n=>shown.includes(n.id)).map(n=>n.id),'Preserve participant order');
    const omitted=await page.locator('[data-omitted]').evaluateAll(nodes=>nodes.map(n=>n.dataset.omitted));
    const omittedGroups=[];
    for(const node of longModel.nodes){
      if(shown.includes(node.id))omittedGroups.push(null);
      else if(omittedGroups.at(-1))omittedGroups[omittedGroups.length-1]+=' '+node.id;
      else omittedGroups.push(node.id);
    }
    assert.deepEqual(omitted,omittedGroups.filter(Boolean),'Each ellipsis must describe its contiguous omitted participants');
    if(omitted.length)assert.match(await page.locator('[data-omitted]').filter({hasText:'…'}).first().getAttribute('aria-label'),/omitted participants/);
    assert.deepEqual(await page.locator('[data-edge]:visible').evaluateAll(edges=>edges.map(e=>e.dataset.edge)),longModel.edges.filter(e=>shown.includes(e.from)&&shown.includes(e.to)).map(e=>e.id),'Only messages between shown participants remain visible');
    await page.waitForTimeout(250);
    await page.screenshot({path:path.join(output,`sequence-density-${viewport.width}-after.png`)});
    // Both pointer and keyboard expansion restore the canonical complete diagram.
    for(const activation of ['click','keyboard']){
      const omission=page.locator('[data-omitted]').first();
      if(!omitted.length)await page.locator('#overview').click();
      else if(activation==='click')await omission.click();else{await omission.focus();await page.keyboard.press('Enter');}
      assert.equal(await page.locator('#overview').getAttribute('aria-pressed'),'true');
      assert.equal(await page.locator('[data-node]:visible').count(),6);
      assert.equal(await page.locator('[data-edge]:visible').count(),32);
      assert.equal(await page.locator('[data-omitted]').count(),0);
      assert(await page.locator('[data-lifeline]').evaluateAll(lines=>{const m=JSON.parse(document.getElementById('diagram-data').textContent);return lines.every(line=>Number(line.getAttribute('x1'))===m.nodes.find(n=>n.id===line.dataset.lifeline).x);}));
      assert((await canvasSizing()).horizontal);assert(await page.locator('.mobile-hint').isVisible());
      await page.locator('#overview').click();
      assert(await page.evaluate(visibleMessage),'Leaving Overview must restore the width-aware geometry');
    }
    await page.locator('#sidebar-toggle').click();
    assert(await page.evaluate(visibleMessage),'Sidebar must retain the whole active arrow and participant boxes');
    await page.locator('#sidebar-toggle').click();
    await page.locator('#step-track button').nth(31).click();
    assert(await page.evaluate(()=>scrollY>innerHeight*2),'Long sequence should exercise several screens of document scrolling');
    const finalY=await page.evaluate(()=>scrollY);
    await page.locator('#reset').click();assert(await page.evaluate(()=>scrollY)<finalY,'Reset must return to the beginning');
    await page.locator('#step-track button').nth(15).click();
    assert(await page.evaluate(visibleMessage),'Jumping to a middle step must restore its viewport');
    await page.evaluate(()=>{document.getElementById('pace').value='1';document.getElementById('pace').dispatchEvent(new Event('input'));});
    await page.locator('#play').click();await page.locator('#info').click();
    const heldLong=await page.locator('#counter').textContent();await page.waitForTimeout(1150);
    assert.equal(await page.locator('#counter').textContent(),heldLong);
    await page.keyboard.press('Escape');
    await page.waitForFunction(previous=>document.getElementById('counter').textContent!==previous,heldLong,{timeout:2000});
    assert(await page.evaluate(visibleMessage),'Long sequence playback must follow after closing details');
    await page.locator('#play').click();
    await page.locator('#step-track button').nth(30).click();await page.locator('#play').click();
    await page.waitForFunction(()=>document.getElementById('play').textContent==='Play ▷',null,{timeout:2000});
    assert(await page.evaluate(visibleMessage),'Final long-sequence playback message must be visible');
    await page.locator('footer').scrollIntoViewIfNeeded();
    const footerLogo=await page.locator('footer .brand-logo').evaluate(el=>({width:el.width,background:getComputedStyle(el).backgroundColor,opacity:getComputedStyle(el).opacity}));
    assert.equal(footerLogo.width,32);assert.equal(footerLogo.background,'rgba(0, 0, 0, 0)');assert.equal(footerLogo.opacity,'0.8');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.locator('footer').screenshot({path:path.join(output,`footer-${viewport.width}-after.png`)});
  }
  // Keep both surrounding messages visible when their four participants fit.
  await page.setViewportSize({width:800,height:658});await page.goto(longUrl);
  await page.locator('#step-track button').nth(4).click();
  assert.deepEqual(await page.locator('[data-node]:visible').evaluateAll(nodes=>nodes.map(n=>n.dataset.node)),['browser','app','queue','worker']);
  for(const id of ['message-04','message-05','message-06']){
    assert(await page.locator(`[data-edge="${id}"]`).isVisible(),`${id}: surrounding exchange hidden despite sufficient space`);
    assert(await page.locator(`[data-edge="${id}"]`).evaluate(el=>{const r=el.getBoundingClientRect(),h=document.getElementById('participant-headings').getBoundingClientRect();return r.top>=h.bottom&&r.bottom<=innerHeight;}),`${id}: surrounding arrow outside the actual window`);
  }
  await page.screenshot({path:path.join(output,'sequence-surrounding-calls-after.png')});
  for(const [width,count] of [[1271,6],[390,2],[800,4]]){
    await page.setViewportSize({width,height:844});
    await page.waitForFunction(expected=>[...document.querySelectorAll('[data-node]')].filter(n=>getComputedStyle(n).display!=='none').length===expected,count);
    assert(await page.evaluate(visibleMessage),'Resize must preserve active arrow fit and header alignment');
  }
  await page.setViewportSize({width:390,height:844});await page.locator('#sidebar-toggle').click();
  for(let i=0;i<32;i++){
    await page.locator('#step-track button').nth(i).click();
    assert(await page.evaluate(visibleMessage),`Mobile sidebar step ${i+1}: active arrow and readable participant names must fit`);
  }
  await page.locator('#sidebar-toggle').click();
  // Match the original footer baseline on the original sequence page.
  await page.setViewportSize({width:1250,height:673});
  await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/sequence.html')).href);
  await page.locator('footer').scrollIntoViewIfNeeded();
  await page.locator('footer').screenshot({path:path.join(output,'footer-after.png')});
  console.log('Long sequence: all 32 arrows and headers fit wide/medium/mobile views; width-aware participants, surrounding calls, resize, ellipses, Overview, mobile sidebar, playback and modal resume passed.');
};
