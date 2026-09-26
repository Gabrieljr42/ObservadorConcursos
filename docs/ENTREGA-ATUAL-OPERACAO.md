# Verificações da execução atual — 09/09/2026

Execução em andamento. Este registro não declara a meta concluída. O relatório
`ENTREGA-2026-09-09.md` descreve a entrega anterior.

Última verificação, 23:54 UTC: **32 seleções, 31 fontes e 99 cargos estruturados**,
48 versões e 47 notificações únicas. A apresentação visual/offline segue pendente.

API, trabalhador e agendador foram reiniciados com o código atualizado. Os seis
serviços ficaram ativos, PostgreSQL e Redis saudáveis. Login, renovação, checkpoint,
32 detalhes e revisões responderam HTTP 200; dados e ações existentes persistiram,
sem duplicação de notificações. Receipt após reinício:
`delivery-api-current-20260909T235433218948Z.json`.

Caruaru/IBAM recebeu seis cargos na versão 48, totalizando 20 vagas imediatas:
Auditor Fiscal Municipal e cinco especialidades de Analista Fiscal Municipal.
Vencimentos-base de R$ 6.000 e R$ 2.500; gratificações variáveis ficam separadas,
sem soma como salário garantido. Jornada de 40h, taxa de R$ 97, requisitos e cotas
foram conferidos. O cadastro de reserva permanece não confirmado. Prova de 29/11:
09h10 para os cinco primeiros cargos e 16h10 para Área Geral, Brasília, duração 4h.
Proposta `tpp-65cb518b1515682a28ffdeb0f4a28c20`, evidências do edital-base p3/p8/p13
e Anexo I p1/p2. Receipt `delivery-ibam-caruaru-applied-v3-20260909.json` no volume:
aplicação idempotente, versão 48 e outbox entregue. Verificação de detalhe/checkpoint:
`delivery-api-current-20260909T234813695157Z.json`.

Web reconstruída em 23 rotas, entry `a55fcae46cbdea828650086747a1c5cb`; 22 testes
mobile e TypeScript passaram. A tentativa visual às 23:45 confirmou
`NoModificationAllowedError` ao abrir o acesso exclusivo ao arquivo local.
Evidência `delivery-ui-blocker-20260909T234533Z.json`. Nenhum armazenamento foi apagado.

Barra Longa/ELO foi publicada como registro 32, versão 47, já com a retificação
incorporada: inscrições de 18/08 às 15h até 18/09 às 15h, Brasília; prova em
18/10; títulos até 13/11 e resultado final até 30/11, ambos às 23h59 (fuso não
explicitado na retificação). A etapa TAF foi substituída por títulos. Proposta
`tpa-663ecb1ce990af4cc1c784310cf8b78b`; aplicação e repetição idempotente em
`delivery-elo-applied-20260909T233001401522Z.json` no volume operacional.
O gate foi liberado após a aplicação. Detalhe e checkpoint reais foram verificados
em `delivery-api-current-20260909T233010389585Z.json`. Os cargos ainda estão pendentes.

Sebastião Leal/CONSEP foi publicado como registro31, versão46: processo seletivo
simplificado de provas e títulos para contratação temporária, edital001/2026,
inscrições12–19/01 e prova01/02/2026. O documento comprova encerramento às19h,
mas não comprova fuso; hora literal permanece na evidência sem offset inventado.
Proposta final `tpp-7c283d64ce9df519f9234936e2fc87a8`, receipt
`delivery-next-reextract-consep-precision-v3-20260909.json`. A proposta anterior
com offset inferido não foi aplicada e deixou de ser reproduzível após a correção.
Os 13 testes de precisão temporal passaram, incluindo rejeição de timestamp sem
evidência de fuso. Verificação via endereço web `/api`:
`delivery-api-current-20260909T231933523757Z.json`.

Itapecerica da Serra/AVANCASP permanece sem publicação: além das retificações de
inscrição/pagamento/prova prática, o edital-base traz prova objetiva em22/05 na
p41 e31/05 na p6. O conflito foi preservado em
`delivery-next-avancasp-exam-conflict-20260909.json`; nenhuma das datas foi promovida.

