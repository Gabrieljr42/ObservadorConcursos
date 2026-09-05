# Segunda investigação independente — casos LOW (ondas 01–06)

## Metadados da revisão

- **Execução:** 2026-08-30 18:13:52 -03:00 (America/Sao_Paulo).
- **Escopo:** somente 03 Instituto AOCP, 07 Consulplan principal, 08 SEPROD, 28 IUDS, 34 CONTEMAX, 38 Consulplan Azure, 41 IDGRAN, 48 Apta Assessoria, 59 W2 Auditores e 61 Oppus Concursos. O caso 25 (Leandro) não foi investigado.
- **Método:** leitura integral dos dois anexos do objetivo; comparação com as seções correspondentes dos lotes BATCH_01–BATCH_05 e com `SOL_SPOTCHECKS.md`; buscas externas focadas em domínios oficiais, páginas oficiais, PDFs oficiais e inspeção de HTML/estado HTTP quando reproduzível.
- **Limitação de transporte:** chamadas HTTP locais com `Invoke-WebRequest`/`Test-NetConnection` foram bloqueadas pelo ambiente de execução (“tentativa de acesso a um soquete ... proibida”). Isso é falha de transporte, não ausência de itens. Quando a busca/abertura externa também falhou, o resultado foi mantido como `UNKNOWN`/`BLOCKED`, nunca como vazio.
- **Regra aplicada:** não foram inventados seletores, endpoints, contagens, APIs ou sucessores. Contagens exatas ficam `UNKNOWN` quando a listagem não foi observada integralmente ou quando a captura é de um índice antigo.

## Matriz executiva

| ID | Observado / relevante / ativo / fechado | Estado revisado | Estratégia | Confiança | Veredito curto |
|---:|---|---|---|---|---|
| 03 | Portal e cartões oficiais observados; relevante e ativo confirmados (totais exatos UNKNOWN) | `ACTIVE_DYNAMIC` | PLAYWRIGHT/HYBRID | Alta (atividade); média (extração) | Manter ativo; não tratar shell sem cartões como vazio |
| 07 | Domínio antigo responde com Cloudflare; universo próprio não observável por HTTP simples | `WAF_BLOCKED` + sucessor oficial confirmado | PLAYWRIGHT/HYBRID no sucessor | Alta (migração); média (extração no antigo) | Manter ID, mas apontar conector para o novo domínio |
| 08 | Site/identidade oficiais observáveis; cartões atuais não reproduzidos | `UNKNOWN/BLOCKED` (não vazio) | KEEP_BLOCKED + PLAYWRIGHT/HYBRID | Alta (bloqueio/incerteza); baixa (atividade) | Bloqueado até validação de navegador/rede |
| 28 | Portal operacional redireciona para conta suspensa; CDN só comprova arquivo histórico | `SITE_OFFLINE` | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED | Alta (indisponibilidade); baixa (universo atual) | Não esvaziar; sem sucessor confirmado |
| 34 | Domínio antigo 502; documentos apontam novo domínio, mas este não foi confirmado operacionalmente | `UNKNOWN/BLOCKED` | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED | Alta (pista de migração); baixa (atividade atual) | Migração provável; não promover novo domínio a fonte funcional |
| 38 | Azure retorna “Web App ... stopped”; listagem indexada é antiga | `SITE_OFFLINE`/`PORTAL_MIGRATED` | Alias legado; DEPRECATE_REVIEW_REQUIRED | Alta | Não contar snapshot Azure; deduplicar com sucessor Consulplan |
| 41 | Domínio fornecido e variantes sem DNS/página oficial reproduzível | `UNKNOWN/BLOCKED` | KEEP_BLOCKED + REVIEW_REQUIRED | Alta (domínio); baixa (universo) | Não é vazio; nenhum sucessor confirmado |
| 48 | Cards oficiais 2026 indexados; página ao vivo exige navegador compatível | `ACTIVE_DYNAMIC` | PLAYWRIGHT/HYBRID | Média | Ativo confirmado; não confundir Câmara 2026 com Prefeitura 2025/ITAME |
| 59 | Listagem oficial com paginação e 32 itens no snapshot; atos municipais 2026 confirmam operação | `ACTIVE_LEGACY_HTML` | HTML configurável + charset fallback | Média | Upgrade de LOW; totais/atualidade exata ainda UNKNOWN |
| 61 | DNS/hosting existem, mas portal e universo atual não são reproduzíveis; só históricos | `UNKNOWN/BLOCKED` | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED | Alta (bloqueio); baixa (atualidade) | Não declarar vazio; sem sucessor confirmado |

