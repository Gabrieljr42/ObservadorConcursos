# Pendências verificáveis das oito fontes sem adaptador

Auditoria documental realizada em 2026-09-09, somente sobre artefatos já existentes em `backend/.tenderproof/product-completion/`. Nenhuma URL foi acessada nesta auditoria, nenhuma nova sessão Solari foi aberta e nenhum bloqueio foi contornado. As oito fontes continuam sem adaptador e sem integração no aplicativo; HTTP 200 isolado, HTML baixado ou conteúdo indexado não foi tratado como conclusão.

## AOCP — `aocp_open` (inventário 3)

- **Bloqueio:** o endereço oficial configurado e a página de concursos retornaram HTTP 403 com página `Just a moment...`; o host público alternativo também retornou HTTP 403 com o mesmo desafio. Não existe adaptador registrado.
- **Evidência:** `backend/.tenderproof/product-completion/missing-sources/20260908T204606Z/report.json` (raiz e `/concursos.jsp`, 403, HTML preservado); `backend/.tenderproof/product-completion/remaining-bancas/public-addresses-20260909T184942Z/report.json` (`https://link.institutoaocp.org.br/`, 403); `backend/.tenderproof/product-completion/remaining-bancas-solari-20260909/report.json` (sessão encerrada, status `challenge`, 403); classificação em `docs/tenderproof-product-status.json`.
- **Alternativa já evidenciada:** nenhuma alternativa de aquisição foi comprovada. A página `link.institutoaocp.org.br` é apenas outro endereço que reproduziu o desafio.
- **Próximo passo:** quando houver acesso público legítimo sem desafio (ou feed oficial acessível), confirmar escopo e implementar aquisição; depois executar o fluxo completo com revisão humana. Não usar bypass, stealth ou autenticação não autorizada.

## SEPROD — `seprod_open` (inventário 8)

- **Bloqueio:** o endereço configurado falhou na validação TLS por certificado expirado; o endereço institucional alternativo também falhou. HTTP redireciona para HTTPS que falha. Nenhuma adaptação ou bypass TLS foi usado.
- **Evidência:** `backend/.tenderproof/product-completion/seprod/initial-verification.json` (raiz e concursos); `backend/.tenderproof/product-completion/seprod/instituto-verification.json` (`www.institutoseprod.com.br`); `docs/tenderproof-product-status.json` registra `discovery_and_pagination=blocked` e certificado expirado nos dois hosts.
- **Alternativa já evidenciada:** nenhum endereço funcional. Os dois hosts registrados falham pelo mesmo motivo; não há feed ou documento local comprovado.
- **Próximo passo:** aguardar correção legítima do certificado ou obter endereço oficial atual com TLS válido; então verificar descoberta/paginação antes de criar adaptador. Nunca desativar verificação TLS.

## UniFil — `unifil_open` (inventário 23)

- **Bloqueio:** o site e a rota de inscrições abertas retornaram HTTP 403 com desafio de navegador. A rota de detalhe também reproduziu o desafio. Não há conteúdo de concurso utilizável nem adaptador.
- **Evidência:** `backend/.tenderproof/product-completion/unifil-solari/report.json` (sessão encerrada, `status=challenge`, HTTP 403); `backend/.tenderproof/product-completion/unifil-solari/public-routes-verification.json` (inscrições e `/concurso/193`, 403, `challenge=true`); `backend/.tenderproof/product-completion/remaining-bancas/public-addresses-20260909T184942Z/report.json` (rota alternativa, 403); HTML preservado em `unifil-solari/http-listing.html` e `http-detail.html`.
- **Alternativa já evidenciada:** nenhuma. Busca indexada mostrou possíveis concursos, mas o próprio registro diz que isso não substitui aquisição atual.
- **Próximo passo:** obter acesso público legítimo ou feed oficial acessível e repetir a prova de descoberta; não resolver/contornar o desafio.

## Leandro Ferreira & Consultoria — `leandroferreira_open` (inventário 25)

- **Bloqueio:** o domínio inventariado não resolve DNS (`getaddrinfo failed`); identidade da consultoria e escopo compatível permanecem sem comprovação. Não há adaptador.
- **Evidência:** `backend/.tenderproof/product-completion/missing-sources/20260908T204606Z/report.json`; `backend/.tenderproof/product-completion/remaining-bancas/20260909T164344Z/report.json`; `backend/.tenderproof/product-completion/new-sources/20260909T004654Z/verification.json`; classificação e endereço em `docs/tenderproof-product-status.json`.
- **Alternativa já evidenciada:** nenhuma. A busca anterior encontrou município homônimo, explicitamente insuficiente para substituir a consultoria.
- **Próximo passo:** confirmar por fonte institucional ou contato público qual é o endereço oficial atual e, somente então, implementar aquisição; não substituir por homônimo.

## IUDS — `iuds_open` (inventário 28)