Itacarambi recebeu sete cargos na versão45: Agente Administrativo, Auxiliar de
Serviços Gerais, Controlador Interno, Motorista, Técnico Legislativo,
Telefonista/Recepcionista e Vigia. Foram conferidos vencimento básico, jornada,
requisitos e taxa no Anexo I separado, SHA
`739b4efa17c3ab3b85cdb50a70da7c3c34d38487612eefb849a59a8b8d7a00b4`.
Cinco cargos têm uma vaga geral e CR na coluna PcD; Motorista e Auxiliar são
somente CR geral/PcD. A observação por cargo evita apresentar CR PcD como geral.
Proposta aplicada `tpp-132598e22af9859dfba47af8a99325d3`; v1 imprecisa permaneceu
sem aplicação. Evidência `delivery-roles-cotec-itacarambi-20260909-v2.json` no volume.
API/checkpoint confirmaram os cargos e a observação; web reconstruída com essa
exibição e histórico de efeitos documentais (23 rotas, entry `860877bb8b49be8c7083c72a474ce57b`).
Os 21 testes mobile e TypeScript passaram. Nenhum armazenamento do navegador foi apagado.

Horários de inscrição complementados nas versões 42–44: Westfália, 12/05 às13h
a 10/06 às13h; Francisco Morato, 12/01 às10h a 12/02 às17h; Caruaru, 10/08 às00h
a 08/10 às23h59, todos com Brasília expresso nos documentos. Corrigida a publicação
que descartava precisão nova no mesmo dia. Duas verificações de integração passaram:
horário explícito aplica/idempotente; extração somente do dia preserva horário existente
nesse mesmo dia. As primeiras tentativas `no_change` foram preservadas; novos runs e
propostas foram aprovados/aplicados. Recibo de conferência de instantes UTC iguais no
detalhe e checkpoint: `delivery-api-current-20260909T225605006831Z.json`.

## Lote encerrado às 22:46 UTC

Publicados pelo fluxo normal, com autorização automatizada rastreável e aplicação
idempotente: EXAME/Lagoa da Prata (26, versão 37), COTEC/Câmara de Itacarambi
(27, versão 38), OBJETIVA/Westfália (28, versão 39), Instituto Mais/Francisco
Morato (29, versão 40) e IBAM/Caruaru (30, versão 41).

Lagoa da Prata é certificação ocupacional para função de Diretor Escolar, sem
criação de vagas de emprego. Inscrições 22/07 às 09h a 24/07 às 23h59 e prova
23/08 às 08h, Brasília. Itacarambi tem inscrições pagas de 10/09 às 08h a
07/10 às 17h, Brasília; o período separado de isenção foi 07 a 09/09. A prova
é em 13/12. O Anexo I de cargos foi incorporado posteriormente na versão 45.

Westfália: concurso 001/2026, edital de abertura 013/2026 (numerações distintas
expressas na primeira página), inscrições 12/05 a 10/06 e prova 05/07.
Francisco Morato: inscrições 12/01 a 12/02 e provas 22/03.
Caruaru: inscrições 10/08 a 08/10 e provas 29/11, em turnos distintos por cargo;
a data canônica não inventa um horário comum. Os cargos de Caruaru foram
incorporados posteriormente na versão 48; os outros dois seguem pendentes.

Evidências privadas: `delivery-exame-cotec-proposed-20260909.json`,
`delivery-next-reextract-three-2026-20260909.json` e recibos individuais
`delivery-next-applied-*` no volume operacional. Verificação real de login,
renovação de sessão, checkpoint, 30 detalhes e revisões:
`backend/.tenderproof/product-completion/delivery-api-current-20260909T224557483859Z.json`.
Snapshot das 99 fontes e orçamento:
`backend/.tenderproof/product-completion/delivery-current-20260909T224633373844Z.json`.
Os 84 testes direcionados de períodos, datas de prova e precisão temporal passaram.

O rascunho anterior de Barra Longa/ELO, `delivery-elo-effects-draft-20260909.json`,
foi sucedido pela proposta e aplicação descritas no início deste relatório.

## Autorização e conferência

O usuário autorizou corrigir o projeto e publicar no piloto os campos conferidos
documentalmente, passando por proposta, aprovação e aplicação. A conferência desta
execução é automatizada, sob essa autorização; não representa leitura humana dos PDFs.
Referência: anexo `6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt`,
SHA-256 `a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6`.

## Estado inicial confirmado

