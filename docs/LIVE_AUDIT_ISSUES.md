# Relatório Técnico de Resolução de Problemas da Auditoria LIVE

> **Projeto**: Observador de Concursos  
> **Data da Emissão**: 2026-08-30T03:11:04.584609+00:00  
> **Documento**: Resolução Técnica e RCA (Root Cause Analysis) das 8 Prioridades e Conectores Auditados

---

## 1. Resumo dos 8 Problemas Prioritários Comprovados e Soluções

### 1.1. Quadrix (`quadrix_open`)
- **Problema**: A extração de vagas falhava em certames com tabelas multi-colunas (ex.: Cristalina com 1.136 vagas totais e CREF-SE com 170 vagas). Publicações continham lixo de rodapé e menus globais.
- **RCA**: O parser de PDF procurava apenas uma única menção de número isolado de vagas e o DOM capturava seções inteiras da página de rodapé.
- **Solução Implementada**: Analisador especializado em `dedicated/national.py` que isola a seção `DAS VAGAS` / `QUADRO DE VAGAS`, soma colunas de vagas imediatas e cadastro reserva oficial, extrai UF/município diretamente da frase de realização da prova no edital e limpa publicações via `parse_publications_from_dom()`.
- **Validação LIVE**: Cristalina capturada com 1.136 vagas e CREF-SE com 170 vagas; 2 certames ativos extraídos perfeitamente.

### 1.2. FEPESE (`fepese_open`)
- **Problema**: O portal FEPESE utiliza subdomínios dinâmicos por certame (ex.: `2026cpcelesc.fepese.org.br`), e os links de editais usam scripts de download `?go=edital`. Títulos vinham contaminados com botões de navegação e as datas de inscrição ficavam vazias.
- **RCA**: O conector padrão não visitava a aba `?go=cronograma` e tentava buscar PDFs estáticos na URL raiz.
- **Solução Implementada**: `FEPESEConnector` em `dedicated/national.py` implementado para:
  1. Descobrir subdomínios canônicos de certames no WordPress central.
  2. Consultar `?go=cronograma` para extrair início e fim de inscrições.
  3. Consultar `?go=edital` e `?go=concurso` para capturar todos os PDFs oficiais e publicações estruturadas.
  4. Atribuir UF `SC` padrão e extrair órgão/município (ex.: CELESC, COMCAP).
- **Validação LIVE**: 13 concursos ativos extraídos com publicações completas e datas normalizadas.

### 1.3. FUNVAPI (`funvapi_open`)
- **Problema**: Publicações e anexos oficiais ficavam vazios ou não capturavam aditivos do edital.
- **RCA**: O site da FUNVAPI estrutura os anexos em blocos dinâmicos dentro do DOM `.entry-content` com links que não continham a extensão `.pdf` no pathname.
- **Solução Implementada**: `FUNVAPIConnector` em `dedicated/regional.py` que rastreia os nós do DOM, inspeciona links de download com query params e extrai todos os anexos oficiais com hash de publicação unificado.
- **Validação LIVE**: 7 concursos ativos extraídos com anexos e cronogramas completos.

### 1.4. OBJETIVA Concursos (`objetiva_open`)
- **Problema**: Vencimentos eram contaminados por benefícios secundários (ex.: auxílio-alimentação de R$ 420,00 no concurso de Guaporé) e taxas de inscrição apareciam como salário mínimo.
- **RCA**: Regex de remuneração pegava o menor valor monetário encontrado no texto do edital sem filtrar menções a alimentação, transporte ou taxas.
- **Solução Implementada**: `ObjetivaConnector` em `dedicated/regional.py` com filtro de exclusão semântica para benefícios (`alimenta`, `refei`, `transporte`, `auxílio`) e separação estrita de taxas (< R$ 500) e salários (>= R$ 1.000).
- **Validação LIVE**: Guaporé extraído com remuneração real de R$ 3.404,76 a R$ 4.523,47, taxa de R$ 60,00/80,00 e benefícios isolados; 12 concursos ativos extraídos.

### 1.5. IDIB (`idib_open`)
- **Problema**: Status de certames vinha como nulo ou incorreto e taxas de inscrição vazavam para o campo de remuneração mínima.
- **RCA**: O portal IDIB renderiza datas de inscrição em cards específicos, enquanto a página principal possui selos genéricos de ano.
- **Solução Implementada**: `IDIBConnector` em `dedicated/national.py` refatorado para isolar a cláusula de inscrições e classificar valores < R$ 500 como taxa e >= R$ 1.000 como remuneração.
- **Validação LIVE**: Marco/CE capturado com 238 vagas e R$ 1.621,00 a R$ 12.308,33; Araguaína capturado com taxa de R$ 115,00 e salário de R$ 2.349,90 a R$ 6.055,93; 6 concursos ativos extraídos.

### 1.6. Instituto Avalia (`avalia_open`)
- **Problema**: Concurso da EPAGRI em Santa Catarina extraía dados residuais no rodapé e normalização incorreta de órgão/UF.
- **RCA**: Layout do Avalia insere informações de outros certames no rodapé da página de detalhes.
- **Solução Implementada**: `AvaliaConnector` em `dedicated/regional.py` padronizado para isolar o container do certame ativo, aplicar UF `SC` e extrair salários da tabela de cargos do Anexo I (R$ 4.362,02 a R$ 16.990,33, taxa R$ 200,00 e 40 vagas).
- **Validação LIVE**: 1 concurso ativo (EPAGRI) extraído com máxima integridade.

