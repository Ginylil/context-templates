/* Catalog journeys called by the website's existing browser proof. */
const assert = require('node:assert/strict');
const path = require('node:path');
const {execFileSync} = require('node:child_process');

async function checkCatalog(page, {origin, root, output, size, noOverflow, checkLinks}) {
  const catalog = JSON.parse(execFileSync(process.env.PYTHON || 'python3',
    ['scripts/skills.py', 'list', '--json'], {cwd: root, encoding: 'utf8'}));
  await page.getByRole('link', {name: 'Browse the catalog'}).click();
  assert.equal(new URL(page.url()).pathname, '/catalog/');
  assert.equal(await page.locator('.catalog-card').count(), catalog.length);
  await noOverflow(page);
  await checkLinks(page);
  await page.screenshot({path: path.join(output, `catalog-${size.id}.png`)});
  await page.getByRole('searchbox', {name: 'Search skills'}).fill('ct-rnd-fix-bug');
  assert.equal(await page.locator('.catalog-card:visible').count(), 1);
  await page.getByRole('combobox', {name: 'Area of work'}).selectOption('Dynamic UMLs');
  assert.equal(await page.locator('.catalog-card:visible').count(), 0);
  assert.equal(await page.getByRole('heading', {name: 'No matching skills.'}).isVisible(), true);
  await page.getByRole('button', {name: 'Clear filters'}).click();
  assert.equal(await page.locator(':focus').getAttribute('id'), 'skill-search');
  assert.equal(await page.locator('.catalog-card:visible').count(), catalog.length);
  await page.getByRole('combobox', {name: 'Area of work'}).selectOption('Dynamic UMLs');
  assert.equal(await page.locator('.catalog-card:visible').count(), 7);
  await page.getByRole('button', {name: 'Clear filters'}).click();
  await page.getByRole('link', {name: 'Build an interface', exact: false}).click();
  assert.match(new URL(page.url()).pathname, /catalog\/ct-design-build-interface\/$/);
  await noOverflow(page);
  await checkLinks(page);
  for (const agent of ['codex', 'cursor', 'claude']) {
    await page.getByRole('combobox', {name: 'Your agent'}).selectOption(agent);
    assert.equal(await page.locator('[data-agent]:visible').count(), 1);
    const expected = `python3 scripts/skills.py install --agent ${agent} --skill ct-design-build-interface`;
    assert.equal(await page.locator(`#preview-${agent}`).textContent(), `${expected} --dry-run`);
    assert.equal(await page.locator(`#install-${agent}`).textContent(), expected);
    for (const action of ['preview', 'install']) {
      await page.locator(`[data-copy="${action}-${agent}"]`).click();
      const box = page.locator(`#${action}-${agent}`).locator('..');
      await page.waitForFunction(id => document.getElementById(id).parentElement
        .querySelector('[role="status"]').textContent.startsWith('Copied.'), `${action}-${agent}`);
      assert.equal(await page.evaluate(() => navigator.clipboard.readText()),
        await page.locator(`#${action}-${agent}`).textContent());
      assert.match(await box.locator('[role="status"]').textContent(), /^Copied\./);
    }
    await noOverflow(page);
  }
  await page.locator('#install-heading').scrollIntoViewIfNeeded();
  await page.screenshot({path: path.join(output, `installation-${size.id}.png`)});
  await page.goto(origin);
}

async function checkCatalogFallback(page, origin, noOverflow) {
  await page.goto(new URL('catalog/ct-rnd-fix-bug/', origin).href);
  await page.locator('[data-copy="install-codex"]').click();
  await page.waitForFunction(() => document.querySelector('#install-codex').parentElement
    .querySelector('[role="status"]').textContent.includes('copy it manually'));
  assert.equal(await page.evaluate(() => window.getSelection().toString()),
    await page.locator('#install-codex').textContent());
  assert.equal(await page.locator(':focus').getAttribute('id'), 'install-codex');
  await noOverflow(page);
}

async function checkCatalogNoScript(page, origin, noOverflow, checkLinks, root) {
  const catalog = JSON.parse(execFileSync(process.env.PYTHON || 'python3',
    ['scripts/skills.py', 'list', '--json'], {cwd: root, encoding: 'utf8'}));
  await page.goto(new URL('catalog/', origin).href);
  assert.equal(await page.locator('.catalog-card').count(), catalog.length);
  assert.equal(await page.locator('.catalog-filters').isVisible(), false);
  await checkLinks(page);
  await page.getByRole('link', {name: 'Build an interface'}).click();
  assert.equal(await page.locator('[data-agent]:visible').count(), 3);
  assert.equal(await page.locator('[data-copy]:visible').count(), 0);
  assert.equal(await page.locator('#install-agent').isVisible(), false);
  await noOverflow(page);
}

module.exports = {checkCatalog, checkCatalogFallback, checkCatalogNoScript};
