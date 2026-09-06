// Actual browser interaction probe, using a caller-selected Playwright install.
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const shellDir = fs.readdirSync(process.env.PLAYWRIGHT_BROWSERS_PATH).find(p => p.startsWith('chromium_headless_shell-'));
  if (!shellDir) throw Error('Pinned headless browser missing');
  const executablePath = path.join(process.env.PLAYWRIGHT_BROWSERS_PATH, shellDir, 'chrome-headless-shell-win64', 'chrome-headless-shell.exe');
  const browser = await chromium.launch({headless: true, executablePath});
  try {
    const page = await browser.newPage();
    await page.setContent('<button id="key">K2</button><output id="count">0</output><script>document.querySelector("button").onclick=()=>document.querySelector("output").textContent=Number(document.querySelector("output").textContent)+1</script>');
    await page.locator('#key').click();
    if (await page.locator('#count').textContent() !== '1') throw Error('Browser click did not update fixture');
    const out = path.resolve(__dirname, '../../artifacts/c00');
    await page.screenshot({path: path.join(out, 'browser-fixture.png')});
    fs.writeFileSync(path.join(out, 'browser.json'), JSON.stringify({
      passed: true, browser: browser.version(), playwright: require(path.join(process.env.PLAYWRIGHT_MODULE || 'playwright', 'package.json')).version,
      executable: executablePath, platform: process.platform,
      assertion: 'Click K2 changes output from 0 to 1',
      scope: 'Browser infrastructure only; not emulator UI acceptance',
      timestamp: new Date().toISOString()
    }, null, 2) + '\n');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
