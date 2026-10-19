const {chromium}=require('playwright');const fs=require('fs');const assert=require('assert/strict');
(async()=>{
 const root='backend/.tenderproof/product-completion/app-sync';fs.mkdirSync(root,{recursive:true});
 const access=fs.readFileSync('backend/.tenderproof/local-pilot/ACESSO-LOCAL.md','utf8');
 const field=k=>access.match(new RegExp(k+':\\s*([^\\r\\n]+)'))[1].replace(/^[ `]+|[ `]+$/g,'');
 const browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext();
 const report={started:new Date().toISOString(),errors:[]};let token,target;
 const page=await context.newPage();page.on('pageerror',e=>report.errors.push(e.message));
 try{
 await page.goto('http://localhost:13000/login');
 await page.getByPlaceholder('E-mail',{exact:true}).fill(field('E-mail'));await page.getByPlaceholder('Senha',{exact:true}).fill(field('Senha'));
 const login=page.waitForResponse(r=>r.url().endsWith('/auth/login'));
 const first=page.waitForResponse(r=>r.url().endsWith('/sync/checkpoint'),{timeout:60000});
 await page.getByText('Entrar',{exact:true}).click();token=(await (await login).json()).access_token;
 const checkpoint=await (await first).json();await page.waitForURL('**/inicio');
 target=checkpoint.concursos.find(c=>!checkpoint.favorites.some(f=>f.concurso_id===c.id));assert.ok(target,'needs an initially unsaved contest');
 report.concurso_id=target.id;report.initially_saved=false;
 await page.getByText(target.titulo,{exact:true}).last().click();await page.getByText('SALVAR',{exact:true}).waitFor();
 await context.setOffline(true);
 await page.getByText('SALVAR',{exact:true}).click();await page.getByText('SALVO',{exact:true}).waitFor();
 report.offline_saved=true;await page.screenshot({path:root+'/favorite-offline.png',fullPage:true});
 await context.setOffline(false);
 await page.goto('http://localhost:13000/notificacoes');
 const sent=page.waitForResponse(r=>r.url().endsWith('/me/favorites/'+target.id)&&r.request().method()==='POST',{timeout:60000});
 const applied=page.waitForResponse(r=>r.url().endsWith('/sync/checkpoint'),{timeout:60000});
 await page.getByRole('button',{name:/Sincronizar tudo/i}).click();
 report.send_status=(await sent).status();const next=await (await applied).json();
 assert.ok(next.favorites.some(f=>f.concurso_id===target.id));report.server_confirmed=true;
 await page.waitForURL('**/inicio');await page.goto('http://localhost:13000/salvos');
 await page.getByText(target.titulo,{exact:true}).waitFor();report.reopened_saved=true;
 await page.screenshot({path:root+'/favorite-reopened.png',fullPage:true});
 await page.getByText(target.titulo,{exact:true}).click();await page.getByText('SALVO',{exact:true}).click();
 await page.goto('http://localhost:13000/notificacoes');
 const removed=page.waitForResponse(r=>r.url().endsWith('/me/favorites/'+target.id)&&r.request().method()==='DELETE',{timeout:60000});
 await page.getByRole('button',{name:/Sincronizar tudo/i}).click();report.remove_status=(await removed).status();
 await page.waitForURL('**/inicio');
 const check=await context.request.get('http://localhost:13000/api/me/favorites',{headers:{Authorization:'Bearer '+token}});
 assert.equal(check.status(),200);assert.ok(!(await check.json()).some(f=>f.concurso_id===target.id));report.restored=true;
 }catch(e){report.failure=e.message;throw e;}
 finally{
  if(token&&target&&!report.restored){const r=await context.request.delete('http://localhost:13000/api/me/favorites/'+target.id,{headers:{Authorization:'Bearer '+token}});report.cleanup_status=r.status();}
  report.finished=new Date().toISOString();fs.writeFileSync(root+'/favorite-roundtrip.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));await browser.close();
 }
})().catch(e=>{console.error(e.message);process.exitCode=1});
