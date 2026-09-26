# Lote99 — grupo institucional Sudeste/Nordeste

Observação de 08/09/2026. Doze fontes investigadas; três estratégias de seleção de pessoas implementadas, com dois ciclos documentais válidos cada. O consolidado estruturado está em `tenderproof-batch99-southeast-validation.json`. Não houve login, browser, publicação, alteração de catálogo ou desativação de TLS.

## Contratos implementados

| Fonte | Escopo observado | Evidência |
|---|---|---|
| FAPESP | Concurso Público01/2026, página4470,58p | `tenderproof-batch99-southeast-live-observed.json` |
| FAPERJ | Artigo812.7.4, seleção para Diretor de Tecnologia20/2025,4p | `tenderproof-batch99-southeast-faperj-live.json` |
| FAPESB | REDA01/2026, abaDOM `reda-tab-2026`,9p | `tenderproof-batch99-southeast-fapesb-live.json` |

FAPESP: o inventário aponta a página de oportunidades de bolsas, inadequada ao produto. A página oficial `https://fapesp.br/index.php/processoseletivo` contém o concurso de pessoal. O endereço canônico4470 devolve meta-refresh para esse alias, preservado na captura. O documento principal é `https://fapesp.br/files/upload/4470/concurso0126.pdf`. O contrato exige explicitamente01/2026 e essa URL; mudança de número, ano, arquivo principal ou múltiplos originais falha para revisão. Assim4470 não transforma silenciosamente um concurso em outro. A tagHTML `base href=https://fapesp.br/` observada resolve um link documental relativo; mudança dessa base é rejeitada. Resultados e retificações ficam no manifesto, sem serem promovidos a principal.

FAPERJ: a navegação oficial observada liga a home a `/?id=35.5.3`, que redireciona ao arquivo `/arquivo_noticias.phtml`. A primeira página atual não contém seleção de pessoal e apresenta links reais de paginação. A notícia histórica `https://faperj.br/?id=812.7.4` foi observada separadamente, com o mesmo edital corroborado na lista oficial2025 `https://www.faperj.br/?id=415.6.5`. Os ciclos seguem esse candidato explicitamente conhecido; não alegam que a primeira página o descobriu. A buscaGET pública observada usaGoogleCSE, sem resultadosHTML, e não foi usada como descoberta falsa. O título do candidato conserva a expressão literal “Diretor de Tecnologia”, removendo apenas o prefixo editorial observado da notícia. A primeira extração com a manchete inteira ficouPARTIAL e foi preservada; a normalização do título foi validada em dois novos ciclos reais, sem enfraquecer a validação dos bytes.

FAPESB: a página de editais de pesquisa mistura fomento com aviso de22vagasREDA. O link externo de inscrições não oferece uma amostra identificável atual: mostra formulário sem opções e umPDFSAEB2014, que não foi utilizado. A busca oficial localizou `https://www.fapesb.ba.gov.br/reda/`, com a aba2026 e seu PDF original. O fragmento `#reda-tab-2026` corresponde a umID real noDOM; número/ano01/2026, título da seção, unicidade da aba e URL original são guardas explícitas. A aba2023 comentada não é coletada.29documentos da aba atual compõem o manifesto; apenas o original observado é principal.

## Nove fontes sem contrato de pessoal homologável nesta amostra

| Fonte | Diagnóstico concreto |
|---|---|
| FAPEMIG | `/pt/editais/` redireciona à home; conteúdo observado de propostas, fomento e bolsas. Sem cadeia de seleção de pessoal estabelecida. |
| FAPES | Página oficialConcursoPúblico contém declaração de não realização entre2023e2026. EvidênciaHTML datada; não é certificação geral de vazio nem validação dos bytes da declaração. |
| FAPESQ | Rota antiga`/editais/` pede login; menu público leva a`/editais-1` e à listagem2026 pública. Originais58/2026e57/2026 foram adquiridos e lidos: são bolsas, não emprego. |
| FAPEPI | TECNOVA3 é seleção de empresas/projetos para fomento; rótulo“Seleção Pública” não basta para ingresso no produto. |
| FAPEMA | Link de notícia sobre trainees observado; rota atual devolve conteúdo genérico sem o corpo da notícia ou documento. Escopo da oportunidade permanece não confirmado. |
| FAPECE | Host inventariado falhaDNS. Alternativa`fapece.com.br` identifica entidade assistencial/previdenciáriaEMATERCE e mostra“TemosVaga” emJPEG, semPDF. Identidade cadastral e aquisição de vaga emimagem ficam pendentes; não houve troca silenciosa porFUNCAP. |
| FAPERN | Redirectoficial para`www` responde503. Impedimento externo preservado. |
| FAPEAL | Home e listagem pública`/pesquisador/editais/` observadas; sem cadeia de seleção de pessoas na amostra. |
| FACEPE | Listagem pública`/editais/todos/` observada com programas de pesquisa/fomento/bolsas; sem original de contratação de pessoas estabelecido na amostra. |

O nome da entidadeFAPECE é corroborado pela referência institucional da [EMATERCE](https://www.ematerce.ce.gov.br/tag/fapece/); a captura HTTP dessa referência falhou, e o domínio alternativo foi preservado separadamente, sem alterar a identidade do inventário. A vaga da alternativa é `https://fapece.com.br/temos-vaga-2/`.

FAPESQ: os PDFs preservados em`.tenderproof/r99scope` têm34e32páginas e SHA verificada. O item12.6 do58/2026 e o item13.6 do57/2026 dizem que o regime de bolsas não constitui vínculo empregatício; os itens12.1e13.1 estabelecem concessão de bolsas. `tenderproof-batch99-southeast-scope-pdfs.json` registra URLs, hashes, páginas e decisões de escopo. A fonte não foi reclassificada inteira como bloqueada por login.

## Verificação e limites

33testes focais passaram em`.tenderproof/batch99-southeast-contracts.xml`. Incluem positivos reais, bolsas/fomento/declaração negativa, troca de edição, troca do original, baseHTML cruzada, aba duplicada, identidade de detalhe, caminhos privados/externos, ambiguidades, limites2MiB e challenge. O registro central resolve as três classes sem monkeypatch local no script.

Ciclos reais: uma listagem e até três detalhes por fonte/ciclo; PDFs até30MiB e60páginas. Capturas exploratórias separadas usam25s/2MiB e mantêm status, redirects e hashes. Nenhuma fonte ganhou comprovação de cobertura histórica completa; nenhuma retificação teve efeitos interpretados automaticamente. A aquisição válida é distinta da homologação de publicação, ainda não executada neste grupo.
