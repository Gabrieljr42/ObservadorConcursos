# Consolidação de apoio — fontes 90–99

Este documento consolida exclusivamente o conteúdo de `BATCH_08.md` para as dez fontes finais do inventário. A observação foi realizada em 30/08/2026 (America/Sao_Paulo). `Relevant` significa seleção de pessoas para trabalho (concurso, PSS, contratação temporária, emprego, estágio ou função). Bolsas, fomento, premiações, chamadas de projetos, propostas e contratação de projetos permanecem fora do escopo.

## Critérios de leitura

- `Observed` é o universo visível/confirmado na superfície consultada, não uma estimativa do acervo inteiro.
- `Active` exige evidência explícita de inscrição ou estado atual; publicação recente, resultado ou “em andamento” isolado não basta.
- `UNKNOWN` é preservado quando a página é dinâmica, bloqueada, incompleta ou não oferece filtro de estado. `0 confirmado` significa somente que nenhum item da amostra foi confirmado, não que o universo completo seja vazio.
- Valores de bolsa, auxílio ou fomento não são salário; número de projetos não é número de vagas de emprego.
- As prioridades são recomendações de trabalho: P0/P1 para correções críticas/fixtures; P2 para conectores claros ou fontes com seleção de pessoal; P3 para lacunas operacionais recuperáveis; P4 para investigação secundária; P5 para bloqueio/identidade ainda não resolvidos; P6 para fonte dependente de confirmação externa; P7 para monitoramento de baixa prioridade, vazio legítimo ou amostra integralmente fora de escopo.

## Matriz das fontes 90–99

