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
      assert.equal(await page.locator('.brand').getAttribute('href'), 'https://contexttemplates.com');
      assert.equal(await page.locator('#counter').textContent(), `01 / ${String(model.scenarios[0].steps.length).padStart(2,'0')}`);
      await page.locator('#next').click();
      assert.match(await page.locator('#counter').textContent(), /^02/);
      await page.locator('#prev').click();
      assert.match(await page.locator('#counter').textContent(), /^01/);
      await page.locator('[data-node]').first().click();
      assert.equal(await page.locator('#inspect-title').textContent(), model.nodes[0].label);
      await page.locator('[data-edge]').first().focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#inspect-title').textContent(), model.edges[0].label);
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
        await page.selectOption('#scenario', '1');
        assert.match(await page.locator('#counter').textContent(), /^01/);
        assert.equal(await page.locator('#step-title').textContent(), model.scenarios[1].steps[0].title);
      }
      await page.locator('#reset').click();
      assert.equal(await page.locator('#scenario').inputValue(), '0');
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
      if (kind === 'sequence') assert(await page.locator('#canvas-scroll').evaluate(el => el.scrollTop > 0));
      await page.locator('#play').click(); // Replay restarts from first step.
      assert.match(await page.locator('#counter').textContent(), /^01/);
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
      assert.equal(await page.locator('.node').first().evaluate(el => getComputedStyle(el).transitionDuration), '0s');
      await page.locator('#next').click();
      assert.match(await page.locator('#counter').textContent(), /^03/);
      await page.locator('[data-node]').first().focus();
      await page.keyboard.press('Space');
      assert.equal(await page.locator('#inspect-title').textContent(), model.nodes[0].label);
      await page.screenshot({path:path.join(output,`${kind}-mobile.png`), fullPage:true});
      await page.setViewportSize({width:1440,height:1000});
      await page.emulateMedia({reducedMotion:'no-preference'});
      console.log(`${kind}: offline playback, navigation, scenarios, inspector, keyboard, desktop/mobile, reduced motion passed`);
    }
    await page.goto(pathToFileURL(path.join(root,'examples/dynamic-umls/index.html')).href);
    assert.equal(await page.locator('.card').count(), 6);
    await page.screenshot({path:path.join(output,'gallery.png'),fullPage:true});
    assert.deepEqual(errors, [], 'Browser console or page errors');
    assert.deepEqual(network, [], 'Unexpected network requests');
    console.log(`Six examples verified without network requests. Proof: ${output}`);
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