Snapshot somente leitura em 09/09/2026 às 20:27 UTC:
10 concursos de 9 fontes no catálogo, 91 adaptadores, 89 configurações habilitadas,
76 fontes com sucesso histórico de detalhe. Nenhum desses indicadores certifica
integração integral. Evidência no volume operacional:
`product-completion/delivery-current-20260909T202720815293Z.json`.

Solari: US$20 autorizados, US$5,26 reservados cumulativamente, oito sessões,
zero encerramentos pendentes. Cobrança efetiva desconhecida. Nenhuma nova sessão
paga aberta até esta verificação.

## Backup e recuperação

Mecanismo existente `scripts/observador-pilot.ps1 -Action Backup` executado antes
das alterações: `/backups/pilot-20260909T202501642Z-postgres.dump` e
`/backups/pilot-20260909T202501642Z-operational`, no volume
`observador-pilot_pilot_backups`.

A verificação integral de hashes passou para 9.121 arquivos (6.991.207.659 bytes),
incluindo cinco bancos SQLite. API, trabalhador e agendador foram pausados pelo
mecanismo de backup e retomados ao concluir. Os volumes foram preservados.

O dump PostgreSQL foi restaurado com `pg_restore --exit-on-error` no banco isolado
`delivery_restore_20260909`. Consulta confirmou 10 concursos, 14 versões,
14 propostas e 13 notificações. Somente esse banco temporário foi removido após
a verificação. O banco operacional original não foi substituído. A restauração
completa dos 6,99 GB operacionais ainda não foi repetida nesta execução; a
verificação integral do backup foi executada.

## Pedrinhas — preparação real

Run `tp-tcj-642cf1e7ede250489a8987a75c2f542d-1`, revisão
`drc-93e5642c8c8a46c392e331f8b45b2f57`. A preparação normal conferiu o manifesto,
preservou o edital-base de 14 páginas e a prorrogação de uma página com os hashes
esperados. Recibo:
`product-completion/delivery-pedrinhas-review-20260909T202819850380Z.json`.
Preparação concluída; aplicação posterior confirmada abaixo.

Input concreto preservado em
`product-completion/delivery-pedrinhas-input-20260909.json`: três campos canônicos,
período original, reabertura/vigente e quatro eventos com trechos dos artigos.
Inscrições têm 10h e Brasília comprovados. Prova (08h–11h) e gabarito (a partir
das 18h) preservam hora local com fuso não informado; pagamento e homologação
preservam apenas o dia.

## Classificação e API real

Corrigida a classificação de inscrições no backend e mobile: concursos futuros
não são abertos e campos desconhecidos não comprovam abertura. Datas sem horário
são inclusivas no calendário operacional de São Paulo; horários documentados
com offset são comparados como instantes. Status documental não é reescrito.
Meia-noite explicitamente comprovada usa o metadado de precisão da retificação.

Login, renovação de sessão, `/auth/me`, dois checkpoints e os dez detalhes/status
documentais retornaram HTTP 200 em 09/09/2026 às 20:40 UTC. O checkpoint continha
10 concursos, 14 versões, 1 alerta e 13 notificações sem duplicação. Favoritos e
alertas permaneceram iguais entre os checkpoints. Isso verifica a API real,
não substitui a verificação visual/offline.
Recibo privado: `delivery-api-current-20260909T204006219493Z.json`.

45 testes backend passaram para classificação, rastreabilidade da autorização e
publicação, incluindo bloqueio de proposta que tentaria reverter campo já
retificado. A autorização delegada integra o hash da proposta e o histórico da
versão, com `human_read=false`.

## Pedrinhas — aplicada e sincronizada pela API

Proposta `tpa-f08e7dff7a6df27a7c442a063f1ad154`, hash
`f08e7dff7a6df27a7c442a063f1ad154beae57880f0e6dc06800f2cffa8cf735`,
aplicada pela publicação normal na versão **15**. Reaplicação retornou a mesma
versão. O gate documental ficou sem pendência somente após a aplicação.
Recibo: `product-completion/delivery-pedrinhas-applied-20260909T210016431931Z.json`.

