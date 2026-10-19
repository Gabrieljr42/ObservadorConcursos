const { chromium } = require('playwright');
const fs = require('fs');
(async()=>{
 const access=fs.readFileSync('backend/.tenderproof/local-pilot/ACESSO-LOCAL.md','utf8');
 const field=key=>access.match(new RegExp(key+':\\s*([^\\r\\n]+)'))[1].replace(/^[ `]+|[ `]+$/g,'');
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext(); const page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://localhost:13000/login');
 await page.getByPlaceholder('E-mail',{exact:true}).fill(field('E-mail'));
 await page.getByPlaceholder('Senha',{exact:true}).fill(field('Senha'));
 const checkpoint=page.waitForResponse(r=>r.url().endsWith('/sync/checkpoint'),{timeout:60000}).then(async r=>({status:r.status(),count:(await r.json()).concursos?.length})).catch(e=>({error:e.message}));
 await page.getByText('Entrar',{exact:true}).click();
 await page.waitForURL('**/inicio',{timeout:60000});
 const serverCheckpoint=await checkpoint;
 await page.waitForTimeout(1000);
 const first=await page.locator('body').innerText();
 const second=await context.newPage();second.on('pageerror',e=>errors.push(e.message));
 await second.goto('http://localhost:13000/salvos');
 await second.waitForTimeout(5000);
 const result={serverCheckpoint,first:first.slice(0,1800),second_url:second.url(),second_text:(await second.locator('body').innerText()).slice(0,1600),errors};
 await page.close();
 await second.getByRole('button',{name:'Tentar novamente',exact:true}).click();
 await second.waitForTimeout(5000);
 result.recovered_url=second.url();result.recovered_text=(await second.locator('body').innerText()).slice(0,2200);
 await context.setOffline(true);
 await second.getByRole('tab',{name:/início/i}).click();
 await second.waitForTimeout(1000);
 result.offline_home=(await second.locator('body').innerText()).slice(0,3400);
 await second.screenshot({path:'backend/.tenderproof/product-completion/app-sync/offline-home.png',fullPage:true});
 fs.mkdirSync('backend/.tenderproof/product-completion/app-sync',{recursive:true});
 fs.writeFileSync('backend/.tenderproof/product-completion/app-sync/first-sync-refresh.json',JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));await browser.close();
})().catch(e=>{console.error(e.message);process.exit(1)});