## 03 — Instituto AOCP (`aocp_open`)

**Tentativas e evidências (18:10–18:14 -03:00).**

1. `https://www.institutoaocp.org.br/concursos/status/inscricoes-abertas` — busca oficial indexada há poucos dias exibiu **SAEB — Secretaria de Administração do Estado da Bahia, Concurso Público nº 02/2026**, com status “Inscrições Abertas”. A abertura direta reproduziu o shell/menu e os headings, mas não os cartões.
2. `https://www.institutoaocp.org.br/?app=true` — página oficial indexada exibiu o cartão **CESAMA/MG, Edital 001/2026**, e as categorias “Finalizados”, “Inscrições Abertas” e “Em Andamento”. A abertura direta exibiu a estrutura, sem cartões no texto extraído.
3. `https://www.institutoaocp.org.br/concursos/685` e `/concursos/686` — links oficiais atuais para os dois concursos IFCE 2026; a notícia oficial confirma 276 vagas, 169 docentes e 107 técnico-administrativas.
4. `https://noticias.institutoaocp.org.br/blog/comecam-as-inscricoes-dos-novos-concursos-do-ifce-com-276-vagas/` — notícia institucional atual confirma os dois concursos e os links acima.
5. `https://link.institutoaocp.org.br/visualizar-prova-public/index.jsp?concurso=690` — página oficial de visualização de prova reproduziu backend legado com mensagem para habilitar JavaScript; não foi tratado como API.

**Tecnologia observada.** Shell HTML oficial com conteúdo de cards dependente de JavaScript/cliente; há host legado de documentos/provas. Nenhum endpoint XHR/API ou paginação estável foi efetivamente observado. Portanto, a ausência de cartões no HTML simples é uma captura parcial, não lista vazia.

**Universo e sucessor.** Portal oficial continua sendo `institutoaocp.org.br`; não foi encontrado sucessor oficial. Observado/relevante/ativo: pelo menos um concurso ativo (SAEB) e outros cartões atuais, mas os totais por estado são `UNKNOWN`. Fechados existem como categoria, sem contagem confiável.

**Estratégia e confiança.** PLAYWRIGHT/HYBRID; esperar renderização e capturar os cartões após a carga. Não criar API presumida. Confiança **alta** para atividade atual e URLs oficiais; **média** para extração técnica até observar DOM/rotas em navegador real.

**Veredito:** `ACTIVE_DYNAMIC`; manter fonte ativa. `UNKNOWN` para totais, nunca `EMPTY`.

## 07 — Consulplan principal (`consulplan_open`)

**Tentativas e evidências.**

1. `https://www.consulplan.net/` — a evidência de `SOL_SPOTCHECKS.md` foi confirmada: resposta HTTP é desafio gerenciado Cloudflare (“Just a moment…”, “Enable JavaScript and cookies to continue”, `cType: managed`). A abertura textual mostra apenas shell/headings. HTTP simples não é evidência de universo vazio.
2. `https://www.institutoconsulplan.org.br/` — novo domínio institucional oficial, acessível/indexável, com rodapé “© Instituto Consulplan 2026”, “Área do Candidato”, “Sistema de Inscrição” e link “consulte os concursos em andamento”. A página também exibe bloco “Próximos Concursos”, com cartões de órgãos como CRA-AM, CRM-MA, CREMERJ, CJF, Câmara Caxambu, Prefeitura Santa Maria Jetibá, IPREMB Betim, Câmara Caratinga, Alvinópolis, Porto Firme, Extrema, CREA-AP e FCCDA Itabira.
3. `https://www.institutoconsulplan.org.br/Concursos` — link oficial do novo domínio abriu uma listagem HTML indexável. O bloco “Inscrições abertas / Novos” inclui UFV PASES 2026–2028, CIDENNF, Câmara de Unaí VIII e Belo Vale (também há vestibulares, que devem ser filtrados conforme o escopo). O bloco “Em andamento” contém, entre outros, TJMG, Bálsamo, SAAEB Barretos, Potirendaba, CRESS/RO, Câmara Montanha, TJMS, Santa Maria Jetibá, Vitória, Ji-Paraná, Alagoa, Manaus, Uberlândia, CRA/PR e Eugenópolis. “Encerrados” também está presente.
4. Detalhes observados na nova listagem apontam para páginas oficiais como `/pases2026`, `/cidennf2026` e `/pref-potirendaba2026`; alguns detalhes retornaram 403 quando abertos isoladamente, mas a lista institucional foi reproduzida. Não foi observado endpoint API.
5. PDFs oficiais recentes no CDN `https://cdnsite.institutoconsulplan.org.br/concursos/...` citam o novo domínio como site oficial (Ji-Paraná 2026, Manaus SEMSEG 2026 e CRA/PR 2026).

