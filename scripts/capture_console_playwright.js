const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const LOG_PATH = require('path').join(__dirname, 'playwright-console.log');
  const url = process.argv[2] || 'http://localhost:3001';
  const out = [];

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => {
    const text = `[console:${msg.type()}] ${msg.text()}`;
    out.push(text);
    console.log(text);
  });

  page.on('pageerror', err => {
    const text = `[pageerror] ${err.toString()}`;
    out.push(text);
    console.error(text);
  });

  page.on('requestfailed', req => {
    const text = `[requestfailed] ${req.url()} ${req.failure()?.errorText || ''}`;
    out.push(text);
    console.warn(text);
  });

  try {
    await page.goto(url, { waitUntil: 'networkidle' , timeout: 15000 });
    // Wait a bit for dynamic scripts and console activity
    await page.waitForTimeout(4000);

    // Try to open a persona page if available to exercise more code
    try {
      await page.goto(url + '/persona/1', { waitUntil: 'networkidle', timeout: 10000 });
      await page.waitForTimeout(3000);
    } catch (e) {
      out.push('[info] Could not open /persona/1 — that may be expected');
    }

  } catch (e) {
    out.push(`[navigation error] ${e.message}`);
    console.error(e);
  } finally {
    fs.writeFileSync(LOG_PATH, out.join('\n'));
    console.log('Saved logs to', LOG_PATH);
    await browser.close();
  }
})();
