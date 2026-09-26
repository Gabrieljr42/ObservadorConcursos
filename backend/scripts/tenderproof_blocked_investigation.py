"""Read-only bounded recheck of 14 blocked sources and observed official alternatives."""
import asyncio, json, sys
from pathlib import Path
from urllib.parse import urlsplit
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.inventory import probe_url, now, PROBE_POLICY
ROOT=Path(__file__).resolve().parents[2]
NOTES={
'aocp_open':('https://www.institutoaocp.org.br/concursos/status/em-andamento','Página oficial indexada com filtro em andamento; não usar portal de notícias como substituto documental. Challenge local pode persistir; investigar renderização permitida e endpoints públicos observados.'),
'seprod_open':('https://www.seprod.com.br/concursos/','Rota oficial sem parâmetro indexada. Compartilha cadeia TLS; não remover validação. Exige correção da cadeia ou confiança pública verificável.'),
'fumarc_open':('https://www.fumarc.com.br/conheca-a-fumarc','Página institucional oficial indexada; não substitui listagem. Resultados de detalhes antigos indicam erro de aplicativo SharePoint. TLS e aplicação são impedimentos separados.'),
'unifil_open':('https://main.institutounifil.com.br/inscricoes-abertas','Rota oficial indexada com contador e detalhes /concurso/193. Portal institucional www.institutounifil.com.br aponta plataforma; não comprova acesso do coletor nem cobertura.'),
'leandroferreira_open':(None,'Busca retornou prefeitura e câmara do município de Leandro Ferreira, não a banca Leandro Ferreira & Consultoria. Sem vínculo oficial inequívoco; preservar ID e exigir documento de origem da entrada, sem substituir pela prefeitura homônima.'),
'iuds_open':('https://iuds.org.br/termos.pdf','Documento de termos no domínio oficial cita Gestor Edital. Não é edital principal nem prova de listagem. PDFs históricos em cdn.iuds.org.br comprovam hipótese documental, não cobertura atual. TLS pendente no host listado.'),
'institutoconsulplan_open':('https://www.institutoconsulplan.org.br','Domínio oficial indicado em publicação hospedada em cdnsite.institutoconsulplan.org.br/concursos/1328/12_1253088.pdf. Investigar identidade/alias com outras entradas Consulplan; não fundir automaticamente o ID Azure.'),
'ufu_selection':('https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1828','Detalhe oficial indexado de concurso docente ICENP 123/2026. Listagem acima de1MiB é limitação operacional, não indisponibilidade. Planejar particionamento por URLs observadas ou limite específico medido; separar vestibulares. Documento específico não prova descoberta completa.'),
'idgran_open':(None,'Busca literal não encontrou entidade organizadora oficial: resultados irrelevantes/homônimos. DNS continua pendente; exigir referência original/correção de identidade antes de escolher outro domínio.'),
'shdias_open':('https://www.shdias.com.br/concursos/index/','Rota oficial indexada com concursos e filtros. URL atual /concursos/ pode estar obsoleta; challenge deve ser confirmado na rota observada sem bypass. Residência médica exige triagem de escopo.'),
'oppus_open':(None,'Edital municipal de Pontal2016 confirma organizadora e www.oppusconcursos.com.br. Nenhuma alternativa oficial atual demonstrada. Oppus.shop e autoridade de registro são homônimos e foram excluídos.'),
'fapece_selection':('https://fapece.com.br/','Página se identifica como Fundação Assistencial e Previdenciária da EMATERCE, entidade de previdência complementar. Não prova equivalência a fapece.ce.gov.br nem fundação de fomento. Não substituir pelo nome; eleições de conselhos/benefícios fora do escopo.'),
'fapern_selection':('https://www.fapern.rn.gov.br/','Redirect oficial já observado. Portal suspenso por período eleitoral2026; não é lista vazia. Diário Oficial RN é evidência específica, não fonte substituta automaticamente. Excluir editais de fomento/bolsas sem contratação.'),
'fapeap_selection':('https://fapeap.portal.ap.gov.br/publicacoes','Portal estadual identifica FAPEAP e publicações; alternativa oficial observada. Amostra contém chamadas de startups, bolsas e pesquisa, fora do escopo de contratação. Acesso alternativo não homologa seleções de pessoas.')}
async def main():
 inventory=json.loads((ROOT/'docs/tenderproof-phases11-13-probe.json').read_text(encoding='utf-8'))
 rows=[r for r in inventory['sources'] if r.get('current_observation')=='access_requires_investigation']
 semaphore=asyncio.Semaphore(4)
 async with httpx.AsyncClient(timeout=12,follow_redirects=False,trust_env=False,verify=True,headers={'User-Agent':'ObservadorDeConcursos/1.0 (public source verification)'}) as client:
  async def check(row):
   async with semaphore:
    source=row['source_type']; alternative,note=NOTES[source]
    urls=list(row['listing_urls'])+([alternative] if alternative and alternative not in row['listing_urls'] else [])
    allowed=tuple(set(row['allowed_probe_hosts']+[urlsplit(u).hostname for u in urls]))
    probes=[]
    for url in urls:
     try: probes.append(await asyncio.wait_for(probe_url(client,url,allowed),25))
     except TimeoutError: probes.append({'requested_url':url,'observed_at':now(),'state':'timeout','reason':'Limite25s atingido'})
    result={'number':row['number'],'source_type':source,'name':row['name'],'category':row['category'],'original_observations':row['url_observations'],'recheck_observations':probes,'alternative_url':alternative,'investigation_note':note,'alternative_status':'accessible_homonym_identity_unresolved_not_replacement' if source=='fapece_selection' else 'not_found' if not alternative else 'http_observed_not_homologated' if probes[-1]['state']=='http_observed' else 'not_verified_for_collection','adapter_activated':False,'next_action':note}
    print(source,[(p['state'],p.get('http_status')) for p in probes],flush=True)
    return result
  result=await asyncio.gather(*(check(row) for row in rows))
 report={'generated_at':now(),'scope':'14 blocked sources, original URL rechecks and search-observed official alternatives; no adapter implementation or production activation','probe_policy':PROBE_POLICY,'search_note':'Primary-page search excerpts identify candidate URLs; index availability does not override local HTTP/TLS/DNS evidence. No authentication, paid browser, challenge bypass or disabled TLS. Non-HTML bytes not downloaded.','sources':result}
 (ROOT/'docs/tenderproof-blocked-investigation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 lines=['# Investigação de14 fontes com acesso pendente','',f"Data: {report['generated_at']}",'','URLs alternativas vieram de resultados de páginas oficiais indexadas; índice de busca não comprova acesso do coletor. Rechecagem com TLS validado, DNS público, allowlist exata,4 fontes simultâneas, máximo1MiB e25s por URL. Nenhum adaptador ativado; gate do piloto permanece independente.','']
 for r in result:
  lines.extend([f"## {r['number']}. {r['name']} — {r['source_type']}",'',r['investigation_note'],''])
  for p in r['recheck_observations']:
   lines.append(f"- [{p['requested_url']}]({p['requested_url']}): {p['state']}; HTTP {p.get('http_status','não recebido')}; {p['observed_at']}. {p.get('reason','')} {p.get('title','')}")
  lines.extend(['',f"Alternativa: {r['alternative_status']}. Nenhuma homologação inferida.",''])
 (ROOT/'docs/tenderproof-blocked-investigation.md').write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__': asyncio.run(main())