**Comparação de universos.** O universo do `consulplan.net` antigo não pôde ser enumerado por causa do WAF. O universo Azure de #38 (abaixo) é um snapshot antigo e distinto. O universo atualmente observável é o da listagem oficial `institutoconsulplan.org.br/Concursos`, que possui novos/abertos, em andamento e encerrados e aparenta ser a operação vigente. Não é seguro somar os universos nem usar os antigos números indexados (5 abertos/~14 em andamento) como atuais.

**Tecnologia.** Principal antigo: Cloudflare managed challenge; precisa navegador/cookies/JavaScript (PLAYWRIGHT/HYBRID). Novo domínio: HTML indexável com âncoras e seções; detalhes podem exigir browser/controle de 403. CDN é host documental, não substitui a listagem.

**Sucessor e estratégia.** Sucessor oficial mais forte e atual: `https://www.institutoconsulplan.org.br/Concursos`. Manter o ID #07 para compatibilidade, mas configurar a busca operacional no novo domínio; deduplicar por URL canônica de detalhe, órgão/edital e documento/PDF. Confiança **alta** para migração/atividade do novo domínio; **média** para extração do domínio antigo sob Cloudflare.

**Veredito:** #07 `WAF_BLOCKED` no principal legado, com sucessor oficial ativo confirmado. Não declarar vazio.

## 08 — SEPROD (`seprod_open`)

**Tentativas e evidências.**

1. `https://www.seprod.com.br/concursos/` — página oficial indexada recentemente reproduz as categorias “Em andamento”, “Próximos concursos” e “Concursos finalizados”, login de candidato e atalhos de 2ª via, isenções, inscrições e envio de títulos, mas nenhum cartão atual no conteúdo disponível.
2. `https://www.seprod.com.br/` — página oficial indexada recentemente mantém a identidade e notícias; a notícia mais recente visível é “Prefeitura Municipal de Capim Grosso — Processo Seletivo Público 01/2022” (24/01/2022), com outras notícias antigas. Isso mostra manutenção/identidade, não prova de concurso atual.
3. `https://www.seprod.com.br/quem-somos/` — página institucional descreve a SEPROD como organizadora de concursos/processos seletivos públicos e privados.
4. PDFs oficiais/hospedados no domínio: `https://www.seprod.com.br/concursos/EDITAL_CONCURSO_S%C3%83O_FRANCISCO.pdf` (São Francisco/SE, histórico) e `https://www.seprod.com.br/concursos/Edital_Prorroga%C3%A7%C3%A3o_Processo_Seletivo_02.pdf` (Ipirá/BA, histórico), confirmando o padrão documental `/concursos/*.pdf`.
5. A abertura externa da listagem apresentou timeout/erro de ferramenta; HTTP local foi bloqueado por socket. Isso é falha de acesso, não lista vazia.

**Tecnologia.** Aparência de aplicação legacy server-rendered com rotas de candidato (`/area-do-candidato/index.asp`, `/concursos/confirmarinscricao.asp?...` em referências históricas) e autenticação; nenhum XHR/API foi observado.

**Universo e sucessor.** Estado atual de observado/relevante/ativo/fechado: `UNKNOWN`; há categorias oficiais, mas não cartões reproduzíveis. Não foi confirmado sucessor oficial; DNS atual do domínio resolve para `148.113.189.63`.

