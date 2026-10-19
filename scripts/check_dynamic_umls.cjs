/* Optional browser proof. Uses an existing Playwright installation; no downloads. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.DYNAMIC_UMLS_PLAYWRIGHT || 'playwright');
const checkExamples = require('./dynamic-uml-browser/examples.cjs');
const checkState = require('./dynamic-uml-browser/state.cjs');
const checkSubflows = require('./dynamic-uml-browser/subflows.cjs');
const checkSequence = require('./dynamic-uml-browser/sequence.cjs');
const checkZoom = require('./dynamic-uml-browser/zoom.cjs');
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
    await checkExamples({page, root, output, kinds});
    await checkState({page, root, output});
    await checkSubflows({page, root, output});
    await checkSequence({page, root, output});
    await checkZoom({page, root, output});
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
