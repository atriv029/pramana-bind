// Headless check of the standalone demo with the network disabled.
// usage: node test_demo.js FILE.html [screenshot_dir]
const { chromium } = require('playwright');
const assert = require('assert');

(async () => {
  const file = process.argv[2], shots = process.argv[3];
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1366, height: 768 }, offline: true });
  const p = await ctx.newPage();
  const errs = [], reqs = [];
  p.on('pageerror', e => errs.push(String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('request', r => { if (!r.url().startsWith('file:') && !r.url().startsWith('data:')) reqs.push(r.url()); });
  await p.goto('file://' + file);
  await p.waitForTimeout(300);

  // the browser's replay must equal the Python results stored with each case
  assert.deepStrictEqual(await p.evaluate(() => window.__selftest()), [], 'browser replay differs from the Python results');

  const txt = async s => (await p.textContent(s)).replace(/\s+/g, ' ').trim();
  const strip = x => x.trim().replace(/^\S\s*/, '');
  const parts = async () => (await p.$$eval('#a-parts .part .v', e => e.map(x => x.textContent))).map(strip);

  // A: initial state is the 323 case
  assert.strictEqual(await p.getAttribute('#a-323', 'aria-pressed'), 'true');
  assert.deepStrictEqual(await parts(), ['Supported', 'Contradicted']);
  assert.match(await txt('#a-agg'), /Contradicted/);
  assert.match(await p.innerHTML('#a-src'), /class="chg">323</);
  await p.click('#a-320');
  assert.deepStrictEqual(await parts(), ['Supported', 'Supported']);
  assert.match(await txt('#a-agg'), /Supported/);
  assert.match(await p.innerHTML('#a-src'), /class="chg">320</);
  await p.click('#a-323');
  assert.deepStrictEqual(await parts(), ['Supported', 'Contradicted']);
  assert.strictEqual(await p.isHidden('#a-compare'), true);
  await p.click('#a-bug');
  assert.strictEqual(await p.isVisible('#a-compare'), true);
  const cols = (await p.$$eval('#a-two .rule', e => e.map(r => [...r.querySelectorAll('.v')].map(x => x.textContent)))).map(c => c.map(strip));
  assert.deepStrictEqual(cols, [['Contradicted', 'Supported', 'Contradicted'], ['Supported', 'Contradicted', 'Contradicted']]);
  assert.match(await txt('#a-compare'), /5 of 754 verdicts but 153 part-level/);
  if (shots) await p.screenshot({ path: shots + '/demo_A.png' });
  await p.click('#a-bug');
  assert.strictEqual(await p.isHidden('#a-compare'), true);

  // B: both cases, both directions of the switch
  await p.click('#t1');
  assert.match(await txt('#b-verdict'), /Not established/);
  assert.match(await txt('#b-ref'), /SUPPORTS/);
  assert.match(await p.innerHTML('#b-src'), /class="q">known professionally as Pink</);
  await p.click('#b-enf');
  assert.match(await txt('#b-verdict'), /Supported/);
  assert.match(await txt('#b-explain'), /not the signed certificate/);
  await p.click('#b-enf');
  assert.match(await txt('#b-verdict'), /Not established/);
  await p.click('#b-c1');
  assert.match(await txt('#b-verdict'), /Not established/);
  assert.match(await txt('#b-ref'), /Incorrect/);
  await p.click('#b-enf');
  assert.match(await txt('#b-verdict'), /Supported/);
  assert.strictEqual(await txt('#b-s1'), '37');
  assert.strictEqual(await txt('#b-s2'), '6');
  assert.strictEqual(await txt('#b-n'), '43');
  if (shots) await p.screenshot({ path: shots + '/demo_B.png' });
  await p.click('#b-enf');
  await p.click('#b-c0');

  // C: genuine record passes; modified copy fails; switching back restores
  await p.click('#t2');
  await p.waitForTimeout(200);
  assert.match(await txt('#c-audit'), /Pass/);
  assert.match(await txt('#c-assign'), /Wrong part/);
  assert.match(await txt('#c-verdict'), /Contradicted/);
  assert.strictEqual((await p.$$('#c-live .ok')).length, 3, 'live checks on the genuine record should all pass');
  await p.click('#c-tamper');
  await p.waitForTimeout(200);
  assert.match(await txt('#c2-audit'), /Fail/);
  assert.ok((await p.$$('#c2-live .no')).length >= 2);
  assert.match(await txt('#c2-steps'), /hash chain/);
  if (shots) await p.screenshot({ path: shots + '/demo_C.png' });
  await p.click('#c-tamper');
  await p.waitForTimeout(200);
  assert.strictEqual((await p.$$('#c2-live .no')).length, 0);

  // keyboard: arrow keys move between tabs; space toggles a switch
  await p.focus('#t2');
  await p.keyboard.press('ArrowLeft');
  assert.strictEqual(await p.getAttribute('#t1', 'aria-selected'), 'true');
  await p.keyboard.press('ArrowLeft');
  assert.strictEqual(await p.getAttribute('#t0', 'aria-selected'), 'true');
  await p.focus('#a-bug');
  await p.keyboard.press('Space');
  assert.strictEqual(await p.getAttribute('#a-bug', 'aria-checked'), 'true');
  await p.keyboard.press('Space');

  // laptop: claim, source and overall verdict visible together without scrolling
  const fits = await p.evaluate(() => ['a-claim', 'a-src', 'a-agg'].every(id => {
    const r = document.getElementById(id).getBoundingClientRect();
    return r.top >= 0 && r.bottom <= innerHeight;
  }));

  // mobile
  const mctx = await b.newContext({ viewport: { width: 390, height: 844 }, offline: true });
  const m = await mctx.newPage();
  await m.goto('file://' + file);
  await m.waitForTimeout(200);
  const over = await m.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
  if (shots) await m.screenshot({ path: shots + '/demo_mobile.png' });

  console.log(JSON.stringify({ console_errors: errs, network_requests: reqs, selftest: 'pass',
    laptop_claim_source_verdict_visible: fits, mobile_horizontal_overflow: over }));
  assert.deepStrictEqual(errs, []);
  assert.deepStrictEqual(reqs, []);
  assert.strictEqual(over, false);
  await b.close();
})().catch(e => { console.error('DEMO TEST FAILED:', e.message); process.exit(1); });
