const {chromium}=require('playwright');const fs=require('fs');
(async()=>{
 const a=fs.readFileSync('backend/.tenderproof/local-pilot/ACESSO-LOCAL.md','utf8');const f=k=>a.match(new RegExp(k+':\\s*([^\\r\\n]+)'))[1].trim(' `');
 const b=await chromium.launch({channel:'msedge',headless:true});const c=await b.newContext();const p=await c.newPage();const out={at:new Date().toISOString(),responses:[],url_before:await p.url()};
 p.on('response',async r=>{if(/auth\/login/.test(r.url())){let body='';try{body=(await r.text()).slice(0,120)}catch{}out.responses.push({url:r.url(),status:r.status(),contentType:r.headers()['content-type']||null,location:r.headers()['location']||null,body_prefix:body})}});
 await p.goto('http://localhost:13000/login');out.login_body=(await p.locator('body').innerText()).slice(0,500);
 if(!/Dados salvos indisponíveis/i.test(out.login_body)){await p.getByPlaceholder('E-mail',{exact:true}).fill(f('E-mail'));await p.getByPlaceholder('Senha',{exact:true}).fill(f('Senha'));await p.getByText('Entrar',{exact:true}).click();await p.waitForTimeout(5000)}
 out.url_after=await p.url();out.final_body=(await p.locator('body').innerText()).slice(0,500);out.receipt='backend/.tenderproof/product-completion/app-sync/login-route-'+Date.now()+'.json';fs.mkdirSync('backend/.tenderproof/product-completion/app-sync',{recursive:true});fs.writeFileSync(out.receipt,JSON.stringify(out,null,2));console.log(JSON.stringify(out));await b.close();
})().catch(e=>{console.error(e.message);process.exitCode=1});
