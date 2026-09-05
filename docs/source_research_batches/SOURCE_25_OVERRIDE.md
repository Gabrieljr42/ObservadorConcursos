## 25 — Leandro Ferreira Consultoria

Identificador técnico: `leandroferreira_open`  
URL fornecida: `https://www.leandroferreira.com.br`  
URL oficial correta: `UNKNOWN`  
Verificação: 30/08/2026, aproximadamente 18:05, `America/Sao_Paulo` (UTC−03:00).

### Navegação

Homepage, abertos, em andamento, encerrados, detalhe e documentos: `UNKNOWN`. A URL fornecida não possui endereço web resolvível. Nenhum sucessor oficial atribuível à consultoria foi encontrado. O portal `leandroferreira.mg.gov.br` pertence ao município homônimo e **não** é sucessor comprovado desta fonte.

### Universo observado

Observed: `UNKNOWN`. Relevant: `UNKNOWN`. Active: `UNKNOWN`. Closed: `UNKNOWN`. Out of scope: qualquer conteúdo do município de Leandro Ferreira/MG quando usado como substituto desta identidade. A falha DNS não permite concluir zero.

### Listagem

Container, item, título, link, ID e status: `UNKNOWN`; nenhuma listagem oficial atual foi recuperada.

### Paginação

Método e parâmetros: `UNKNOWN`.

### Exemplo real

Nenhum exemplo atual e atribuível à consultoria foi confirmado. Não usar PSS municipal homônimo como fixture.

### Campos

`titulo`, `orgao`, `modalidade`, `cargo`, `area`, `cidade`, `uf`, `status`, `vagas`, `salario_min`, `salario_max`, `escolaridade`, `taxa`, `prova_data`, `edital_numero`, `edital_data`, `inscricao_inicio`, `inscricao_fim`, `link_edital` e `link_inscricao`: `NÃO DISPONÍVEL/UNKNOWN`.

### Publicações

Estrutura, tipos, seletor, API e regras de deduplicação: `UNKNOWN`. Não anexar documentos de terceiros ou do município homônimo à fonte.

### API/XHR

Endpoint, método, parâmetros, paginação, JSON path e autenticação: `UNKNOWN`. Não inventar API nem enumerar IDs.

### Tecnologia

Tipo: `DNS_INACTIVE / UNKNOWN`. A consulta DNS direta encontrou `www.leandroferreira.com.br` inexistente; o domínio raiz retornou apenas o SOA da zona, sem endereço A utilizável. HTTP, JavaScript e Playwright não chegam à aplicação porque não há host web confirmado.

### Bloqueios

Bloqueio atual: `ERR_NAME_NOT_RESOLVED`/DNS. Isso é falha externa de identidade/transporte, não `EMPTY_EXPLICIT`. Não há alternativa oficial confirmada.

### Quality gate

ACEITAR somente após uma comunicação ou página de primeira parte comprovar o sucessor da mesma consultoria e oferecer processo seletivo de pessoal. REJEITAR coincidência nominal, portal municipal, agregadores e documentos históricos sem vínculo verificável com a fonte.

### Empty evidence

`UNKNOWN_EMPTY`. Nunca transformar a falha DNS em `active=0` ou “sem concursos”.

### Estratégia recomendada

`DEPRECATE_REVIEW_REQUIRED` + `KEEP_BLOCKED`. Preservar o identificador técnico por compatibilidade até decisão explícita; não criar parser especulativo e não substituir silenciosamente a URL.

### Instruções para Codex

1. Manter `leandroferreira_open` bloqueado e registrar a falha DNS.
2. Não apontar a fonte para `leandroferreira.mg.gov.br`.
3. Antes de qualquer alteração, exigir um domínio de primeira parte que prove continuidade da consultoria.
4. Se um sucessor for comprovado, refazer apenas a investigação dessa fonte e criar fixture/listagem/detalhe reais.
5. Testar que DNS indisponível resulta em `BLOCKED/UNKNOWN`, nunca em empty legítimo.

### Confidence

HIGH para a indisponibilidade e para a rejeição do portal municipal homônimo; LOW para a existência de sucessor, que permanece `UNKNOWN`.

### Evidências

- `https://www.leandroferreira.com.br` — host não resolvido na consulta de 30/08/2026.
- DNS direto de `www.leandroferreira.com.br` e `leandroferreira.com.br` — nenhum endereço web utilizável.
