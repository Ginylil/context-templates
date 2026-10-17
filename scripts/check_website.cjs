/* Optional local website proof; uses an existing Playwright and browser. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require(process.env.WEBSITE_PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname, '..');
const output = path.resolve(process.env.WEBSITE_PROOF || path.join(root, 'dist/website-proof'));
const origin = process.env.WEBSITE_URL || 'http://127.0.0.1:8766/';
const sizes = [
  {id: 'mobile', width: 390, height: 844},
  {id: 'desktop', width: 1440, height: 1000},
];

async function noOverflow(page) {
  assert.equal(await page.evaluate(() =>
    document.documentElement.scrollWidth <= window.innerWidth), true, 'Horizontal page overflow');
}

async function checkLinks(page) {
  for (const href of await page.locator('a[href]').evaluateAll(links => links.map(link => link.href))) {
    const url = new URL(href);
    if (url.origin !== new URL(origin).origin) continue;
    const response = await page.request.get(url.href);
    assert.equal(response.status(), 200, `Local link failed: ${url.pathname}`);
  }
}

(async () => {
  await fs.mkdir(output, {recursive: true});
  const browser = await chromium.launch({headless: true,
    ...(process.env.WEBSITE_CHROME ? {executablePath: process.env.WEBSITE_CHROME} : {})});
  const errors = [], external = [];
  try {
    for (const size of sizes) {
      const context = await browser.newContext({viewport: {width: size.width, height: size.height},
        deviceScaleFactor: 1, reducedMotion: 'reduce', permissions: ['clipboard-read', 'clipboard-write']});
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {if (message.type() === 'error') errors.push(message.text());});
      page.on('request', request => {
        if (new URL(request.url()).origin !== new URL(origin).origin) external.push(request.url());
      });
      await page.goto(origin);
      await noOverflow(page);
      await page.keyboard.press('Tab');
      assert.equal(await page.locator(':focus').textContent(), 'Skip to content');
      await page.keyboard.press('Enter');
      assert.equal(new URL(page.url()).hash, '#main');
      await page.getByRole('link', {name: 'Find your first skill'}).click();
      assert.equal(new URL(page.url()).hash, '#start');
      await page.getByRole('button', {name: 'Copy prompt'}).click();
      await page.waitForFunction(() => document.querySelector('#copy-status').textContent.startsWith('Copied.'));
      assert.match(await page.locator('#copy-status').textContent(), /^Copied\./);
      const prompt = await page.locator('#install-prompt').textContent();
      assert.equal(await page.evaluate(() => navigator.clipboard.readText()), prompt);
      const readme = await fs.readFile(path.join(root, 'README.md'), 'utf8');
      assert.equal(prompt, readme.match(/```text\n([\s\S]*?)\n```/)[1], 'Prompt differs from README');
      await checkLinks(page);
      await page.getByRole('link', {name: 'Try a live example'}).click();
      assert.match(new URL(page.url()).pathname, /examples\/dynamic-umls\/sequence.html$/);
      await page.goBack();
      await page.getByRole('link', {name: 'Read the build journal'}).click();
      assert.match(await page.title(), /Building with our own skills/);
      await noOverflow(page);
      await checkLinks(page);
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({path: path.join(output, `journal-${size.id}.png`), fullPage: false});
      await page.getByRole('link', {name: 'Back to the website'}).click();
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({path: path.join(output, `website-${size.id}.png`), fullPage: false});
      await page.screenshot({path: path.join(output, `website-${size.id}-full.png`), fullPage: true});
      await context.close();
    }
    const denied = await browser.newContext({viewport: {width: 390, height: 844}});
    await denied.addInitScript(() => Object.defineProperty(navigator, 'clipboard', {
      value: {writeText: () => Promise.reject(new Error('Clipboard unavailable in this check'))},
    }));
    const fallback = await denied.newPage();
    await fallback.goto(origin);
    await fallback.getByRole('button', {name: 'Copy prompt'}).click();
    await fallback.waitForFunction(() => document.querySelector('#copy-status').textContent.includes('copy it manually'));
    assert.match(await fallback.locator('#copy-status').textContent(), /copy it manually/);
    assert.equal(await fallback.evaluate(() => window.getSelection().toString()),
      await fallback.locator('#install-prompt').textContent());
    assert.equal(await fallback.locator(':focus').getAttribute('id'), 'install-prompt');
    await noOverflow(fallback);
    await denied.close();
    const plain = await browser.newContext({javaScriptEnabled: false, viewport: {width: 390, height: 844}});
    const noScript = await plain.newPage();
    await noScript.goto(origin);
    assert.equal(await noScript.locator('#copy-prompt').isVisible(), false);
    assert.match(await noScript.locator('#install-prompt').textContent(), /Install all skills/);
    await noOverflow(noScript);
    await checkLinks(noScript);
    await plain.close();
    assert.deepEqual(errors, [], 'Browser console or page errors');
    assert.deepEqual(external, [], 'Third-party resource requests');
    console.log('PASS: desktop/mobile layout, keyboard, clipboard, denied fallback, no-JS, local links; no browser errors or external resources.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