- **Bloqueio:** o domínio configurado falhou por certificado TLS expirado; a variante `portal.iuds.org.br` apresentou o mesmo problema. HTTP redireciona para HTTPS inválido. Não há adaptador.
- **Evidência:** `backend/.tenderproof/product-completion/new-sources/20260909T004654Z/verification.json`; `backend/.tenderproof/product-completion/new-sources/20260909T004654Z/` registra `certificate has expired`; `docs/tenderproof-product-status.json` referencia `new-sources/20260909T004654Z/verification.json` e registra ambos os hosts.
- **Alternativa já evidenciada:** nenhuma alternativa funcional. Aviso indexado de CDN foi identificado como de 2022 e não prova integração atual.
- **Próximo passo:** obter endereço oficial com certificado válido ou aguardar correção do servidor; então comprovar descoberta atual. Não desativar TLS nem usar a página indexada antiga como dado atual.

## IDGRAN — `idgran_open` (inventário 41)

- **Bloqueio:** o domínio inventariado falhou na resolução DNS. A identidade oficial e qualquer endereço alternativo continuam não comprovados; não há adaptador.
- **Evidência:** `backend/.tenderproof/product-completion/missing-sources/20260908T204606Z/report.json`; `backend/.tenderproof/product-completion/remaining-bancas/20260909T164344Z/report.json`; `backend/.tenderproof/product-completion/new-sources/20260909T004654Z/verification.json` (`getaddrinfo failed`); classificação em `docs/tenderproof-product-status.json`.
- **Alternativa já evidenciada:** nenhuma. O registro exige não trocar por banca de nome semelhante.
- **Próximo passo:** confirmar por evidência institucional um domínio atual e compatível; somente depois testar descoberta e implementar adaptador.

## Oppus — `oppus_open` (inventário 61)

- **Bloqueio:** a aquisição HTTP comum retornou desafio HTTP 403. A sessão Solari posterior chegou a HTTP 200, mas o registro de produto classifica o conteúdo como artigos italianos de apostas, sem links de seleção; isso não comprova identidade institucional nem escopo de concursos. Não há adaptador.
- **Evidência:** `backend/.tenderproof/product-completion/new-sources/20260909T004654Z/verification.json` e `oppus.html` (página de challenge); `backend/.tenderproof/product-completion/remaining-bancas/20260909T164344Z/report.json` (403); `backend/.tenderproof/product-completion/remaining-bancas-solari-20260909/report.json` (200, `content_acquired`); `docs/tenderproof-product-status.json` registra o conteúdo incompatível observado e preserva histórico municipal de Pontal/2016 sem associação atual.
- **Alternativa já evidenciada:** a sessão Solari obteve uma página, mas ela não é alternativa utilizável: não contém escopo compatível nem links de seleção. Nenhum feed ou documento oficial foi comprovado.
- **Próximo passo:** confirmar identidade e endereço oficial atual por fonte institucional e obter uma listagem de concursos; não publicar artigos atuais nem associar automaticamente o domínio ao registro histórico de 2016.

## FAPEMAT — `fapemat_selection` (inventário 90)

- **Bloqueio:** o domínio configurado redirecionou para `www.fapemat.mt.gov.br`, mas a conexão foi encerrada sem resposta. Três aliases públicos já registrados tiveram o mesmo `RemoteProtocolError`. Não há adaptador nem aquisição atual persistida.
- **Evidência:** `backend/.tenderproof/product-completion/fapemat/discovery-20260909T151214Z/verification.json` (302 para `www`, depois desconexão); `editais-current.json` (erro de desconexão); `backend/.tenderproof/product-completion/fapemat/public-aliases-20260909T192447Z/report.json` (site www, SEFAZ e SECOM, todos desconectados); `backend/.tenderproof/product-completion/fapemat/solari-recheck-20260909/report.json` (sessão encerrada em `navigate`, `ERR_CONNECTION_RESET`, reserva registrada sem cobrança confirmada).
- **Alternativa já evidenciada:** os três aliases oficiais preservados são alternativas concretas de endereço, mas todos falharam com a mesma desconexão; nenhum conteúdo foi adquirido. O registro indica conteúdo oficial indexado, porém isso não substitui aquisição atual.
- **Próximo passo:** quando o serviço responder normalmente, validar a rota de editais e o escopo de seleções; depois implementar e provar coleta repetida. Não usar conteúdo indexado antigo como publicação atual.

## Estado de fechamento

As oito fontes permanecem pendências externas individualizadas: nenhuma tem coleta → extração → conferência → publicação autorizada → sincronização → aplicativo comprovada. Os artefatos acima são evidência de bloqueio de acesso/identidade, não prova de incompatibilidade institucional. O restante da entrega deve avançar com fontes implementadas e deixar estas oito para retomada somente após mudança verificável no acesso ou na identidade oficial.
