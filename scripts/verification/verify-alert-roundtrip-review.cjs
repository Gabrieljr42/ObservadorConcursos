const { chromium } = require('playwright');
const fs = require('fs');
const assert = require('assert/strict');

(async () => {
  const outDir = 'backend/.tenderproof/product-completion/app-sync';
  fs.mkdirSync(outDir, { recursive: true });
  const access = fs.readFileSync('backend/.tenderproof/local-pilot/ACESSO-LOCAL.md', 'utf8');
  const field = (key) => access.match(new RegExp(`${key}:\\s*([^\\r\\n]+)`))[1].trim(' `');
  const stamp = new Date().toISOString().replace(/[-:.]/g, '').replace('Z', 'Z');
  const name = `T006 review ${stamp}`;
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  const report = { started: new Date().toISOString(), name, errors: [], snapshots: [] };
  let token;
  page.on('pageerror', (e) => report.errors.push(e.message));
  const card = () => page.getByText(name, { exact: true }).locator('..').locator('..');
  const snapshot = async (label) => {
    if (await page.getByText(name, { exact: true }).count() === 0) {
      const body = await page.locator('body').innerText();
      report.snapshots.push({ label, textPresent: false, body: body.slice(-2500) });
      return { textPresent: false };
    }
    const value = await card().evaluate((el) => ({
      text: el.innerText,
      switches: [...el.querySelectorAll('[role="switch"],button,input[type="checkbox"]')].map((x) => ({
        role: x.getAttribute('role'), ariaChecked: x.getAttribute('aria-checked'), text: x.innerText,
      })),
    }));
    report.snapshots.push({ label, ...value });
    return value;
  };
  try {
    await page.goto('http://localhost:13000/login');
    await page.getByPlaceholder('E-mail', { exact: true }).fill(field('E-mail'));
    await page.getByPlaceholder('Senha', { exact: true }).fill(field('Senha'));
    const loginWait = page.waitForResponse((x) => x.url().endsWith('/auth/login'));
    const cpWait = page.waitForResponse((x) => x.url().endsWith('/sync/checkpoint'), { timeout: 60000 });
    await page.getByText('Entrar', { exact: true }).click();
    token = (await (await loginWait).json()).access_token;
    await cpWait; await page.waitForURL('**/inicio');
    await page.getByRole('tab', { name: /alertas/i }).click();
    await page.getByText('Novo Alerta', { exact: true }).click();
    await page.getByLabel('Nome do alerta', { exact: true }).fill(name);
    await page.getByLabel('Cargo ou palavra-chave', { exact: true }).fill(`review_${Date.now()}`);
    await context.setOffline(true);
    await page.getByText('Salvar alerta', { exact: true }).click();
    await page.getByText(name, { exact: true }).waitFor();
    await snapshot('created_offline');
    const sw = card().getByRole('switch');
    assert.equal(await sw.count(), 1);
    await sw.click();
    await snapshot('immediate_after_click');
    try { await sw.waitFor({ state: 'visible', timeout: 5000 }); } catch {}
    await page.waitForTimeout(1000);
    const delayed = await snapshot('after_1s');
    if (!delayed.textPresent) throw new Error('alert card disappeared after toggle');
    await sw.waitFor({ state: 'visible' });
    await expectAttribute(sw, 'aria-checked', 'false', 5000);
    report.disabled_offline = true;
    await context.setOffline(false);
    await page.goto('http://localhost:13000/notificacoes');
    const syncWait = page.waitForResponse((x) => x.url().endsWith('/sync/checkpoint'), { timeout: 60000 });
    await page.getByRole('button', { name: /Sincronizar tudo/i }).click();
    const synced = await (await syncWait).json();
    const server = synced.alerts.filter((x) => x.name === name);
    assert.equal(server.length, 1); assert.equal(server[0].active, false);
    report.server_disabled = true;
  } catch (e) { report.failure = e.message; }
  finally {
    await context.setOffline(false);
    if (token) {
      const headers = { Authorization: `Bearer ${token}` };
      const response = await context.request.get('http://localhost:13000/api/me/alerts', { headers });
      if (response.ok()) for (const alert of (await response.json()).filter((x) => x.name === name))
        await context.request.delete(`http://localhost:13000/api/me/alerts/${alert.id}`, { headers });
    }
    report.finished = new Date().toISOString();
    report.receipt = `${outDir}/alert-roundtrip-review-${stamp}.json`;
    fs.writeFileSync(report.receipt, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
    await browser.close();
  }
})();

async function expectAttribute(locator, name, expected, timeout) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await locator.getAttribute(name) === expected) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  assert.equal(await locator.getAttribute(name), expected);
}