API reiniciada e verificada às 21:04 UTC: login, renovação, sessão, dez detalhes,
revisões e dois checkpoints HTTP 200; 15 versões e 14 notificações sem duplicação.
Alerta existente preservado. Recibo privado:
`delivery-api-current-20260909T210419455559Z.json`. Essa prova é do backend e
da resposta de sincronização; a apresentação visual permanece bloqueada pelo
handle OPFS descrito abaixo. Sete testes adversariais do fluxo passaram antes
da aplicação, incluindo bytes alterados, manifesto novo, revisão parcial,
concorrência, identidade diferente e trecho inventado.

Build web atualizado concluído: 23 rotas, bundle
`entry-8279e80d030b2df450a16b1c9f051618.js`, incluindo datas, retificações e revisão.

Regressão integrada após a aplicação: **77 testes passaram** (retificação,
gates adversariais, revisão documental, autorização, publicação, sessão offline
e classificação). Em nova consulta às 21:10 UTC foi verificada a igualdade do
histórico de retificações entre detalhe e checkpoint, com início/fim canônicos
13h UTC (10h Brasília), prova em 27/09 e revisão sem pendência. Recibo:
`delivery-api-current-20260909T211016404771Z.json`.

## Ibiúna

Conflito confirmado entre edital-base 002/2026 e cabeçalhos 001/2026 nos três
documentos novos. Nenhum prazo alterado ou gate limpo. Pacote e condição de
retomada em `ENTREGA-IBIUNA-CONFLITO.md`.

## Cargos — lote aplicado

Publicados 32 cargos conferidos por comparação independente dos PDFs: Carmo da
Cachoeira (5, versão 16), Ponta Porã (7, versão 17) e Caxambu do Sul (20, versão
18). Incluem vagas imediatas/CR, remuneração, jornada, requisitos e taxas.
Requisitos ACS/ACE e taxas Cebraspe foram corrigidos antes da aprovação.

Os primeiros runs adicionais tinham trechos gerados por leitura bruta do PDF;
o gate de publicação os rejeitou. Runs v3 usam o processador normal, sem
sobrescrever as observações anteriores. Propostas v3 foram aprovadas/aplicadas
com autorização delegada e repetidas sem criar novas versões.
Recibo: `product-completion/delivery-roles-applied-20260909T211356226828Z.json`.

A API confirmou os 32 cargos iguais entre detalhe e checkpoint às 21:14 UTC,
com 18 versões, 14 notificações únicas e o alerta existente preservado.
Recibo privado: `delivery-api-current-20260909T211432879103Z.json`.

## Verificação web em andamento

A abertura de `http://127.0.0.1:13000/inicio` apresentou aviso de dados salvos
indisponíveis. O log identificou especificamente `NoModificationAllowedError`
ao abrir um handle OPFS já mantido por outra instância. Não houve diagnóstico de
corrupção nem limpeza de armazenamento. Foi solicitado fechar outras abas ou
painéis anteriores, preservando ações offline. Trabalho de backend continua.

## Estado confirmado às 21:52 UTC — execução ainda incompleta

O catálogo possui **19 seleções de 18 fontes e 84 cargos estruturados**.
A API confirmou login, renovação, sessão, os 19 detalhes e revisões, além de
dois checkpoints: 29 versões e 28 notificações internas únicas. As ações
existentes de favoritos e alertas permaneceram iguais. Recibo privado:
`backend/.tenderproof/product-completion/delivery-api-current-20260909T214559821015Z.json`.
A fotografia `delivery-current-20260909T215249358739Z.json` confirma 99 fontes,
91 adaptadores, 89 configurações habilitadas e 81 fontes com sucesso histórico
de coleta de detalhe. Esses números não certificam integração integral.

Publicações posteriores ao lote de cargos acima:

| Concurso | Fonte / seleção | Resultado aplicado |
| --- | --- | --- |
| 11 | CONSULPAM / Maranguape 003/2025 | Identidade, inscrições e 43 cargos; ACE com 28 vagas imediatas e 280 CR; 42 áreas ACS com 20 CR cada. |
| 12 | FAPED / 001/2025 | Identidade, inscrições e Analista de Sanidade Vegetal; remuneração, jornada e requisitos conferidos. |
| 13 | FUMARC / CREA-MG 01/2026 | Identidade, inscrições e sete cargos; edital consolidado comparado com errata e anexo. Ver `ENTREGA-FUMARC-CONFERENCIA.md`. |
| 14 | FAPESE / PRONERA 007/2026 | Chamada para prestação de serviços por pessoa física; inscrições de 07 a 14/09/2026. Honorários por hora/etapa não foram convertidos em salário mensal. |
| 15 | IBADE / Florianópolis 005/2025 | Identidade e inscrições; cargos ainda não estruturados. |
| 16 | OMNI / Osvaldo Cruz 002/2024 | Identidade e inscrições; cargos ainda não estruturados. |
| 17 | CONTEMAX / Cubati 001/2024 | Identidade e inscrições; órgão corrigido antes da aplicação. |
| 18 | QUADRIX / Cristalina 1/2026 | Identidade, inscrições até 10/09/2026 e prova em 18/10/2026. |
| 19 | MSConcursos / CRIS 02/2026 | Identidade, inscrições de 30/04 a 31/05/2026 e prova em 14/06/2026; cargos ainda pendentes. |

