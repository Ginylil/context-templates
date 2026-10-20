const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {execFileSync} = require('node:child_process');
const {chromium} = require(process.env.CLASS_CAMERA_PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname,'..'),output=path.join(root,'dist/class-camera-proof');
const url=pathToFileURL(path.join(output,'class-camera-demo.html')).href;
const errors=[],proof={sourceRevision:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),viewports:[],checks:[]};
let browser,page;
const settled=()=>page.waitForFunction(()=>!CC.animating&&Object.keys(CC.routes).length===CC.view.edges.length);
const state=()=>page.evaluate(()=>({camera:{...CC.camera},playing:CC.playing,mode:CC.mode,focus:CC.focus,
  step:CC.step,view:CC.view.id,grid:[CC.metrics.cols,CC.metrics.rows],neighbors:[...CC.neighbors],animating:CC.animating}));
async function focusVisible() {
  return page.evaluate(()=>{
    const frame=stage.getBoundingClientRect(),current=document.querySelector('.node.current rect').getBoundingClientRect();
    const visible=[...document.querySelectorAll('.node:not(.offstage)')];
    return {centered:Math.abs((current.left+current.right-frame.left-frame.right)/2)<2&&
      Math.abs((current.top+current.bottom-frame.top-frame.bottom)/2)<2,
      count:visible.length,expected:CC.neighbors.length+1,
      inside:visible.every(n=>{const b=n.querySelector('rect').getBoundingClientRect();
        return b.left>=frame.left+2&&b.right<=frame.right-2&&b.top>=frame.top+2&&b.bottom<=frame.bottom-2;}),
      textInside:visible.every(n=>{const r=n.querySelector('rect').getBoundingClientRect();
        return [...n.querySelectorAll('text')].every(t=>{const b=t.getBoundingClientRect();return b.left>=r.left-1&&b.right<=r.right+1&&b.top>=r.top-1&&b.bottom<=r.bottom+1;});})};
  });
}
async function verifyFocus(label) {
  await settled();const result=await focusVisible();
  assert(result.centered,`${label}: focus is centered`);assert(result.inside,`${label}: every direct neighbor fits`);
  assert(result.textInside,`${label}: class text stays inside its card`);assert.equal(result.count,result.expected);
  const cleanLabels=await page.evaluate(()=>{
    const cards=[...document.querySelectorAll('.node:not(.offstage) rect')].map(n=>n.getBoundingClientRect());
    return [...document.querySelectorAll('.edge:not(.offstage) text')].every(t=>{
      const b=t.getBoundingClientRect();if(!b.width||!b.height)return true;
      return cards.every(r=>b.right<=r.left||b.left>=r.right||b.bottom<=r.top||b.top>=r.bottom);
    });
  });
  assert(cleanLabels,`${label}: relationship and cardinality labels stay outside class cards`);
}
async function stagePoint(x=.5,y=.5) {
  const box=await page.locator('#stage').boundingBox();return {x:box.x+box.width*x,y:box.y+box.height*y};
}
async function run() {
  await fs.mkdir(output,{recursive:true});browser=await chromium.launch();
  const context=await browser.newContext({viewport:{width:1440,height:900},offline:true});
  page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.goto(url);await verifyFocus('Desktop initial');
  assert.equal((await state()).playing,false,'Playback is opt-in');
  await page.screenshot({path:path.join(output,'desktop-focus.png')});
  proof.viewports.push({viewport:'desktop',...(await state())});

  const initial=await state();await page.locator('#next').click();await page.waitForTimeout(180);
  const traveling=await state();assert(traveling.animating,'Camera moves between classes');
  assert(Math.hypot(traveling.camera.x-initial.camera.x,traveling.camera.y-initial.camera.y)>1);
  await verifyFocus('Desktop product');
  const distances=await page.evaluate(()=>{
    const node=nodesById.get(CC.focus),neighbor=CC.neighbors.find(id=>Math.hypot(nodesById.get(id).home.x-node.home.x,nodesById.get(id).home.y-node.home.y)>700);
    const home=nodesById.get(neighbor).home,p=CC.positions[neighbor],c=CC.positions[CC.focus];
    return {before:Math.hypot(home.x-node.home.x,home.y-node.home.y),after:Math.hypot(p.x-c.x,p.y-c.y)};
  });
  assert(distances.after<distances.before,'Far direct relations come closer temporarily');

  // A plain mouse wheel takes control, pauses playback and keeps its world anchor.
  await page.locator('#play').click();await settled();
  const point=await stagePoint(.43,.48);await page.mouse.move(point.x,point.y);
  const beforeWheel=await page.evaluate(p=>{
    const r=stage.getBoundingClientRect();return {x:CC.camera.x+(p.x-r.left-r.width/2)/CC.camera.k,
      y:CC.camera.y+(p.y-r.top-r.height/2)/CC.camera.k,k:CC.camera.k};
  },point);
  await page.mouse.wheel(0,120);await page.waitForTimeout(100);
  const wheel=await state();assert.equal(wheel.playing,false);assert.equal(wheel.mode,'explore');assert(wheel.camera.k<beforeWheel.k);
  const afterWheel=await page.evaluate(p=>{
    const r=stage.getBoundingClientRect();return {x:CC.camera.x+(p.x-r.left-r.width/2)/CC.camera.k,
      y:CC.camera.y+(p.y-r.top-r.height/2)/CC.camera.k};
  },point);
  assert(Math.hypot(afterWheel.x-beforeWheel.x,afterWheel.y-beforeWheel.y)<1,'Zoom remains pointer-anchored');
  await page.mouse.down();await page.mouse.move(point.x+90,point.y+45,{steps:8});await page.mouse.up();
  const dragged=await state();assert(Math.abs(dragged.camera.x-wheel.camera.x)>20,'Mouse drag pans');
  assert.equal(dragged.playing,false);await page.screenshot({path:path.join(output,'desktop-explore.png')});

  await page.locator('#wheel-mode').selectOption('pan');const beforePan=await state();
  await page.mouse.wheel(35,65);await page.waitForTimeout(80);const pan=await state();
  assert.equal(pan.camera.k,beforePan.camera.k,'Trackpad scrolling pans without changing scale');
  assert(Math.abs(pan.camera.y-beforePan.camera.y)>10);
  await page.locator('#stage').dispatchEvent('wheel',{deltaY:-30,deltaMode:0,ctrlKey:true,clientX:point.x,clientY:point.y});
  assert((await state()).camera.k>pan.camera.k,'Trackpad pinch zooms in pan mode');
  proof.checks.push('mouse wheel anchor, playback takeover, drag pan, explicit trackpad pan and pinch');

  await page.locator('#follow').click();await verifyFocus('Restore focus');
  const neighbor=await page.evaluate(()=>CC.neighbors[0]);
  await page.locator(`[data-node="${neighbor}"] rect`).click();await settled();
  assert.equal((await state()).focus,neighbor,'Clicking a class focuses it');await verifyFocus('Selected class');
  await page.locator('#steps button').nth(0).click();await settled();
  await page.locator('#linked').click();await verifyFocus('Linked view');
  assert.equal((await state()).view,'fulfilment');assert.equal((await state()).focus,'order');
  assert.match(await page.locator('#relations').innerText(),/27 relationships across 3 diagrams/);
  await page.locator('#linked').click();await verifyFocus('Second linked view');assert.equal((await state()).view,'settlement');

  // Pause during travel: layout can settle, but must not replace manual camera input.
  await page.locator('#steps button').nth(4).click();
  await page.locator('#play').click();await page.waitForTimeout(150);
  const mid=await stagePoint(.5,.5);await page.mouse.move(mid.x,mid.y);await page.mouse.wheel(0,55);
  const taken=await state();await page.waitForTimeout(350);const retained=await state();
  assert.equal(retained.playing,false);assert.equal(retained.mode,'explore');
  assert.deepEqual(retained.camera,taken.camera,'A settling layout cannot overwrite manual camera control');
  await page.locator('#resume').click();await settled();assert.equal((await state()).playing,true);
  await page.locator('#play').click();assert.equal((await state()).playing,false);
  await page.locator('#info').click();assert(await page.locator('#details').isVisible());
  await page.keyboard.press('Escape');assert.equal(await page.locator('#details').isVisible(),false);
  proof.checks.push('class selection, linked diagrams, manual takeover during animation, explicit resume and accessible details');

  for(const [width,height,grid,name]of [[390,844,[3,5],'mobile-portrait'],[844,390,[5,3],'mobile-landscape']]) {
    await page.setViewportSize({width,height});await page.locator('#steps button').nth(0).click();
    await verifyFocus(name);assert.deepEqual((await state()).grid,grid);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No page horizontal overflow');
    await page.screenshot({path:path.join(output,`${name}.png`),fullPage:true});
    proof.viewports.push({viewport:name,...(await state())});
  }
  await page.setViewportSize({width:1440,height:900});await page.emulateMedia({reducedMotion:'reduce'});
  for(let i=0;i<8;i++) {
    await page.locator('#steps button').nth(i).click();assert.equal((await state()).animating,false,'Reduced motion jumps without animation');
    await verifyFocus(`Reduced-motion step ${i+1}`);
  }
  await page.locator('#stage').focus();const keyBefore=await state();await page.keyboard.press('ArrowRight');
  assert((await state()).camera.x>keyBefore.camera.x);assert.equal((await state()).mode,'explore');
  await page.keyboard.press('f');await verifyFocus('Keyboard Focus');
  proof.checks.push('all tour steps, responsive orientations, keyboard alternatives and reduced motion');

  // Chromium's touch input path generates real browser pointer events.
  const touch=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,offline:true});
  const touchPage=await touch.newPage();page=touchPage;page.on('pageerror',error=>errors.push(error.message));
  await page.goto(url);await settled();const client=await touch.newCDPSession(page),p=await stagePoint(.5,.45);
  await page.locator('#play').click();await settled();const touchBefore=await state();
  const points=(dx,dy,spread)=>[{x:p.x-40-spread+dx,y:p.y+dy,id:1},{x:p.x+40+spread+dx,y:p.y+dy,id:2}];
  await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:points(0,0,0)});
  await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:points(25,20,0)});
  await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  const touchPan=await state();assert.equal(touchPan.playing,false);assert.equal(touchPan.mode,'explore');
  assert(Math.hypot(touchPan.camera.x-touchBefore.camera.x,touchPan.camera.y-touchBefore.camera.y)>10,'Two fingers pan');
  await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:points(0,0,0)});
  await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:points(0,0,30)});
  await client.send('Input.dispatchTouchEvent',{type:'touchCancel',touchPoints:[]});
  assert((await state()).camera.k>touchPan.camera.k*1.3,'Two-finger pinch scales the diagram');
  assert.equal(await page.evaluate(()=>pointers.size),0,'Cancellation releases gesture state');
  await page.locator('#follow').click();await verifyFocus('Touch recovery');
  proof.checks.push('emulated two-finger pan, pinch, cancellation and focus recovery');
  await touch.close();assert.deepEqual(errors,[],'No browser runtime errors');await context.close();

  // A real browser recording shows camera travel and manual exploration.
  const recording=await browser.newContext({viewport:{width:1440,height:900},offline:true,
    recordVideo:{dir:output,size:{width:1440,height:900}}});
  page=await recording.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.goto(url);await settled();await page.locator('#play').click();
  await page.waitForTimeout(9800);const location=await stagePoint(.48,.53);
  await page.mouse.move(location.x,location.y);await page.mouse.wheel(0,180);await page.waitForTimeout(500);
  await page.mouse.down();await page.mouse.move(location.x+180,location.y+30,{steps:24});await page.mouse.up();await page.waitForTimeout(1200);
  await page.locator('#steps button').nth(3).click();await settled();await page.locator('#play').click();
  await page.waitForTimeout(5400);await page.locator('#map').click();await settled();await page.waitForTimeout(1200);
  const video=page.video();await recording.close();await video.saveAs(path.join(output,'camera-walkthrough.webm'));
  await fs.unlink(await video.path());
  assert.deepEqual(errors,[],'The recorded walkthrough has no runtime errors');
  proof.errors=errors;proof.limitations=['Chromium emulates mobile input; physical-device and Safari acceptance remain unverified.'];
  await fs.writeFile(path.join(output,'browser-proof.json'),JSON.stringify(proof,null,2)+'\n');
  console.log('Class camera: desktop/mobile layout, tour, relationships, mouse/touch gestures, takeover, resume and recording passed.');
}
run().catch(async error=>{
  proof.failure=error.stack;proof.errors=errors;
  await fs.writeFile(path.join(output,'browser-proof.json'),JSON.stringify(proof,null,2)+'\n');
  if(page&&!page.isClosed())await page.screenshot({path:path.join(output,'failure.png'),fullPage:true}).catch(()=>{});
  console.error(error);process.exitCode=1;
}).finally(async()=>{if(browser)await browser.close();});