| ID | Fonte | URL fornecida | URL correta | Tecnologia | Observed | Relevant | Active | Estratégia recomendada | Confiança | Prioridade |
|---:|---|---|---|---|---|---|---|---|---|:---:|
| 90 | FAPEMAT | https://fapemat.mt.gov.br | https://www.fapemat.mt.gov.br/pt/editais_1 | Liferay/server-rendered com componentes dinâmicos e PDFs | UNKNOWN (abas observadas; itens não renderizados) | 0 na amostra; universo total UNKNOWN | 0 confirmadas; universo total UNKNOWN | HYBRID + KEEP_BLOCKED; retestar a rota Liferay e seguir PDFs oficiais | MEDIUM | P5 |
| 91 | FAPEG | https://goias.gov.br/fapeg/categoria/editais/ | https://goias.gov.br/fapeg/editais/inscricoes-abertas/ | WordPress/Goiás, tabela HTML + PDF/XLSX | 8 itens abertos observados | 0 na lista aberta; 1 histórico relevante fechado | 0 | CONFIGURABLE_HTML + PDF; filtrar PSS/contratação de pessoa | HIGH | P2 |
| 92 | FAPDF | https://fap.df.gov.br | https://www.fap.df.gov.br/ | Portal governamental server-rendered + páginas anuais/PDF | UNKNOWN (arquivo heterogêneo, sem lista atual única) | 0 nas páginas consultadas; universo total UNKNOWN | 0 confirmadas; universo total UNKNOWN | HTTP_HTML/CONFIGURABLE_HTML + KEEP_EMPTY; monitorar arquivos sem usar SIGFAPDF autenticado | MEDIUM | P7 |
| 93 | FAPT | https://fapt.to.gov.br | https://fapt.to.gov.br (operacionalidade não confirmada) | PDF_INDEX/OTHER; domínio com timeout | UNKNOWN | UNKNOWN; nenhum item de pessoal confirmado | UNKNOWN | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED; manter PDFs `central.to.gov.br` como fallback | MEDIUM | P5 |
| 94 | FAPEAM | https://fapeam.am.gov.br | https://www.fapeam.am.gov.br/editais/ | WordPress com componente Vue/dinâmico; PDFs | UNKNOWN (placeholders `Carregando...`/template) | UNKNOWN; nenhum anúncio de pessoal confirmado | UNKNOWN | HYBRID/PLAYWRIGHT para descobrir a lista; não tratar placeholder como vazio | MEDIUM | P3 |
| 95 | FAPESPA | https://fapespa.pa.gov.br | https://www.fapespa.pa.gov.br/chamadas/ | WordPress + PDF; inscrição externa SIPROS | 4 blocos de chamadas observados | 1 PSS relevante (8 vagas), fechado | 0 | CONFIGURABLE_HTML + PDF; SIPROS somente como inscrição/resultado público comprovado | HIGH | P2 |
| 96 | FAPEAP | https://fapeap.ap.gov.br | https://fapeap.portal.ap.gov.br/ | Portal estadual Amapá server-rendered + arquivos `matrix.amapa.gov.br` | 7 publicações recentes | 0 confirmadas; amostra de projetos/bolsas | UNKNOWN; nenhuma seleção ativa confirmada | CONFIGURABLE_HTML no domínio novo + PDF; manter SIG FAPEAP separado | HIGH/MEDIUM | P3 |
| 97 | FAPERR | https://faperr.rr.gov.br/ | https://faperr.rr.gov.br/ | Shell de aplicação/OTHER; conteúdo `Loading...` | UNKNOWN | UNKNOWN; nenhum item de pessoal confirmado | UNKNOWN | KEEP_BLOCKED + reteste PLAYWRIGHT; não criar API sem evidência | MEDIUM/LOW-MEDIUM | P5 |
| 98 | FAPERO | https://rondonia.ro.gov.br/fapero/publicacoes/ | https://rondonia.ro.gov.br/fapero/publicacoes/ | WordPress governamental, HTML + arquivos anuais/PDF | pelo menos 3 blocos programáticos em 2026 | 0 confirmadas na amostra; histórico total UNKNOWN | 0 relevante confirmada | HTTP_HTML + CONFIGURABLE_HTML + PDF + KEEP_EMPTY; filtrar vínculo de pessoal | HIGH/MEDIUM | P7 |
| 99 | FAPAC | https://fapac.ac.gov.br/ | https://fapac.ac.gov.br/98-2/ | WordPress/HTML + PDFs e possível iframe/feed | pelo menos 7 publicações/blocos | 0 confirmadas; amostra fora de pessoal | UNKNOWN; universo completo UNKNOWN | CONFIGURABLE_HTML + PDF + KEEP_EMPTY; manter SIGFAPAC fora do discovery | HIGH/MEDIUM | P7 |

## Justificativa curta das prioridades

- **90 — P5:** a rota oficial possui abas, mas a listagem foi rejeitada/expirou e não há prova de feed completo; reteste é pré-requisito para qualquer conector.
- **91 — P2:** tabela HTML, estados separados e um PSS histórico de contratação permitem conector genérico com fixture negativa/positiva.
- **92 — P7:** as superfícies consultadas são de fomento, bolsas, eventos ou credenciamento ad hoc; manter monitoramento barato, sem priorizar conector de emprego.
- **93 — P5:** o domínio oficial sofreu timeout e não há migração confirmada; não substituir pela FAPTO nem transformar um PDF de fomento em oportunidade.
- **94 — P3:** há uma lista institucional plausível, porém o conteúdo é populado por JavaScript; vale investigação controlada de browser/XHR antes de classificar o universo.
- **95 — P2:** existe PSS verificável com oito vagas e anexos de cargo/remuneração; é a fonte do lote com maior valor imediato, ainda que o caso observado esteja fechado.
- **96 — P3:** a migração para o domínio novo está confirmada e a tabela é simples, mas a amostra atual não contém seleção de pessoal; implementar depois das fontes com oportunidade/fixture.
- **97 — P5:** a homepage entrega somente shell/`Loading...`; a lista pública e o backend permanecem desconhecidos e dependem de reteste controlado.
- **98 — P7:** a superfície HTML é recuperável e os exemplos observados são bolsas, inovação, projetos e premiações; não há evidência de contratação no recorte.
- **99 — P7:** a página de editais está acessível, mas as publicações observadas são bolsas, pesquisa, PPSUS, Centelha, premiações ou OSC; monitorar filtro institucional sem criar adaptador especializado.