As propostas passaram pela aprovação e aplicação normais, com autorização
delegada rastreável e `human_read=false`. Reaplicações retornaram a mesma versão.
Recibos de aplicação estão no volume operacional, em
`/var/lib/observador/tenderproof/product-completion/delivery-next-applied-*.json`.
Nenhuma ausência de extração foi certificada como ausência no documento.

A pesquisa e os filtros consideram nomes dos cargos estruturados, com
normalização de acentos. O detalhe distingue vagas imediatas e quantidade
conhecida de cadastro reserva. Botões abrem o edital ou a página oficial;
URLs S3 assinadas temporárias usam a página oficial como alternativa.
Datas documentadas sem horário não recuam um dia por conversão de fuso.
O coletor legado preserva campos retificados e registra observações
conflitantes para revisão. Alertas também consideram os cargos estruturados.

Validação adicional: 35 testes de publicação, cargos, proteção contra
regressão de retificação e alertas passaram. No mobile, 20 testes, TypeScript
e fixtures passaram; build web com 23 rotas, bundle
`entry-3a332e6a38b4c4e20d1ee5b4e31b0463.js`. São provas de implementação e API;
o aceite visual, reabertura e leitura offline desta versão continuam pendentes
pelo handle OPFS mantido por outra instância. Não houve limpeza do armazenamento.
API, worker e agendador foram reiniciados após a alteração mais recente de
alertas. A verificação às 22:00 UTC confirmou os 19 registros, os 84 cargos,
29 versões e 28 notificações sem regressão; recibo
`delivery-api-current-20260909T220056718179Z.json`.

A matriz `entrega-fontes-atual.csv` foi atualizada para as 99 fontes:
90 parcialmente funcionando, oito bloqueadas externamente e uma com
dependência humana. Nenhuma está certificada integralmente. Ibiúna mantém
o conflito entre cabeçalhos 001/2026 e edital-base 002/2026.

## Condição de continuidade

O lote delimitado de seis fontes de 2026 (LEGATUS, FUNVAPI, FUNCERN,
FGV, FCC e FACET) foi concluído até publicação e API, conforme seção abaixo. Os quatro
subagentes ativos encerraram com erro de limite de uso do Codex. A revisão
automática também rejeitou a cópia local de um recibo de Pedrinhas pelo mesmo
motivo; o original permanece no volume. Não houve tentativa de contornar a
rejeição. A consulta posterior de limites informou 0% utilizado, zero créditos
e zero resets disponíveis, em divergência com os erros de execução; não se
presumiu que isso liberasse as ações rejeitadas. Operações independentes de
consulta e reinício do piloto foram depois aprovadas e executadas normalmente,
permitindo continuar o trabalho; a cópia rejeitada não foi repetida.

Os cargos do CRIS foram posteriormente aplicados na versão 30, proposta
`tpp-da44c03c106e228a3fe349bfcc98fd4f`: Cuidador (uma vaga, R$1.726,52 básicos,
12x36, ensino médio, taxa R$24,90) e Médico PSF (uma vaga, R$17.584,43,
40 horas semanais, Medicina e CRM, taxa R$25,93). O adicional de 20% (*)
não foi somado ao vencimento; a quantidade de CR permanece não determinada.
Quatro testes de rejeição por documento/identidade divergente passaram.
A API confirmou os dois cargos iguais entre detalhe e checkpoint no recibo
`delivery-api-current-20260909T220547390093Z.json`.

