const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');

module.exports=async function checkCompatibility(context,output) {
  const html=await fs.readFile(path.join(output,'class-camera-demo.html'),'utf8');
  const marker=/<script id="diagram-data" type="application\/json">([\s\S]*?)<\/script>/;
  const original=JSON.parse(html.match(marker)[1]);
  const page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const model={...original,title:'An invoice and its account',nodes:[
    {id:'invoice',kind:'class',label:'An invoice with a deliberately long class name',detail:'All members remain available.',
      x:250,y:260,fields:['+ id: UUID','+ status: InvoiceState','+ total: Money'],methods:['+ collect(): void']},
    {id:'account',kind:'class',label:'Account',detail:'No members were supplied.',x:700,y:260}],
    edges:['association','composition','aggregation','inheritance','dependency'].map(kind=>({
      id:kind,kind,from:'invoice',to:'account',label:kind,detail:`The supplied ${kind} explanation.`,targetMultiplicity:'0..*'})),
    scenarios:['first','second'].map((id,i)=>({id,label:`Explanation ${i+1}`,steps:[{
      title:`Explain ${i+1}`,body:'A legacy single-view model without explicit focus.',
      nodes:i?['account','invoice']:['invoice','account'],edges:[]}]}))};
  delete model.views;
  const data=JSON.stringify(model).replaceAll('<','\\u003c');
  await page.setContent(html.replace(marker,()=>`<script id="diagram-data" type="application/json">${data}</script>`));
  await page.waitForFunction(()=>typeof CC!=='undefined'&&!CC.animating);
  assert.equal(await page.evaluate(()=>CC.focus),'invoice','No dependency on demo class IDs');
  assert.equal(await page.evaluate(()=>CC.view.id),'structure','Legacy model gets a complete default view');
  assert(await page.locator('#scenario-picker').isVisible());
  assert.equal(await page.locator('[data-edge="aggregation"] .stroke').getAttribute('marker-start'),'url(#hollow)');
  assert.equal(await page.locator('[data-edge="inheritance"] .stroke').getAttribute('marker-end'),'url(#triangle)');
  assert.equal(await page.locator('[data-edge="dependency"] .stroke').getAttribute('stroke-dasharray'),'6 5');
  assert.equal(await page.locator('[data-edge="dependency"] .stroke').getAttribute('marker-end'),'url(#open)');
  await page.locator('#inspect-class').click();
  for(const member of [...model.nodes[0].fields,...model.nodes[0].methods])assert((await page.locator('#details-list').innerText()).includes(member));
  await page.keyboard.press('Escape');
  await page.evaluate(()=>CC.edgeEls.get('association').dispatchEvent(new MouseEvent('click',{bubbles:true})));
  assert((await page.locator('#details-list').innerText()).includes('Account: 0..*'),'Target-only cardinality remains accessible');
  await page.keyboard.press('Escape');
  await page.locator('#scenario').selectOption('second');await page.waitForFunction(()=>!CC.animating);
  assert.equal(await page.evaluate(()=>CC.focus),'account');
  assert.equal(await page.locator('#story-title').innerText(),'Explain 2');
  assert((await page.locator('[data-node="account"] .member').first().textContent()).includes('No listed attributes'));
  await page.setViewportSize({width:390,height:844});await page.waitForFunction(()=>CC.metrics.mobile&&!CC.animating);
  const fits=await page.locator('[data-node="invoice"]').evaluate(g=>{
    const r=g.querySelector('rect').getBoundingClientRect();
    return [...g.querySelectorAll('text')].every(t=>{const b=t.getBoundingClientRect();return b.left>=r.left-1&&b.right<=r.right+1;});
  });
  assert(fits,'Long arbitrary class/member text stays inside mobile cards');
  assert.equal(await page.locator('#legend li').count(),model.legend.length);
  assert.deepEqual(errors,[]);await page.close();
};