**Estratégia e confiança.** KEEP_BLOCKED + PLAYWRIGHT/HYBRID, depois validar renderização, status e paginação em navegador/rede que consiga acessar a origem. Confiança **alta** para “não foi possível enumerar”; **baixa** para atividade atual.

**Veredito:** `UNKNOWN/BLOCKED`; manter explicitamente bloqueado, nunca emitir vazio.

## 28 — IUDS (`iuds_open`)

**Tentativas e evidências.**

1. `https://portal.iuds.org.br/edital/ver/77` — abertura atual redireciona para `https://portal.iuds.org.br/cgi-sys/suspendedpage.cgi`, com “Account Suspended / This Account has been suspended. Contact your hosting provider.”
2. `https://www.iuds.org.br` e `https://portal.iuds.org.br` — DNS resolve, mas não houve lista operacional atual reproduzível; falhas locais de socket não foram tratadas como vazio.
3. PDFs no CDN oficial `https://cdn.iuds.org.br/edital/...` (por exemplo Mogi Guaçu 2023 e outros editais históricos) confirmam o acervo documental e a marca IUDS. O arquivo indexado mais recente encontrado ainda é edital de 2021, portanto não prova atividade atual.
4. Busca por sucessor oficial não encontrou outro portal operacional. `https://linktr.ee/iuds` aponta para “Site”, Facebook e vagas, mas não foi usado como sucessor oficial.

**Tecnologia.** Portal legado/hosting suspenso; CDN documental separado. Nenhuma API, lista atual ou seletor observável.

**Universo e sucessor.** Observado/relevante/ativo/fechado atuais: `UNKNOWN`. O fixture histórico `/edital/ver/77` não é utilizável enquanto a origem estiver suspensa. Nenhum sucessor confirmado; o CDN é apenas arquivo documental.

**Estratégia e confiança.** `SITE_OFFLINE`; KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED. Confiança **alta** para indisponibilidade atual; **baixa** para universo atual.

**Veredito:** `SITE_OFFLINE`, não `EMPTY`; preservar bloqueio e não fabricar contagem.

## 34 — CONTEMAX (`contemax_open`)

**Tentativas e evidências.**

1. `https://www.contemaxconsultoria.com.br/` — abertura externa retornou `502 Bad Gateway`; a rota histórica `/site/concursos-em-andamento/` e a página de Cubati também não foram reproduzíveis. HTTP local sofreu bloqueio de socket.
2. Evidência documental primária/near-primary do Concurso Cubati 001/2024: edital espelhado em `https://www.editorasolucao.com.br/blog/wp-content/uploads/2024/07/Concurso-Cubati.pdf` informa que os atos seriam publicados em **`www.contemax.com.br`**, não somente no domínio antigo. Outro espelho (`https://s3.portalt5.com/arquivos/Edital-CUBATI.pdf?v=1720185007`) menciona `http://www.contemax.com.br/site/area-restrita` e o e-mail `cubati@contemax.com.br`.
3. `https://temconcursos.com.br/...edital_de_abertura_n_01_2024-cubati.pdf` também registra `www.contemax.com.br` como site de publicação; trata-se de espelho, usado apenas para corroborar a pista documental.
4. `https://www.contemax.com.br/` e suas rotas não foram abertas pela ferramenta (marcadas como inseguras), e busca `site:contemax.com.br concursos` não entregou uma lista oficial reproduzível.
5. DNS independente: `contemaxconsultoria.com.br`, `www.contemaxconsultoria.com.br`, `contemax.com.br` e `www.contemax.com.br` resolvem para o mesmo endereço IPv4 `38.226.110.14` (com CNAMEs distintos nos `www`). Isso suporta alias/migração de hospedagem, mas não prova que exista uma listagem funcional.

**Tecnologia.** Domínio antigo com rotas históricas `/site/...`; nenhuma API, HTML atual ou seletor observável. O novo domínio é uma pista oficial de sucessor, não uma fonte confirmada.

**Universo e sucessor.** Observado/relevante/ativo/fechado atuais: `UNKNOWN/BLOCKED`. Possível sucessor oficial: `https://www.contemax.com.br`, sustentado por editais de Cubati e mesmo IP, porém operação/lista não confirmada. Não usar “nenhum concurso” de agregadores secundários como fonte de verdade.