Legalle: a inspeção anterior preservou hashes e excertos, mas não os PDFs.
A preparação normal de revisão adquiriu e preservou os três documentos,
com os mesmos hashes, no caso `drc-01fce885628b488085ea2a34fe8487b1`.
Recibo `product-completion/delivery-legalle-review-20260909T220726095061Z.json`.
A retificação de 06/11/2025 altera Secretário de Escola de até 20h para
40h, com CR, R$2.682,07 e ensino médio. A de 17/12/2025 desloca sorteio,
resultado e homologação para 22/12/2025. Não estão refletidas no edital-base.
A composição desses efeitos permanece pendência interna, sem publicação
da base desatualizada nem aprovação por presunção. Dados de classificação
individual permanecem privados.

Orçamento Solari confirmado: US$20 autorizados, US$5,26 reservados, oito
sessões e zero encerramentos pendentes. Cobrança efetiva desconhecida;
nenhuma sessão paga nova. Backup e teste de restauração descritos acima
continuam preservados. A meta permanece em execução; não houve aceite final.

## Lote de seis fontes de 2026 aplicado

| Concurso / versão | Fonte / órgão | Inscrições | Prova prevista |
| --- | --- | --- | --- |
| 20 / 31 | LEGATUS / Domingos Mourão | 12/01 a 09/02/2026 | 08/03/2026 |
| 21 / 32 | FUNVAPI / Cajueiro | 27/04 a 27/05/2026 | 28/06/2026 |
| 22 / 33 | FUNCERN / Lagoa de Pedras | 03/08 a 10/09/2026 | 01/11/2026 |
| 23 / 34 | FGV / Macaé | 30/03 a 30/04/2026 | 21/06/2026 |
| 24 / 35 | FCC / Câmara de Presidente Prudente | 22/04 a 21/05/2026 | 12/07/2026 |
| 25 / 36 | FACET / Floresta | 24/08 a 01/10/2026 | 01/11/2026 |

Cada seleção recebeu seis campos: título, órgão, edital, início e fim das
inscrições e data prevista da prova. Os cargos e valores por cargo desse lote
continuam pendentes de estruturação, não ausentes nos documentos.
As propostas e suas evidências estão no volume em
`product-completion/delivery-next-reextract-six-2026-20260909.json`.
O título FACET foi normalizado, preservando o texto observado original; usar
`delivery-next-reextract-facet-title-20260909.json` para sua proposta final
`tpp-acd439c83a23d2acc312352746af9f22`, run `tpr-114af82037b4`.
As propostas anteriores permanecem preservadas e não foram aplicadas.

Durante a preparação FACET, o ciclo recorrente descobriu um resultado
preliminar de isenção e o gate bloqueou a publicação. A revisão normal
`drc-5ad9f0b120754b18aa9fe7a7c75c1600` preservou esse PDF, SHA
`2037e1a1d6d3a77bca2243562c42de5fe8b71f915a49e166d431e7aa3c8c12e9`.
As 192 páginas, sem erro de extração, contêm resultados individuais e
cabeçalhos de cargos. O conteúdo não individual foi conferido integralmente;
não altera inscrições, prova, cargos, vagas ou vencimentos do edital.
A decisão `no_field_change` foi registrada com autorização automatizada
explícita; somente depois a proposta final foi criada e aplicada.
Recibos privados: `delivery-facet-review-20260909.json` e
`delivery-facet-review-approved-20260909.json`. Dados individuais não são
publicados no catálogo nem reproduzidos neste relatório.

Após esse lote, 80 testes de inscrições, listas, prova e classificação
passaram. API, worker e agendador foram reiniciados com o código atual.
Login, renovação, sessão, detalhes/revisões e checkpoints dos 25 registros
retornaram HTTP200; favoritos/alertas preservados, 35 notificações únicas.
Recibo `delivery-api-current-20260909T222420640201Z.json`; snapshot
`delivery-current-20260909T222436691518Z.json`. Os seis serviços estão ativos,
PostgreSQL e Redis saudáveis. A classificação sobre os dados reais reconheceu
nove seleções abertas: IDs1,3,7,8,9,14,18,22,25. Isso não substitui teste visual.

Nova abertura de `localhost:13000/inicio` em uma sessão sem abas anteriores
continuou mostrando o bloqueio de dados salvos. O armazenamento foi preservado.
Não foi declarada conclusão da meta: ainda há campos, fontes preservadas e
composição de retificações a executar, além do aceite visual/offline bloqueado.
