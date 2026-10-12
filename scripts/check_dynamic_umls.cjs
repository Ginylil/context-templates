/* Optional browser proof. Uses an existing Playwright installation; no downloads. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.DYNAMIC_UMLS_PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname, '..');
const kinds = ['sequence', 'class', 'flowchart', 'state', 'activity', 'component'];
const output = path.resolve(process.env.DYNAMIC_UMLS_PROOF || path.join(root, 'dist/dynamic-umls-proof'));

(async () => {
  await fs.mkdir(output, {recursive: true});
  const browser = await chromium.launch({headless: true,
    ...(process.env.DYNAMIC_UMLS_CHROME ? {executablePath: process.env.DYNAMIC_UMLS_CHROME} : {})});
  try {
    const context = await browser.newContext({viewport: {width:1440, height:1000}});
    await context.setOffline(true);
    const page = await context.newPage();
    const errors = [], network = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {if (message.type() === 'error') errors.push(message.text());});
    page.on('request', request => {if (/^https?:/.test(request.url())) network.push(request.url());});
    for (const kind of kinds) {
      await page.goto(pathToFileURL(path.join(root, `examples/dynamic-umls/${kind}.html`)).href);
      const model = await page.locator('#diagram-data').textContent().then(JSON.parse);
      assert.equal(await page.title(), model.title);
      assert(await page.locator('#canvas-scroll').evaluate(el=>el.scrollHeight<=el.clientHeight+1&&el.scrollTop===0),`${kind}: diagram must use document vertical scrolling`);
      assert.equal(await page.locator('.brand').getAttribute('href'), 'https://contexttemplates.com');
      assert.equal(await page.locator('footer a').getAttribute('href'),'https://contexttemplates.com');
      assert.equal(await page.locator('footer .brand-logo').getAttribute('src'),await page.locator('header .brand-logo').getAttribute('src'));
      assert.equal(await page.locator('footer .brand-logo').evaluate(el=>el.complete&&el.naturalWidth>0),true);
      assert.equal(await page.locator('#counter').textContent(), `01 / ${String(model.scenarios[0].steps.length).padStart(2,'0')}`);
      await page.locator('#next').click();
      assert.match(await page.locator('#counter').textContent(), /^02/);
      await page.locator('#prev').click();
      assert.match(await page.locator('#counter').textContent(), /^01/);
      assert.equal(await page.locator('#details-sidebar').isVisible(), false);
      const fullWidth=await page.locator('#canvas-scroll').evaluate(el=>el.clientWidth);
      await page.locator('#sidebar-toggle').click();
      assert.equal(await page.locator('#details-sidebar').isVisible(), true);
      assert(await page.locator('#canvas-scroll').evaluate(el=>el.clientWidth) < fullWidth-200);
      assert(await page.locator('#canvas-scroll').evaluate(el=>el.scrollHeight<=el.clientHeight+1),`${kind}: sidebar introduced inner vertical scrolling`);
      await page.locator('#info').click();
      await page.locator('#close-details').click();
      await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
      assert.equal(await page.locator('#details-panel').evaluate(el=>el.parentElement.id),'details-sidebar');
      await page.locator('#sidebar-toggle').click();
      await page.locator('[data-node]').first().click();
      assert.equal(await page.locator('#details-modal').isVisible(), true);
      assert.equal(await page.locator('#inspect-title').textContent(), model.nodes[0].label);
      await page.locator('#close-details').click();
      await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
      assert.equal(await page.locator('#play').textContent(), 'Play ▷');
      await page.locator('[data-edge]').first().focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#inspect-title').textContent(), model.edges[0].label);
      await page.keyboard.press('Escape');
      await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
      assert.equal(await page.locator('[data-edge]').first().evaluate(el=>el===document.activeElement),true);
      await page.locator('#reset').click();
      await page.evaluate(() => document.activeElement.blur());
      await page.keyboard.press('ArrowRight');
      assert.match(await page.locator('#counter').textContent(), /^02/);
      await page.keyboard.press('ArrowLeft');
      assert.match(await page.locator('#counter').textContent(), /^01/);
      await page.locator('#step-track button').nth(1).focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#step-track button').nth(1).evaluate(el => el === document.activeElement), true);
      assert.equal(await page.locator('#step-track button').nth(1).getAttribute('aria-current'), 'true');
      if (model.scenarios.length > 1) {
        await page.locator('#scenario').click();
        await page.locator('#scenario-menu [role=option]').nth(1).click();
        assert.match(await page.locator('#counter').textContent(), /^01/);
        assert.equal(await page.locator('#step-title').textContent(), model.scenarios[1].steps[0].title);
      }
      // Repo-owned picker opens below the trigger, with keyboard selection and dismissal.
      await page.locator('#scenario').focus();
      await page.keyboard.press('ArrowDown');
      const trigger=await page.locator('#scenario').boundingBox(), menu=await page.locator('#scenario-menu').boundingBox();
      assert(menu.y>=trigger.y+trigger.height && menu.x>=0 && menu.x+menu.width<=1440);
      assert.equal(await page.locator('#scenario').getAttribute('aria-expanded'),'true');
      await page.keyboard.press('End');
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#scenario-value').textContent(),model.scenarios.at(-1).label);
      await page.locator('#scenario').click();await page.keyboard.press('Escape');
      assert.equal(await page.locator('#scenario').evaluate(el=>el===document.activeElement),true);
      assert.equal(await page.locator('#scenario-menu').isVisible(),false);
      await page.locator('#scenario').click();await page.locator('#overview').click();
      assert.equal(await page.locator('#scenario-menu').isVisible(),false);
      await page.locator('#reset').click();
      assert.equal(await page.locator('#scenario').evaluate(el=>el.value), '0');
      await page.locator('#overview').click();
      assert.equal(await page.locator('#overview').getAttribute('aria-pressed'), 'true');
      assert.equal(await page.locator('.dim').count(), 0);
      await page.locator('#reset').click();
      await page.evaluate(() => {document.getElementById('pace').value='1';document.getElementById('pace').dispatchEvent(new Event('input'));});
      const penultimate = model.scenarios[0].steps.length - 2;
      await page.locator('#step-track button').nth(penultimate).click();
      await page.locator('#play').click();
      await page.waitForFunction(() => document.getElementById('play').textContent === 'Play ▷', null, {timeout:3000});
      assert.equal(await page.locator('#next').isDisabled(), true);
      if (kind === 'sequence') {
        assert(await page.evaluate(()=>scrollY>0));
        assert.equal(await page.locator('#canvas-scroll').evaluate(el=>el.scrollTop),0);
        assert(await page.locator('.edge.active').evaluate(el=>{const b=el.getBoundingClientRect(),f=document.getElementById('canvas-scroll').getBoundingClientRect();return b.top>=f.top && b.bottom<=Math.min(innerHeight,f.bottom);}), 'Active message must be visible in the window');
      }
      await page.locator('#play').click(); // Replay restarts from first step.
      assert.match(await page.locator('#counter').textContent(), /^01/);
      await page.locator('#info').click();
      const pausedCounter=await page.locator('#counter').textContent();
      assert.equal(await page.locator('#play').textContent(),'Play ▷');
      await page.waitForTimeout(1150);
      assert.equal(await page.locator('#counter').textContent(),pausedCounter);
      await page.screenshot({path:path.join(output,`${kind}-modal.png`)});
      await page.locator('#close-details').click();
      await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
      assert.equal(await page.locator('#play').textContent(),'Pause Ⅱ');
      await page.waitForFunction(previous=>document.getElementById('counter').textContent!==previous,pausedCounter,{timeout:2000});
      await page.locator('#play').click();
      assert.equal(await page.locator('#play').getAttribute('aria-label'), 'Play walkthrough');
      await page.locator('#reset').click();
      await page.locator('#step-track button').nth(Math.min(1,model.scenarios[0].steps.length-1)).click();
      const overflowingText = await page.locator('[data-node]').evaluateAll(nodes => nodes.flatMap(n => {
        const shape = n.querySelector('.shape');
        if (!shape) return [];
        const box = shape.getBBox();
        return [...n.querySelectorAll('text')].filter(t => {
          const b=t.getBBox(); return b.x < box.x-1 || b.x+b.width > box.x+box.width+1;
        }).map(t => t.textContent);
      }));
      assert.deepEqual(overflowingText, [], `${kind}: overflowing node text`);
      await page.screenshot({path:path.join(output,`${kind}-desktop.png`), fullPage:true});
      await page.setViewportSize({width:390,height:844});
      await page.emulateMedia({reducedMotion:'reduce'});
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${kind}: page overflow`);
      assert(await page.locator('#canvas-scroll').evaluate(el=>el.scrollHeight<=el.clientHeight+1&&el.scrollTop===0),`${kind}: mobile introduced inner vertical scrolling`);
      assert.equal(await page.locator('.node').first().evaluate(el => getComputedStyle(el).transitionDuration), '0s');
      await page.locator('#next').click();
      assert.match(await page.locator('#counter').textContent(), /^03/);
      const mobileNode=page.locator('[data-node]:visible').first();
      const mobileNodeId=await mobileNode.getAttribute('data-node');
      await mobileNode.focus();
      await page.keyboard.press('Space');
      assert.equal(await page.locator('#inspect-title').textContent(),model.nodes.find(n=>n.id===mobileNodeId).label);
      assert.equal(await page.locator('#details-modal').isVisible(),true);
      const modalBox=await page.locator('#details-modal').boundingBox();
      assert(modalBox.x>=0&&modalBox.y>=0&&modalBox.x+modalBox.width<=390&&modalBox.y+modalBox.height<=844);
      await page.screenshot({path:path.join(output,`${kind}-mobile-modal.png`)});
      await page.keyboard.press('Escape');
      await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
      await page.screenshot({path:path.join(output,`${kind}-mobile.png`), fullPage:true});
      await page.setViewportSize({width:1440,height:1000});
      await page.emulateMedia({reducedMotion:'no-preference'});
      console.log(`${kind}: offline playback, navigation, scenarios, inspector, keyboard, desktop/mobile, reduced motion passed`);
    }
    // Match the owner's short, wide window: state diagrams must not need two canvas scroll axes.
    await page.setViewportSize({width:1250,height:673});
    await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/state.html')).href);
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
    // Composition: drill into a bounded child, then recover the parent's scenario/step.
    await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/flowchart.html')).href);
    await page.locator('#scenario').click();await page.locator('#scenario-menu [role=option]').nth(1).click();
    await page.locator('#step-track button').nth(1).click();
    const parentCounter=await page.locator('#counter').textContent();
    await page.locator('[data-node=repair]').focus();await page.keyboard.press('Enter');
    await page.locator('#open-subflow').click();
    await page.waitForFunction(()=>document.getElementById('info').getAttribute('aria-expanded')==='false');
    assert.equal(await page.locator('#title').textContent(),'Repair the failure');
    assert.equal(await page.locator('[data-node]').count(),4);
    assert.equal(await page.locator('#play').textContent(),'Play ▷');
    assert.equal(await page.locator('#flow-back').evaluate(el=>el===document.activeElement),true);
    await page.locator('#next').click();assert.match(await page.locator('#counter').textContent(),/^02/);
    assert(await page.locator('.node.active').evaluateAll(nodes=>{const f=document.getElementById('canvas-scroll').getBoundingClientRect();return nodes.every(n=>{const b=n.getBoundingClientRect();return b.top>=f.top&&b.bottom<=Math.min(innerHeight,f.bottom);});}),'Subprocess active nodes must fit in the viewport');
    await page.screenshot({path:path.join(output,'flowchart-subprocess-after.png'),fullPage:true});
    await page.locator('#flow-back').click();
    assert.equal(await page.locator('#title').textContent(),'Is this change ready?');
    assert.equal(await page.locator('#counter').textContent(),parentCounter);
    assert.equal(await page.locator('#scenario-value').textContent(),'A check fails');
    assert.equal(await page.locator('[data-node=repair]').evaluate(el=>el===document.activeElement),true);
    await page.locator('#overview').click();
    // Match the baseline viewport, then a taller canvas capture for route inspection.
    await page.setViewportSize({width:1440,height:960});
    await page.locator('#reset').click();await page.locator('#overview').click();
    await page.screenshot({path:path.join(output,'flowchart-layout-after.png'),fullPage:true});
    await page.locator('#scenario').click();
    await page.screenshot({path:path.join(output,'scenario-after.png')});
    await page.keyboard.press('Escape');
    await page.setViewportSize({width:1000,height:1400});
    await page.waitForTimeout(100);
    await page.screenshot({path:path.join(output,'flowchart-routes-after.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.locator('#scenario').click();
    const mobileMenu=await page.locator('#scenario-menu').boundingBox(), mobileTrigger=await page.locator('#scenario').boundingBox();
    assert(mobileMenu.y>=mobileTrigger.y+mobileTrigger.height && mobileMenu.x+mobileMenu.width<=390 && mobileMenu.y+mobileMenu.height<=844);
    await page.screenshot({path:path.join(output,'scenario-mobile-after.png')});
    await page.keyboard.press('Escape');
    console.log('Themed picker below trigger and nested subprocess return verified.');
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
    await page.setViewportSize({width:1440,height:1000});
    await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/index.html')).href);
    assert.equal(await page.locator('.card').count(), 6);
    assert.equal(await page.locator('a[href="sequence-long.html"]').count(),1);
    await page.screenshot({path:path.join(output,'gallery.png'),fullPage:true});
    assert.deepEqual(errors, [], 'Browser console or page errors');
    assert.deepEqual(network, [], 'Unexpected network requests');
    console.log(`Seven examples verified without network requests. Proof: ${output}`);
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