**Estratégia e confiança.** KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED; revalidar ambos os domínios com navegador/rede. Se voltar, conector HTML dedicado para os slugs históricos, sem presumir endpoint. Confiança **alta** para a pista de migração/indisponibilidade antiga; **baixa** para atividade atual.

**Veredito:** `UNKNOWN/BLOCKED`; migração provável, mas não promovida a sucessor operacional. Nunca vazio.

## 38 — Consulplan Azure (`institutoconsulplan_open`)

**Tentativas e evidências.**

1. `https://institutoconsulplan.azurewebsites.net/Concursos` — spotcheck atual reproduziu HTTP 403 da Azure: “Error 403 — This web app is stopped / Web App - Unavailable”.
2. Resultados indexados antigos (cerca de dois meses) ainda exibiam uma fotografia do Azure com 5 itens em “abertos/novos” e cerca de 14 em “andamento”, mas essa fotografia é anterior ao estado parado e não pode ser contada como universo atual.
3. O novo portal oficial `https://www.institutoconsulplan.org.br/Concursos` contém hoje a listagem corrente descrita no caso #07, com seção de abertos/novos, em andamento e encerrados.
4. PDFs atuais no CDN `https://cdnsite.institutoconsulplan.org.br/concursos/...` citam o domínio novo como site oficial; isso reforça migração, não equivalência 1:1 dos IDs antigos.

