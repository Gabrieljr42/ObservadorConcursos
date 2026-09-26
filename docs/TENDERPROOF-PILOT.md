# TenderProof — piloto de dez fontes (etapa 11)

Validação de 07/09/2026 UTC. O registro possui **dez adaptadores implementados**:
IBGP e IMESO anteriores, mais oito desta etapa. Cadastro no registro não ativa
coleta nem publicação. A cobertura de cada ciclo continua parcial quando falta
marcador explícito de fim, há filtros/abas não percorridos ou um limite foi atingido.

## Seleção e contrato observados

As oito fontes adicionais foram escolhidas a partir do inventário, mas a
implementação foi baseada em novas capturas HTTP, não em rotas presumidas.
O piloto cobre duas famílias de fornecedores, HTML próprio paginado, portais com
conteúdo oculto, namespaces de tenants em CDN, redirects assinados e seleção
institucional com conteúdos fora do escopo. Não são oito cópias do mesmo scraper.

| ID original / fonte | Listagem oficial | Família e evidência | Motivo / dificuldades / critério específico |
|---|---|---|---|
| `ibgp_open` / IBGP | https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp | JSP + REST renderizado; prova anterior com browser | Preserva risco de renderização e journal; evidência anterior de 9 candidatos, uma sessão encerrada. Nenhum novo browser pago nesta etapa. |
| `imeso_open` / IMESO | https://portal.imeso.com.br/edital | `/edital/ver/ID`, CDN com ID no caminho | Referência de contrato e armazenamento durável; provas anteriores de 115 candidatos e PDF29p; não confundir com cobertura integral. |
| `access_open` / ACCESS | https://access.selecao.net.br/index/abertos/ | `h3 a /informacoes/ID`; `/uploads/422/concursos/ID/anexos/` | Tenant422 distinto; candidato180 tem original + consolidado e exige revisão. Homologar ID, título e PDF do candidato183; seguir apenas abas observadas1/3/7. |
| `abcp_open` / ABCP | https://abcp.selecao.net.br/index/abertos/ | Mesmo contrato HTML/documental, tenant567 | Provar isolamento entre tenants do mesmo CDN; candidatos2869/2868/2867 reais. Abas1/2/3/4/5 observadas; ausência de próxima não prova fim. |
| `avancasp_open` / Avança SP | https://avancasp.selecao.net.br/index/abertos/ | Mesmo contrato, tenant301 | Nove candidatos visíveis; PDF272 com48p; candidatos271/270 excedem60p e foram recusados sem truncamento silencioso. |
| `ibade_open` / IBADE | https://portal.ibade.selecao.site/edital | Cartões `detalhes-edital`, `/edital/ver/ID`; `arquivo.php?file=` | Arquivo oficial redireciona302 para bucket `cdn-ibade.selecao.site` em S3 sa-east-1. Query assinada preservada somente no acesso; valores removidos dos relatórios. ID e bucket obrigatórios. |
| `fenix_open` / Fênix | https://portal.fenix.selecao.site/edital | Mesmo HTML, CDN específico `cdn-fenix.selecao.site/edital/1/ID/` | Reuso confirmado por cartões/linhas documentais reais; nenhuma permissão ampla a selecao.site. PDF 129 (14 páginas); 128 e 127 também validados. |
| `legalle_open` / Legalle | https://portal.editais.legalleconcursos.com.br/edital | Mesmo HTML; S3 sa-east-1, bucket `cdn.legalle.com.br` | Listagem877KB inclui blocos ocultos e modalidades diversas. Parser conta144 candidatos visíveis elegíveis, exclui qualificação/residência. PDF 2557 válido (32 páginas); 2548 ambíguo. |
| `fgv_open` / FGV | https://conhecimento.fgv.br/concursos | HTML Drupal, `.views-field-title`, `?page=1` observado | Inclui bloco em andamento e realizados;33 candidatos de concursos na primeira página, não33 inscrições abertas. Exclui rota de admissão FEMPAR. Principal retificado SEPLAG exige revisão; TJRS juiz26 válido (53 páginas). |
| `funcern_selection` / FUNCERN | https://funcern.br/concursos/ | Cartões `article h3`, `?page=2` observado; institucional | Dois concursos elegíveis entre15 cartões; bolsas, IFRN integrado, PROITEC, vestibular e modalidades sem classificação segura não entram. PDF Lagoa de Pedras62p; limite60 respeitado e recuperação local explícita80. |

## Regras que preservam a qualidade

- Nenhuma rota de paginação/API foi inventada. Cada nova página precisa estar no
  HTML observado e passar pelo contrato do adaptador. Sem marcador confiável de
  vazio, a página fica inconclusiva e candidatos conhecidos são preservados.
- HTML oculto, scripts e desafios não viram candidatos. O detalhamento exige URL,
  fonte e ID compatíveis; título observado é corroborado no conteúdo do detalhe.
- O nome do arquivo ou diretório contendo `edital` nunca promove um documento a
  principal. O título da linha precisa indicar edital. Resultados, anexos,
  gabaritos, retificações, manuais, políticas, históricos e convocações são
  classificados separadamente. Dois principais distintos exigem revisão.
- Edital consolidado não é escolhido silenciosamente. Se coexistir com original,
  há ambiguidade; sozinho, exige revisão. Retificações novas continuam no manifesto
  documental para revisão; não são aplicadas automaticamente.
