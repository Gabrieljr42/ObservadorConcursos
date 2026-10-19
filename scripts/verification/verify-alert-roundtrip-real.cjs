const {chromium}=require('playwright');
const fs=require('fs');
const assert=require('assert/strict');

(async()=>{
 const root='backend/.tenderproof/product-completion/app-sync';fs.mkdirSync(root,{recursive:true});
 const access=fs.readFileSync('backend/.tenderproof/local-pilot/ACESSO-LOCAL.md','utf8');
 const field=k=>access.match(new RegExp(k+':\\s*([^\\r\\n]+)'))[1].replace(/^[ `]+|[ `]+$/g,'');
 const stamp=new Date().toISOString().replace(/[-:.]/g,'').replace('Z','Z');
 const name='T006 offline '+stamp;
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext();const page=await context.newPage();
 const report={started:new Date().toISOString(),name,errors:[],network:[]};let token;
 page.on('response',async r=>{if(/\/auth\/login$/.test(r.url())) report.network.push({url:r.url(),status:r.status(),contentType:r.headers()['content-type']||null});});
 page.on('pageerror',e=>report.errors.push(e.message));
 const card=()=>page.getByText(name,{exact:true}).locator('..').locator('..');
 const inspect=async()=>card().evaluate(el=>({
   text:el.innerText,
   html:el.outerHTML,
   switches:[...el.querySelectorAll('[role="switch"],button,input[type="checkbox"]')].map(x=>({
     tag:x.tagName,role:x.getAttribute('role'),ariaChecked:x.getAttribute('aria-checked'),
     dataState:x.getAttribute('data-state'),checked:x.checked===true,
     text:x.innerText||x.getAttribute('aria-label')||''
   }))
 }));
 async function sync(){
   await page.goto('http://localhost:13000/notificacoes');
   const response=page.waitForResponse(r=>r.url().endsWith('/sync/checkpoint'),{timeout:60000});
   await page.getByRole('button',{name:/Sincronizar tudo/i}).click();
   const data=await (await response).json();await page.waitForURL('**/inicio');return data;
 }
 try{
   await page.goto('http://localhost:13000/login');
   const initialBody=await page.locator('body').innerText();
   if(/Dados salvos indisponíveis/i.test(initialBody)) { report.blocked_storage=true; report.initial_body=initialBody; throw new Error('storage unavailable before login'); }
   await page.getByPlaceholder('E-mail',{exact:true}).fill(field('E-mail'));await page.getByPlaceholder('Senha',{exact:true}).fill(field('Senha'));
   const login=page.waitForResponse(r=>r.url().endsWith('/auth/login'));const first=page.waitForResponse(r=>r.url().endsWith('/sync/checkpoint'),{timeout:60000});
   await page.getByText('Entrar',{exact:true}).click();
   const loginResponse=await login;const loginType=loginResponse.headers()['content-type']||'';
   if(!loginType.includes('json')) throw new Error(`login non-json response ${loginResponse.status()} ${loginResponse.url()} ${loginType}`);
   token=(await loginResponse.json()).access_token;await first;await page.waitForURL('**/inicio');
   await page.getByRole('tab',{name:/alertas/i}).click();await page.getByText('Novo Alerta',{exact:true}).click();
   await page.getByLabel('Nome do alerta',{exact:true}).fill(name);await page.getByLabel('Cargo ou palavra-chave',{exact:true}).fill('t006_sem_correspondencia_'+Date.now());
   await context.setOffline(true);await page.getByText('Salvar alerta',{exact:true}).click();await page.getByText(name,{exact:true}).waitFor();report.created_offline=true;
   report.dom_after_create=await inspect();
   const sw=card().getByRole('switch');assert.equal(await sw.count(),1,'alert switch absent');
   await sw.click();report.disabled_offline=true;report.dom_after_disable=await inspect();
   await context.setOffline(false);const synced=await sync();const server=synced.alerts.filter(a=>a.name===name);assert.equal(server.length,1);assert.equal(server[0].active,false);report.server_created_once=true;report.server_disabled=true;
   await page.goto('http://localhost:13000/alertas');await page.getByText(name,{exact:true}).waitFor();report.dom_after_reopen=await inspect();report.reopened=true;
   assert.match((report.dom_after_reopen.text||'').toLowerCase(),/desativ|inativ|off|ativar/,'no visible inactive state in DOM');
   await context.setOffline(true);await card().getByText('Excluir',{exact:true}).click();await page.getByText(name,{exact:true}).waitFor({state:'hidden'});report.deleted_offline=true;
   await context.setOffline(false);const deleted=await sync();assert.ok(!deleted.alerts.some(a=>a.name===name));report.server_deleted=true;
 }catch(e){report.failure=e.message}
 finally{
   await context.setOffline(false);
   if(token){const headers={Authorization:'Bearer '+token};const r=await context.request.get('http://localhost:13000/api/me/alerts',{headers});if(r.ok()){for(const a of (await r.json()).filter(a=>a.name===name)){await context.request.delete('http://localhost:13000/api/me/alerts/'+a.id,{headers})}}}
   report.finished=new Date().toISOString();const out=root+'/alert-roundtrip-real-'+stamp+'.json';fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(JSON.stringify({...report,receipt:out}));await browser.close();
 }
})().catch(e=>{console.error(e.message);process.exitCode=1});
