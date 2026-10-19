const {chromium}=require('playwright');const fs=require('fs');const assert=require('assert/strict');
(async()=>{
 const root='backend/.tenderproof/product-completion/app-sync';
 const access=fs.readFileSync('backend/.tenderproof/local-pilot/ACESSO-LOCAL.md','utf8');const field=k=>access.match(new RegExp(k+':\\s*([^\\r\\n]+)'))[1].replace(/^[ `]+|[ `]+$/g,'');
 const browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext();const page=await context.newPage();
 const name='Verificação offline '+Date.now();const report={name,errors:[]};let token;
 page.on('pageerror',e=>report.errors.push(e.message));
 async function synchronize(){await page.goto('http://localhost:13000/notificacoes');const response=page.waitForResponse(r=>r.url().endsWith('/sync/checkpoint'),{timeout:60000});await page.getByRole('button',{name:/Sincronizar tudo/i}).click();const data=await (await response).json();await page.waitForURL('**/inicio');return data;}
 const card=()=>page.getByText(name,{exact:true}).locator('..').locator('..');
 try{
 await page.goto('http://localhost:13000/login');await page.getByPlaceholder('E-mail',{exact:true}).fill(field('E-mail'));await page.getByPlaceholder('Senha',{exact:true}).fill(field('Senha'));
 const login=page.waitForResponse(r=>r.url().endsWith('/auth/login'));const first=page.waitForResponse(r=>r.url().endsWith('/sync/checkpoint'),{timeout:60000});
 await page.getByText('Entrar',{exact:true}).click();token=(await (await login).json()).access_token;await first;await page.waitForURL('**/inicio');
 await page.getByRole('tab',{name:/alertas/i}).click();await page.getByText('Novo Alerta',{exact:true}).waitFor();await context.setOffline(true);
 await page.getByText('Novo Alerta',{exact:true}).click();await page.getByLabel('Nome do alerta',{exact:true}).fill(name);await page.getByLabel('Cargo ou palavra-chave',{exact:true}).fill('verificacao_sem_correspondencia_'+Date.now());
 await page.getByText('Salvar alerta',{exact:true}).click();await page.getByText(name,{exact:true}).waitFor();report.created_offline=true;
 await card().getByRole('switch').click();report.disabled_offline=true;
 await context.setOffline(false);const created=await synchronize();const alerts=created.alerts.filter(a=>a.name===name);assert.equal(alerts.length,1);assert.equal(alerts[0].active,false);report.server_created_once=true;report.server_disabled=true;
 await page.goto('http://localhost:13000/alertas');await page.getByText(name,{exact:true}).waitFor();assert.equal(await card().getByRole('switch').getAttribute('aria-checked'),'false');report.reopened=true;
 await context.setOffline(true);await card().getByText('Excluir',{exact:true}).click();await page.getByText(name,{exact:true}).waitFor({state:'hidden'});report.deleted_offline=true;
 await context.setOffline(false);const deleted=await synchronize();assert.ok(!deleted.alerts.some(a=>a.name===name));report.server_deleted=true;
 }catch(e){report.failure=e.message;throw e;}
 finally{
  await context.setOffline(false);
  if(token){const headers={Authorization:'Bearer '+token};const r=await context.request.get('http://localhost:13000/api/me/alerts',{headers});if(r.ok()){const leftovers=(await r.json()).filter(a=>a.name===name);for(const a of leftovers)await context.request.delete('http://localhost:13000/api/me/alerts/'+a.id,{headers});report.cleanup_removed=leftovers.length;}}
  fs.writeFileSync(root+'/alert-roundtrip.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));await browser.close();
 }
})().catch(e=>{console.error(e.message);process.exitCode=1});