- Selecao.net.br confere simultaneamente tenant e ID de concurso no documento.
  Edital/ver confere host/bucket e ID. Redirects são validados antes do acesso;
  documentos de outro tenant/concurso são recusados.
- FUNCERN serve uma canonical incorreta `http://localhost/...`. A exceção documentada
  aceita somente esse defeito observado, com **a mesma path**, URL real oficial e
  título em h1 corroborado. Localhost nunca é navegável. Outro host/path é erro.
  O PDF ainda precisa corroborar título. Nenhuma guarda DNS/TLS foi removida.
- O redirect FUNCERN admite exclusivamente
  `nyc3.digitaloceanspaces.com/repo/funcern.br/media/documents/`, com termos
  distintivos do slug do concurso no nome do arquivo. IBADE admite exclusivamente
  seu bucket e ID; não libera S3 inteiro.

## Evidências e limites

1. `backend/tests/fixtures/tenderproof_pilot/manifest.json`:18 páginas oficiais
   capturadas inicialmente (8 listagens,8 detalhes,2 páginas adicionais), com
   URLs, timestamps, tamanho e SHA-256. O pós-processador inicial falhou depois
   de salvar corretamente os bytes (bytearray no BeautifulSoup); o erro foi
   preservado e a análise refeita localmente com bytes. Fixtures são HTML oficial,
   não conteúdo criado para fazer o parser passar.
2. `tenderproof-pilot-live.json`:16 ciclos fonte (duas repetições das8), com
   até5 candidatos de listagem e até3 detalhes por fonte/ciclo. Não há alegação de
   percorrer todos os candidatos. O guard de páginas recusou PDFs maiores que60.
3. `tenderproof-pilot-redirects.json`:dois redirects302 observados sem seguir o
   destino antes de cadastrar namespaces. Parâmetros assinados estão removidos.
4. `tenderproof-pilot-live-redirect-validation.json`:quatro ciclos fonte adicionais
   (IBADE/FUNCERN), depois da correção dos destinos. IBADE 127 teve PDF de 26 páginas validado
   nos dois ciclos. FUNCERN adquiriu PDF62p, íntegro, e recusou o processamento60p.
5. `tenderproof-pilot-offline-recovery.json`:o PDF FUNCERN adquirido foi recuperado
   por hash, sem nova rede, e processado com limite explícito80p.62/62 páginas e
   identidade `valid`. Não é uma terceira observação live.

Os20 ciclos fonte dos dois relatórios HTTP totalizaram52 aberturas de detalhe e
32 downloads preservados (incluem repetição e downloads que excederam páginas).
Sete fontes adicionais têm aquisição+processamento `valid` repetidos ao vivo,
com24 aquisições válidas de12 documentos distintos. A oitava tem aquisição real
repetida e processamento válido posterior em recuperação local, somando13
PDFs distintos corroborados no piloto novo. **Nenhum evento novo real ocorreu
para comprovar detecção de mudança**; novidade/retry/crash usam cenários
controlados explicitamente identificados. Zero sessões de navegador foram criadas.

Hashes dos PDFs repetidos permaneceram iguais. Isso prova estabilidade dessas
amostras no intervalo, não deduplicação de observações contínuas por si só.
A prova adicional do motor contínuo com replay das capturas é entregue pelo
[tenderproof-pilot-continuous-replay.json](tenderproof-pilot-continuous-replay.json): oito fontes, dois ciclos cada, uma observação válida deduplicada por fonte e zero rede. A homologação declarada é a amostra/contrato
verificado, nunca a cobertura integral de uma fonte.

## Reproduzir

No diretório `backend`, usando o Python da `.venv` e `PYTHONPATH=.`:

```text
python -m pytest tests/test_tenderproof_pilot.py tests/test_tenderproof_sources.py -q
python scripts/tenderproof_pilot_live.py --report ../docs/novo-relatorio-piloto.json
python scripts/tenderproof_pilot_live.py --sources ibade_open funcern_selection --report ../docs/novo-relatorio-redirects.json
python scripts/tenderproof_pilot_recover_pdf.py
```

Os comandos live exigem rede pública e não ativam browser/produção. São limitados
a duas rodadas e até3 detalhes por fonte; param no primeiro resultado valid.
O script de recuperação usa os artefatos do relatório existente, sem rede.
Dados duráveis estão em `backend/.tenderproof/pilot-live-20260907/`:SQLite
operacional, `artifacts/` e processamento local. Esse ensaio no workspace não é
recomendação de SQLite em OneDrive/volume de rede para produção.

Os testes usam capturas reais mais perturbações sintéticas nomeadas. Cobrem
normal, vazio conservador, bloqueio, limite, documento errado/ambíguo, tenants,
canonical, identidade de título, páginas observadas e recuperação/fencing com
repetição de ciclos. O teste de fila injeta resultado controlado; não é prova de
extração real. A extração real está nos relatórios HTTP e na recuperação acima.

Produção permanece desabilitada. Não houve publicação canônica real, envio de
notificações, contratação de serviço nem navegador pago.

Validação focal: **97 testes passaram** (79 do piloto e 18 de fontes existentes).
Matriz estruturada: [tenderproof-pilot-validation.json](tenderproof-pilot-validation.json).

Regressão do contrato existente/inventário: **35 testes passaram**. A última
checagem de classificação documental e capturas oficiais passou **16 testes**.
