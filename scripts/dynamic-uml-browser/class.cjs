const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');

module.exports=async function checkClass({page,root,output}) {
  await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/class.html')).href);
  await page.waitForFunction(()=>!CC.animating);
  assert.equal(await page.locator('#title').innerText(),await page.title());
  for(const link of await page.locator('.brand').all())assert.equal(await link.getAttribute('href'),'https://contexttemplates.com/index.html');
  for(const logo of await page.locator('.brand img').all())assert(await logo.evaluate(el=>el.complete&&el.naturalWidth>0));
  await page.locator('#next').click();await page.waitForFunction(()=>!CC.animating);
  assert.equal(await page.evaluate(()=>CC.focus),'product');
  await page.locator('#zoom-out').click();assert.equal(await page.evaluate(()=>CC.mode),'explore');
  await page.locator('#resume').click();assert.equal(await page.evaluate(()=>CC.playing),true);
  await page.locator('#play').click();await page.waitForFunction(()=>!CC.animating);
  await page.locator('#inspect-class').click();assert(await page.locator('#details').isVisible());
  await page.keyboard.press('Escape');
  await page.screenshot({path:path.join(output,'class-desktop.png')});
  await page.setViewportSize({width:390,height:844});await page.locator('#follow').click();
  await page.waitForFunction(()=>!CC.animating);assert.deepEqual(await page.evaluate(()=>[CC.metrics.cols,CC.metrics.rows]),[3,5]);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(output,'class-mobile.png'),fullPage:true});
  await page.setViewportSize({width:1440,height:1000});
};
