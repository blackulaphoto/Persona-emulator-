const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const appChunksDir = path.join(__dirname, '..', '.next', 'static', 'chunks', 'app');
  if (!fs.existsSync(appChunksDir)) {
    console.error('app chunks dir not found:', appChunksDir);
    process.exit(1);
  }

  // Find a layout JS file (dev uses layout.js, prod uses layout-<hash>.js)
  const files = fs.readdirSync(appChunksDir).filter(f => /^layout(\.|-).+\.js$/.test(f));
  if (files.length === 0) {
    console.error('No layout bundle found in', appChunksDir);
    process.exit(1);
  }
  const bundlePath = path.join(appChunksDir, files[0]);

  const tmpHtml = path.join(__dirname, 'tmp_layout_test.html');
  // Create an HTML file that loads the bundle via a file:/// URL
  const fileUrl = 'file:///' + bundlePath.replace(/\\/g, '/').replace(/ /g, '%20');
  const html = `<!doctype html><html><head><meta charset="utf-8"></head><body>
  <h1>Local bundle test</h1>
  <script src="${fileUrl}"></script>
  </body></html>`;
  fs.writeFileSync(tmpHtml, html, 'utf8');

  const logs = [];
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => {
    const text = `[console:${msg.type()}] ${msg.text()}`;
    logs.push(text);
    console.log(text);
  });
  page.on('pageerror', err => {
    const text = `[pageerror] ${err.toString()}`;
    logs.push(text);
    console.error(text);
  });

  try {
    await page.goto('file:///' + tmpHtml.replace(/\\/g, '/').replace(/ /g, '%20'));
    await page.waitForTimeout(2000);
  } catch (e) {
    logs.push('[navigation error] ' + e.message);
    console.error(e);
  } finally {
    const outPath = path.join(__dirname, 'playwright-local-bundle.log');
    fs.writeFileSync(outPath, logs.join('\n'));
    console.log('Saved', outPath);
    await browser.close();
  }
})();