## Resumo de plataformas e reuso

| Cluster | Fontes | Reuso seguro | Limite obrigatório |
|---|---|---|---|
| HTML/WordPress + PDF | 91, 95, 98, 99 | Extrair título, data, link, PDF, retificação e resultado por headings/links ou tabela; seguir arquivos derivados | Não presumir a mesma estrutura CSS, endpoint ou status; validar cada domínio |
| Portal governamental com arquivo e SIG separado | 90, 92, 94, 96, 97, 99 | Modelo comum de superfície pública + documentos, mantendo SIGFAPEMAT, SIGFAPDF, SIGFAPEAM, SIG FAPEAP, SISC&T e SIGFAPAC fora do discovery sem evidência pública | Sistema de submissão autenticado não é feed de vagas e não prova API compartilhada |
| Portal estadual do Amapá e downloads externos | 96 | Reaproveitar leitura de tabela `Data/Descrição/Arquivo` e download em `matrix.amapa.gov.br` | Confirmar que o arquivo pertence à FAPEAP e não a outra secretaria/programa estadual |
| Lista JavaScript/shell | 94, 97 | Playwright apenas para observar carregamento e requests públicos, com fallback para PDFs | Placeholders e `Loading...` não são lista vazia; não inventar endpoint |
| Inscrição externa de seleção | 95 | Acompanhar SIPROS somente quando resultado/estado público estiver comprovado | Não usar login nem tratar o sistema externo como fonte institucional primária |
| PDFs oficiais sem portal operacional | 93 | Registrar PDF e cronograma como evidência documental de classificação | PDF isolado não prova cobertura nem substitui uma listagem; FAPT não deve ser confundida com FAPTO |

## Quality checks para o runbook

1. Confirmar que esta consolidação contém exatamente dez linhas de matriz, IDs 90 a 99, sem duplicação ou salto.
2. Preservar `UNKNOWN` para universo incompleto, timeout, shell, placeholder ou estado não publicado. Nunca converter “nenhum encontrado” em vazio global.
3. Exigir evidência textual de cargo, emprego, estágio, função, concurso, PSS ou contratação temporária de pessoa para `Relevant`.
4. Rejeitar bolsas, auxílios, fomento, pesquisa, PPSUS, Centelha, PDPG, premiações, startups, OSC, submissões e contratação de projetos. Valor mensal de bolsa não é salário e quantidade de projetos não é vaga.
5. Exigir inscrição atual, prazo vigente ou marcador oficial equivalente para `Active`; resultado, retificação, convocação posterior ou “em andamento” não bastam isoladamente.
6. Respeitar limites institucionais: separar FAPEMAT de SECITEC/SEDUC/SEDEC, separar FAPT de FAPTO e separar sistemas SIG/SISC&T de anúncios públicos.
7. Deduplicar edital-base, retificação, resultado e convocação por URL canônica + número/programa + órgão; não contar cada PDF derivado como novo certame.
8. Retestar fontes P5/P3 sem bypass agressivo e registrar data/fuso, URL e motivo do bloqueio. WAF, timeout, `Carregando...` e `Loading...` devem gerar estado operacional, não `Active=0` falso.
9. Usar somente seletores/endpoints efetivamente observados. Em páginas sem seletor/API confirmado, manter `UNKNOWN` e preferir headings, cabeçalhos de tabela e links visíveis.
10. Validar cada fixture negativa (bolsa/fomento) e positiva (PSS FAPEG/FAPESPA) antes de promover a fonte ao fluxo de pessoal.