**Comparação explícita dos universos.** Azure (#38) é um portal legado parado e seu snapshot indexado não é o universo corrente. O novo domínio possui universo atual mais amplo e diferente, com diversos concursos e processos em seções próprias. O principal antigo (#07) tem bloqueio Cloudflare, mas pertence à mesma marca/ecossistema; nenhum dos dois deve ser somado ao novo universo. Manter #07 e #38 por compatibilidade histórica, com alias/deduplicação por detalhe/órgão/edital/documento.

**Tecnologia.** Azure App Service parado (erro de plataforma, não lista vazia); sem API observável.

**Sucessor e estratégia.** Sucessor oficial atual: `https://www.institutoconsulplan.org.br/Concursos`. Marcar #38 como `PORTAL_MIGRATED`/`SITE_OFFLINE` e `DEPRECATE_REVIEW_REQUIRED`; o conector funcional deve ser o do novo domínio e o #38 deve ser alias legado. Confiança **alta**.

**Veredito:** `SITE_OFFLINE` + `PORTAL_MIGRATED`; não usar contagens antigas e não declarar vazio.

## 41 — IDGRAN (`idgran_open`)

**Tentativas e evidências.**

1. `https://idgran.com.br`, `http://idgran.com.br` e `https://www.idgran.com.br` — abertura externa marcada como insegura/não reexecutável; não houve página oficial reproduzível.
2. DNS local: `idgran.com.br` retorna NXDOMAIN. Também foram testadas variantes plausíveis (`idgran.com`, `.org`, `.org.br`, `idgranconcursos.com.br`, `institutoidgran.com.br`, `idgran.net.br`), sem resolução.
3. Busca por “IDGRAN concursos públicos organizadora” e por `idgran.com.br` só retornou páginas não oficiais ou homônimos (inclusive CNPJ de pessoa chamada Idgran Leal Santana). Esses homônimos foram descartados.

**Tecnologia.** Nenhuma página/HTML/API/selector oficial observável.

**Universo e sucessor.** Observado/relevante/ativo/fechado: `UNKNOWN/BLOCKED`. Nenhum sucessor oficial confirmado.

**Estratégia e confiança.** KEEP_BLOCKED + REVIEW_REQUIRED; revalidar somente se houver URL oficial nova. Confiança **alta** para domínio fornecido sem DNS/página reproduzível; **baixa** para universo.

**Veredito:** `UNKNOWN/BLOCKED`; não é `EMPTY`.

## 48 — Apta Assessoria (`apta_open`)

**Tentativas e evidências.**

1. `https://www.aptaconcursos.com.br/` — busca oficial indexada ontem exibiu cartões correntes, incluindo **Concurso Público 01/2026 — Câmara Municipal de Aragarças-GO**, com ações “INSCREVER-ME”, “DOCUMENTOS” e “2ª VIA DO BOLETO”, e **Concurso Público 01/2026 — Prefeitura de Nova Ponte-MG** com documentos.
2. `https://www.aptaconcursos.com.br/servicos/` — página oficial confirma serviços de concursos públicos e processos seletivos.
3. `https://www.aptaconcursos.com.br/sobre` — página institucional identifica Apta Assessoria e Consultoria Ltda., fundada em 2004, dedicada a concursos públicos.
4. A abertura direta do domínio e de `/sobre` retornou “Navegador incompatível com o sistema”, recomendando Firefox/Chrome/Opera/Safari. A rota de login `https://www.aptaconcursos.com.br/concursos/login_candidato_sistema` é restrita por CPF. Isso é incompatibilidade/browser gate, não vazio.
5. A página oficial da Câmara de Aragarças `https://www.aragarcas.go.leg.br/%F0%9F%93%A2-concurso-publico-na-camara-municipal-de-aragarcas/` (16/06/2026) confirma o Concurso Público 001/2026 da Câmara. Não confundir com o concurso da Prefeitura 01/2025, organizado por ITAME, que é outro certame.
6. Padrões históricos observados: `https://aptaconcursos.com.br/concursos/publicacoes/{órgão}/{id}` e CDN documental `https://arquivos.aptaconcursos.com.br/arquivos/{id}/{arquivo}.pdf`. Os placeholders não foram convertidos em IDs/arquivos inventados.

**Tecnologia.** Portal dinâmico com gate de compatibilidade de navegador; login separado; nenhum endpoint API confirmado. Cards indexados demonstram que o backend/listagem existia e tinha estado atual, mas o HTML direto não é suficiente.

**Universo e sucessor.** Observado: cartões oficiais 2026 e históricos; relevante/ativo confirmados em pelo menos Aragarças Câmara 2026 e Nova Ponte 2026; totais exatos `UNKNOWN`; fechados também aparecem historicamente. Nenhum sucessor oficial identificado.

**Estratégia e confiança.** PLAYWRIGHT/HYBRID com navegador compatível; capturar cards/links e separar Câmara Aragarças 2026 de Prefeitura Aragarças 2025/ITAME. Confiança **média**: alta para existência/atividade dos cartões, média-baixa para extração até superar o gate.

**Veredito:** `ACTIVE_DYNAMIC`; não vazio.

## 59 — W2 Auditores (`w2_open`)

**Tentativas e evidências.**

1. `https://www.w2consultores.com.br/` — abertura oficial reproduziu menu/status (“Inscrições Abertas”, “Em andamento”, “Homologado”, “Finalizado”, “Suspenso”, “Cancelado”) e a listagem “Processos Seletivos — Em andamento”. O snapshot exibiu, entre outros, Juscimeira/MT 001/2026, Lambari d’Oeste/MT 001/2025, Salto do Céu/MT 001/2025, Poconé/MT 001/2025, Santo Antônio do Leste/MT 001/2025, Cláudia/MT 001/2025, Reserva do Cabaçal e Rio Branco/MT.
2. No rodapé da mesma página: **“Mostrando 1–10 de 32”**, com paginação 1–4, próxima e última. Isso é evidência de 32 itens no snapshot da categoria observada, não garantia de 32 ativos hoje; os intervalos exibidos incluem processos já encerrados pela data.
3. `https://www.w2consultores.com.br/index/todos/?dir=&ord=&pg=7&pp=10&q=` — página histórica indexada, com paginação e 247 páginas; é outra fotografia/filtro e não deve ser misturada ao snapshot de 32.
4. `https://www.w2consultores.com.br/index/todos/?busca=CONQUISTA+` — busca oficial indexada mostra 18 resultados e confirma parâmetros de consulta/paginação, sem evidência de API.
5. `https://www.w2consultores.com.br/informacoes/82/` — detalhe oficial server-rendered (Santo Afonso 001/2015) com informações, publicações e vagas.
6. Atos oficiais municipais atuais confirmam operação da W2: `https://amm.diariomunicipal.org/publicacao/1809840/` (PSS 002/2026, inscrições 07–16/04/2026), `https://amm.diariomunicipal.org/publicacao/1796308/` (PSS 001/2026, Rio Branco/MT, inscrições 17–31/03/2026) e `https://riobranco.mt.gov.br/uploads/publicacoes/3754/` (edital oficial que identifica W2 e CNPJ 41.424.264/0001-50).

**Tecnologia.** HTML legado/server-rendered com filtros e paginação. A abertura direta de `/index/todos/` sofreu erro de decodificação Unicode; isso requer fallback `windows-1252`/Latin-1, não pode virar lista vazia. Rodapé informa plataforma compartilhada ProSeleta (`https://www.proseleta.com.br/`), mas a fonte continua sendo W2.

**Universo e sucessor.** Observado: 32 itens na categoria do snapshot e detalhes/paginação; relevante/atividade 2026 confirmadas pelos atos oficiais; ativo exato e fechados atuais `UNKNOWN`. Não há sucessor da W2; ProSeleta é plataforma de gestão, não substituto da organizadora.

**Estratégia e confiança.** HTML configurável com charset fallback, preservando parâmetros `dir`, `ord`, `pg`, `pp`, `q` apenas como navegação observada (não como API presumida). Confiança **média**, upgrade de LOW: listagem/paginação/detalhe são reproduzíveis, mas frescor e classificação de ativo ainda precisam de validação por data/status.

**Veredito:** `ACTIVE_LEGACY_HTML`; não vazio. Manter observação de 32 como snapshot e não como contagem corrente.

## 61 — Oppus Concursos (`oppus_open`)

**Tentativas e evidências.**

1. `https://www.oppusconcursos.com.br` e versão HTTP — abertura externa marcada como insegura/não reexecutável; nenhuma página/listagem oficial atual reproduzível.
2. DNS independente resolve `www.oppusconcursos.com.br` por CNAME Hostinger (`www.oppusconcursos.com.br.cdn.hstgr.net`) e endereços Hostinger, portanto há infraestrutura DNS/hosting, mas isso não prova aplicação HTTP funcionando nem conteúdo atual.
3. Busca secundária `https://www.acheconcursos.com.br/concursos-organizadora/oppus` (cerca de dois meses) afirma “nenhum concurso aberto, previsto ou em andamento” e aponta o domínio Oppus. É apenas corroborativa e não é fonte de verdade.
4. Documentos históricos primários confirmam que a Oppus existiu como organizadora: `https://www.condor.rs.gov.br/wordpress/wp-content/uploads/2017/02/prefeitura-condor-concurso-publico-001-2015-edital-de-abertura.pdf` cita o domínio; `https://www.coffito.gov.br/nsite/?p=5558` (CREFITO-4, 2016) também informa inscrições pelo portal Oppus.
5. Nenhum domínio sucessor oficial ou edital primário recente (2025/2026) foi encontrado.

**Tecnologia.** Nenhum HTML/API/selector atual observável. DNS Hostinger não deve ser tratado como sucessor.

**Universo e sucessor.** Observado/relevante/ativo/fechado atuais: `UNKNOWN/BLOCKED`; só há histórico. Nenhum sucessor confirmado.

**Estratégia e confiança.** KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED; conservar o ID e revalidar somente com origem oficial funcional. Confiança **alta** para bloqueio/ausência de evidência atual reproduzível; **baixa** para universo atual.

**Veredito:** `UNKNOWN/BLOCKED`; não declarar vazio.

## Recomendações para o consolidado

- Tratar #07 e #38 como IDs compatíveis do mesmo ecossistema Consulplan, mas com estados distintos: #07 é WAF-blocked no domínio antigo; #38 é Azure app stopped/legacy. O conector operacional deve usar `institutoconsulplan.org.br/Concursos`, com deduplicação por detalhe/órgão/edital/documento.
- Não converter falha de socket, timeout, erro 403/502, incompatibilidade de navegador, conta suspensa ou erro de decodificação em `[]`/“nenhum concurso”.
- Contagens declaradas neste relatório são snapshots observados, nunca contagens atuais implícitas: W2 “1–10 de 32” pertence à captura daquela categoria; o antigo Azure “5/~14” é obsoleto; Consulplan novo tem cartões atuais, mas totais exatos permanecem `UNKNOWN`.
- Nenhuma API foi confirmada nos dez casos. Onde a tecnologia foi reconhecida, a estratégia indicada é browser/HTML configurável com fallback de charset, e não endpoint inferido.
