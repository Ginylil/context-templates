const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

module.exports = async function checkSubflows({page, root, output}) {
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
};
