const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

module.exports = async function checkZoom({page, root, output}) {
  await page.setViewportSize({width:1440,height:900});
  await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/class.html')).href);
  const state=()=>page.evaluate(()=>{
    const frame=document.getElementById('canvas-scroll'),svg=document.getElementById('diagram');
    return {width:svg.getBoundingClientRect().width,frame:frame.clientWidth,label:document.getElementById('zoom-level').textContent,
      focus:document.getElementById('zoom-focus').getAttribute('aria-pressed'),vertical:frame.scrollHeight>frame.clientHeight+1};
  });
  const activeVisible=()=>page.locator('.node.active').evaluateAll(nodes=>{
    const f=document.getElementById('canvas-scroll').getBoundingClientRect(),t=document.querySelector('.toolbar').getBoundingClientRect();
    return nodes.every(n=>{const b=n.getBoundingClientRect();return b.left>=f.left&&b.right<=f.right&&b.top>=t.bottom&&b.bottom<=innerHeight;});
  });
  const initial=await state();
  assert.equal(initial.focus,'true');
  assert(initial.width>initial.frame,'Focus framing enlarges the active class and its neighbors');
  assert(await activeVisible(),'Focused active class stays in view');
  assert.equal(initial.vertical,false,'Zoom must not add an inner vertical scrollport');
  await page.screenshot({path:path.join(output,'class-zoom-focus.png')});

  for (let i=1;i<await page.locator('#step-track button').count();i++){
    await page.locator('#next').click();
    assert(await activeVisible(),`Focus step ${i+1}: active elements stay in view`);
  }

  await page.locator('#zoom-fit').click();
  const fit=await state();
  assert.equal(fit.label,'100%');assert.equal(fit.focus,'false');
  assert(fit.width<=fit.frame+1,'Fit shows the whole diagram width');
  await page.locator('#zoom-in').click();
  const zoomed=await state();
  assert.equal(zoomed.label,'125%');assert(Math.abs(zoomed.width-fit.width*1.25)<2);assert.equal(zoomed.vertical,false);
  await page.locator('#zoom-out').click();await page.locator('#zoom-out').click();
  assert.equal((await state()).label,'80%');
  await page.locator('#prev').click();
  assert.equal((await state()).label,'80%','Manual zoom persists across steps');
  await page.evaluate(()=>document.activeElement.blur());
  await page.keyboard.press('0');
  assert.equal((await state()).label,'100%');
  await page.keyboard.press('+');
  assert.equal((await state()).label,'125%','Keyboard shortcuts zoom');
  for (let i=0;i<12;i++) await page.keyboard.press('+');
  assert.equal((await state()).label,'300%');assert.equal(await page.locator('#zoom-in').isDisabled(),true);
  await page.screenshot({path:path.join(output,'class-zoom-max.png')});

  await page.locator('#zoom-focus').click();
  assert.equal((await state()).focus,'true');assert(await activeVisible(),'Re-enabling Focus re-frames the step');
  await page.locator('#overview').click();
  assert.equal((await state()).label,'100%','Overview shows the whole diagram in focus mode');
  await page.locator('#overview').click();

  await page.setViewportSize({width:390,height:844});
  await page.locator('#reset').click();
  // Wider-than-canvas steps follow their destination, as without zoom.
  assert(await page.locator('.node.active').last().evaluate(n=>{const b=n.getBoundingClientRect(),f=document.getElementById('canvas-scroll').getBoundingClientRect();return b.left>=f.left&&b.right<=f.right;}),'Mobile focus keeps the destination class in view');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile page stays within viewport width');
  await page.screenshot({path:path.join(output,'class-zoom-mobile.png')});

  await page.setViewportSize({width:1440,height:900});
  await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/sequence.html')).href);
  assert.equal(await page.locator('#zoom-focus').isVisible(),false,'Sequence keeps its density layout without focus framing');
  assert.equal((await state()).label,'100%');
  await page.locator('#zoom-in').click();
  const head=await page.evaluate(()=>[document.querySelector('#participant-headings svg').getBoundingClientRect().width,document.getElementById('diagram').getBoundingClientRect().width]);
  assert(Math.abs(head[0]-head[1])<1,'Sequence headers scale with the zoomed lifelines');
  console.log('Zoom: focus framing, manual zoom, keyboard, Fit, Overview, mobile and sequence header sync passed.');
};
