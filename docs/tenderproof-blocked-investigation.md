# Investigação de 14 fontes com acesso pendente

Data: 2026-09-07T23:49:02.711678+00:00

URLs alternativas vieram de resultados de páginas oficiais indexadas; índice de busca não comprova acesso do coletor. Rechecagem com TLS validado, DNS público, allowlist exata, 4 fontes simultâneas, máximo 1 MiB e 25 s por URL. Nenhum adaptador ativado; gate do piloto permanece independente.

## 3. Instituto AOCP - Concursos — aocp_open

Página oficial indexada com filtro em andamento; não usar portal de notícias como substituto documental. Challenge local pode persistir; investigar renderização permitida e endpoints públicos observados.

- [https://www.institutoaocp.org.br](https://www.institutoaocp.org.br): blocked_or_challenge; HTTP 403; 2026-09-07T23:48:59.752524+00:00.  Just a moment...
- [https://www.institutoaocp.org.br/concursos.jsp](https://www.institutoaocp.org.br/concursos.jsp): blocked_or_challenge; HTTP 403; 2026-09-07T23:48:59.885458+00:00.  Just a moment...
- [https://www.institutoaocp.org.br/concursos/status/em-andamento](https://www.institutoaocp.org.br/concursos/status/em-andamento): blocked_or_challenge; HTTP 403; 2026-09-07T23:48:59.969595+00:00.  Just a moment...

Alternativa: not_verified_for_collection. Nenhuma homologação inferida.

## 8. SEPROD Concursos — seprod_open

Rota oficial sem parâmetro indexada. Compartilha cadeia TLS; não remover validação. Exige correção da cadeia ou confiança pública verificável.

- [https://www.seprod.com.br/concursos/?utm_refererencia=em_andamento](https://www.seprod.com.br/concursos/?utm_refererencia=em_andamento): tls_verification_failed; HTTP não recebido; 2026-09-07T23:48:59.756551+00:00. certificado TLS não pôde ser verificado; não houve tentativa sem verificação 
- [https://www.seprod.com.br/concursos/](https://www.seprod.com.br/concursos/): tls_verification_failed; HTTP não recebido; 2026-09-07T23:49:00.097420+00:00. certificado TLS não pôde ser verificado; não houve tentativa sem verificação 

Alternativa: not_verified_for_collection. Nenhuma homologação inferida.

## 16. FUMARC Concursos — fumarc_open

Página institucional oficial indexada; não substitui listagem. Resultados de detalhes antigos indicam erro de aplicativo SharePoint. TLS e aplicação são impedimentos separados.

- [https://www.fumarc.com.br/SitePages/Home.aspx](https://www.fumarc.com.br/SitePages/Home.aspx): tls_verification_failed; HTTP não recebido; 2026-09-07T23:48:59.757542+00:00. certificado TLS não pôde ser verificado; não houve tentativa sem verificação 
- [https://www.fumarc.com.br/conheca-a-fumarc](https://www.fumarc.com.br/conheca-a-fumarc): tls_verification_failed; HTTP não recebido; 2026-09-07T23:48:59.829939+00:00. certificado TLS não pôde ser verificado; não houve tentativa sem verificação 

Alternativa: not_verified_for_collection. Nenhuma homologação inferida.

## 23. Instituto UniFil — unifil_open

Rota oficial indexada com contador e detalhes /concurso/193. Portal institucional www.institutounifil.com.br aponta plataforma; não comprova acesso do coletor nem cobertura.

- [https://main.institutounifil.com.br](https://main.institutounifil.com.br): blocked_or_challenge; HTTP 403; 2026-09-07T23:48:59.758546+00:00.  Just a moment...
- [https://main.institutounifil.com.br/inscricoes-abertas](https://main.institutounifil.com.br/inscricoes-abertas): blocked_or_challenge; HTTP 403; 2026-09-07T23:49:01.431205+00:00.  Just a moment...

Alternativa: not_verified_for_collection. Nenhuma homologação inferida.

## 25. Leandro Ferreira & Consultoria — leandroferreira_open

Busca retornou prefeitura e câmara do município de Leandro Ferreira, não a banca Leandro Ferreira & Consultoria. Sem vínculo oficial inequívoco; preservar ID e exigir documento de origem da entrada, sem substituir pela prefeitura homônima.

- [https://www.leandroferreira.com.br](https://www.leandroferreira.com.br): dns_resolution_failed; HTTP não recebido; 2026-09-07T23:48:59.869943+00:00. nome não resolvido neste ambiente; confirmar endereço e DNS 

Alternativa: not_found. Nenhuma homologação inferida.

## 28. IUDS Concursos — iuds_open

Documento de termos no domínio oficial cita Gestor Edital. Não é edital principal nem prova de listagem. PDFs históricos em cdn.iuds.org.br comprovam hipótese documental, não cobertura atual. TLS pendente no host listado.

- [https://www.iuds.org.br](https://www.iuds.org.br): tls_verification_failed; HTTP não recebido; 2026-09-07T23:48:59.885458+00:00. certificado TLS não pôde ser verificado; não houve tentativa sem verificação 
- [https://iuds.org.br/termos.pdf](https://iuds.org.br/termos.pdf): tls_verification_failed; HTTP não recebido; 2026-09-07T23:49:00.976176+00:00. certificado TLS não pôde ser verificado; não houve tentativa sem verificação 

Alternativa: not_verified_for_collection. Nenhuma homologação inferida.

## 38. Instituto Consulplan — institutoconsulplan_open

Domínio oficial indicado em publicação hospedada em cdnsite.institutoconsulplan.org.br/concursos/1328/12_1253088.pdf. Investigar identidade/alias com outras entradas Consulplan; não fundir automaticamente o ID Azure.

- [https://institutoconsulplan.azurewebsites.net/Concursos](https://institutoconsulplan.azurewebsites.net/Concursos): blocked_or_challenge; HTTP 403; 2026-09-07T23:49:00.048886+00:00.  Web App - Unavailable
- [https://www.institutoconsulplan.org.br](https://www.institutoconsulplan.org.br): http_observed; HTTP 200; 2026-09-07T23:49:00.159719+00:00.  Instituto Consulplan

Alternativa: http_observed_not_homologated. Nenhuma homologação inferida.

## 40. UFU / DIRPS - Seleções e Concursos — ufu_selection

Detalhe oficial indexado de concurso docente ICENP 123/2026. Listagem acima de1MiB é limitação operacional, não indisponibilidade. Planejar particionamento por URLs observadas ou limite específico medido; separar vestibulares. Documento específico não prova descoberta completa.

- [https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos](https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos): response_too_large; HTTP 200; 2026-09-07T23:49:00.275709+00:00. resposta excede 1 MiB; corpo parcial descartado 
- [https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1828](https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1828): http_observed; HTTP 200; 2026-09-07T23:49:00.878390+00:00.  DIRPS - Portal de Seleção: Edital

Alternativa: http_observed_not_homologated. Nenhuma homologação inferida.

## 41. IDGRAN Concursos — idgran_open

Busca literal não encontrou entidade organizadora oficial: resultados irrelevantes/homônimos. DNS continua pendente; exigir referência original/correção de identidade antes de escolher outro domínio.

- [https://idgran.com.br](https://idgran.com.br): dns_resolution_failed; HTTP não recebido; 2026-09-07T23:49:00.435070+00:00. nome não resolvido neste ambiente; confirmar endereço e DNS 

Alternativa: not_found. Nenhuma homologação inferida.

## 51. SHDias Consultoria e Concursos — shdias_open

Rota oficial indexada com concursos e filtros. URL atual /concursos/ pode estar obsoleta; challenge deve ser confirmado na rota observada sem bypass. Residência médica exige triagem de escopo.

- [https://www.shdias.com.br/concursos/](https://www.shdias.com.br/concursos/): blocked_or_challenge; HTTP 403; 2026-09-07T23:49:00.439066+00:00.  None
- [https://www.shdias.com.br/concursos/index/](https://www.shdias.com.br/concursos/index/): http_observed; HTTP 200; 2026-09-07T23:49:01.030773+00:00.  None

Alternativa: http_observed_not_homologated. Nenhuma homologação inferida.

## 61. Oppus Concursos — oppus_open

Edital municipal de Pontal2016 confirma organizadora e www.oppusconcursos.com.br. Nenhuma alternativa oficial atual demonstrada. Oppus.shop e autoridade de registro são homônimos e foram excluídos.

- [https://www.oppusconcursos.com.br](https://www.oppusconcursos.com.br): blocked_or_challenge; HTTP 403; 2026-09-07T23:49:01.058774+00:00.  Checking your browser before accessing. Just a moment...

Alternativa: not_found. Nenhuma homologação inferida.

## 79. FAPECE (Ceará) - Seleções — fapece_selection

Página se identifica como Fundação Assistencial e Previdenciária da EMATERCE, entidade de previdência complementar. Não prova equivalência a fapece.ce.gov.br nem fundação de fomento. Não substituir pelo nome; eleições de conselhos/benefícios fora do escopo.

- [https://fapece.ce.gov.br](https://fapece.ce.gov.br): dns_resolution_failed; HTTP não recebido; 2026-09-07T23:49:01.128858+00:00. nome não resolvido neste ambiente; confirmar endereço e DNS 
- [https://fapece.com.br/](https://fapece.com.br/): http_observed; HTTP 200; 2026-09-07T23:49:01.131958+00:00.  FAPECE – Fundação Assistencial e Previdenciária da EMATERCE

Alternativa: http_observed_not_homologated. Nenhuma homologação inferida.

## 80. FAPERN (Rio Grande do Norte) - Seleções — fapern_selection

Redirect oficial já observado. Portal suspenso por período eleitoral2026; não é lista vazia. Diário Oficial RN é evidência específica, não fonte substituta automaticamente. Excluir editais de fomento/bolsas sem contratação.

- [https://fapern.rn.gov.br](https://fapern.rn.gov.br): http_error; HTTP 503; 2026-09-07T23:49:01.327501+00:00.  Site temporariamente suspenso — Período Eleitoral 2026
- [https://www.fapern.rn.gov.br/](https://www.fapern.rn.gov.br/): http_error; HTTP 503; 2026-09-07T23:49:01.855177+00:00.  Site temporariamente suspenso — Período Eleitoral 2026

Alternativa: not_verified_for_collection. Nenhuma homologação inferida.

## 96. FAPEAP (Amapá) - Seleções — fapeap_selection

Portal estadual identifica FAPEAP e publicações; alternativa oficial observada. Amostra contém chamadas de startups, bolsas e pesquisa, fora do escopo de contratação. Acesso alternativo não homologa seleções de pessoas.

- [https://fapeap.ap.gov.br](https://fapeap.ap.gov.br): tls_verification_failed; HTTP não recebido; 2026-09-07T23:49:01.336799+00:00. certificado TLS não pôde ser verificado; não houve tentativa sem verificação 
- [https://fapeap.portal.ap.gov.br/publicacoes](https://fapeap.portal.ap.gov.br/publicacoes): http_observed; HTTP 200; 2026-09-07T23:49:01.560967+00:00.  FAPEAP - Fundação de Amparo à Pesquisa do Amapá

Alternativa: http_observed_not_homologated. Nenhuma homologação inferida.

## Evidências primárias complementares

- aocp_open: [página oficial indexada](https://www.institutoaocp.org.br/concursos/status/em-andamento)
- aocp_open: [página oficial indexada](https://noticias.institutoaocp.org.br/blog/evite-fraudes-sites-falsos-se-passam-pelo-instituto-aocp/)
- seprod_open: [página oficial indexada](https://www.seprod.com.br/concursos/)
- fumarc_open: [página oficial indexada](https://www.fumarc.com.br/conheca-a-fumarc)
- unifil_open: [página oficial indexada](https://main.institutounifil.com.br/inscricoes-abertas)
- leandroferreira_open: [página oficial indexada](https://www.leandroferreira.mg.gov.br/)
- leandroferreira_open: [página oficial indexada](https://leandroferreira.cam.mg.gov.br/licitacoes)
- iuds_open: [página oficial indexada](https://iuds.org.br/termos.pdf)
- iuds_open: [página oficial indexada](https://cdn.iuds.org.br/edital/1/97/71b34fb9c0fc17361f2ef6cc33e940e0.pdf)
- institutoconsulplan_open: [página oficial indexada](https://cdnsite.institutoconsulplan.org.br/concursos/1328/12_1253088.pdf)
- ufu_selection: [página oficial indexada](https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1828)
- shdias_open: [página oficial indexada](https://www.shdias.com.br/concursos/index/)
- oppus_open: [página oficial indexada](https://www.pontal.sp.gov.br/site/processo-seletivo/2016/processo-seletivo-02/edital_abertura.pdf)
- fapece_selection: [página oficial indexada](https://fapece.com.br/)
- fapern_selection: [página oficial indexada](https://www.cidadao.rn.gov.br/orgaos.html?tab=ipern)
- fapeap_selection: [página oficial indexada](https://fapeap.portal.ap.gov.br/publicacoes)

A tentativa inicial no sandbox teve falhas de transporte e foi substituída por execução de rede autorizada com os mesmos controles. FAPECE: o domínio .com.br acessível permanece identidade não resolvida e não é alternativa aprovada. Nenhuma entrada do inventário original foi reclassificada ou substituída.