### 1.7. CPCon / UEPB (`cpcon_open`)
- **Problema**: Links do WordPress Download Manager geravam hashes duplicados por causa de query strings de timestamp (`?wpdmdl=...&refresh=...`) e quebras de linha em PDFs concatenavam dígitos de vagas incorretamente.
- **RCA**: A extração do WPDM mantinha a query string inteira e a leitura do PDF do edital de Guarabira misturava o edital de abertura com retificações.
- **Solução Implementada**: `CPConConnector` em `dedicated/regional.py` implementado para normalizar URLs WPDM (removendo `refresh`), ler o texto do edital com quebras de linha corrigidas e extrair 170 vagas e cargos.
- **Validação LIVE**: 10 concursos ativos extraídos (Guarabira 170 vagas, etc.).

### 1.8. EXAME Auditores (`exame_open`)
- **Problema**: Concursos da Exame misturavam seleções internas e certificações ocupacionais na mesma listagem, e a remuneração era extraída do edital preliminar ao invés do quadro de cargos.
- **RCA**: A plataforma ProSeleta abriga certificações escolares e seleções públicas na mesma rota `/index/1/`.
- **Solução Implementada**: `ExameConsultoresConnector` em `dedicated/regional.py` implementado com filtro de exclusão semântica para rejeitar certificações, capturar o edital normativo primário e extrair remunerações do Anexo I (ex.: Santana de Pirapama R$ 1.593,53 a R$ 6.221,41, taxa R$ 80,00; Córrego Fundo R$ 2.083,54 a R$ 4.368,63, taxa R$ 104,00).
- **Validação LIVE**: 4 concursos públicos ativos extraídos.

---

## 2. Aprimoramentos de Plataformas e Conectores Críticos

### 2.1. CEBRASPE (`cebraspe_open`)
- **Inovação**: Mapeada e integrada a REST API pública oficial do Cebraspe (`https://apis.cebraspe.org.br/cebraspe/eventos/tipo/concursos/fase/inscricoes-abertas` e `/cebraspe/eventos/{slug}`).
- **Benefício**: Crawling 100% estruturado reduzindo o tempo de execução de 160s para 6.5s, capturando 6 concursos abertos (TC-DF, SEAP-MA Especialista e Inspetor, PC-AL, Perícia MA, Ponta Porã) com URLs diretas no CDN Cebraspe.

### 2.2. Nosso Rumo (`nossorumo_open`)
- **Inovação**: Mapeadas as rotas oficiais ASP.NET do portal (`/Home/GetPublicacoes`, `/Cargo/Pesquisar` e `/Home/GetCronograma`).
- **Benefício**: Extração 100% estruturada de 2 concursos ativos (Mairiporã 5 vagas e Caraguatatuba) com tabela de cargos, salários de até R$ 5.574,03 e links diretos de editais em `/Arquivos/Projetos/`.

### 2.3. CONSULPAM (`consulpam_open`)
- **Inovação**: Atualização de `list_urls` para incluir a rota de concursos ativos `index.php?menu=concursos` e portal selecao.net.br.
- **Benefício**: 9 concursos ativos extraídos com sucesso e integridade (Groaíras 003/2026, Groaíras 002/2026, Massapê 001/2026, Beberibe 002/2026, Beberibe 001/2026, etc.).

### 2.4. FUNDEP (`fundep_open`)
- **Inovação**: Normalização da extração de cidade/UF a partir de `orgao` e `titulo` com default `MG`.
- **Benefício**: Concurso da FUMEP Sete Lagoas extraído com 39 vagas e cidade `Sete Lagoas/MG`.

### 2.5. Instituto Verbena / UFG (`verbena_selection`)
- **Inovação**: Mapeamento do subdomínio canônico `sistemas.institutoverbena.ufg.br`.
- **Benefício**: 4 concursos municipais goianos capturados com dezenas de publicações oficiais (Minaçu 31 pubs, São Miguel do Araguaia 12 pubs, Mutunópolis e Carmo do Rio Verde).

### 2.6. Fundações de Apoio e FAPs (Fontes 64 a 99)
- **Quality Gate Semântico**: 100% das 36 fundações auditadas com semântica estrita de `empty_evidence`. Extração de vagas reais de pessoal para UFU (11 itens), FUNPEC (10 itens), FATEC (3 itens), UNISELVA (2 itens), FUNCERN (2 itens) e FAPPR (1 item), com isolamento total contra editais de bolsas de fomento científico.

---

## 3. Tratamento de Exceções de Infraestrutura Externa

- **WAF / Cloudflare Challenge**: Portais com bloqueio Turnstile ativo (AOCP, UNIFIL, SHDias) são diagnosticados como `status = 'blocked'` com `error_type = 'CloudflareChallenge'`, sem degradação do pipeline.
- **Domínios Inativos / Expirados**: Bancas com DNS NXDOMAIN (Leandro Ferreira Consultoria, IDGRAN e FAPECE) são diagnosticadas como `status = 'failed'` com rastreabilidade completa de erro de rede.
