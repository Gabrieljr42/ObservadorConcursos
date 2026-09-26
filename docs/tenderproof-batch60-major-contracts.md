# Lote60 — IBAM, FCC, Cebraspe, Cesgranrio e Avalia

Capturas oficiais de 08/09/2026, hashes e limites em
`tenderproof-batch60-major-validation.json`. Cinco contratos implementados, sem
homologação integral. IBAM375, FCCabgfg126, CebraspeADEAL_26 e Avalia631 validaram
PDFs em dois ciclos HTTP pelo serviço comum. Cesgranrio27 baixou o mesmo original
em dois ciclos, recusou81p sob o limite padrão60 e validou localmente com limite100,
sem novo download. Cada ciclo preserva origem e hash dos bytes.

## Contratos e identidade

- IBAM: a página única apresenta cartões, IDs `docs-375` e controles com
  `data-bs-target="#docs-375"`. A URL usa esse fragmento observado sobre a própria
  página; o HTTP continua buscando a mesma página. Documentos ficam restritos ao
  cartão correto e título corroborado. IDs duplicados são excluídos com diagnóstico.
  Não são inventados endpoints de detalhe. `/documento/*.pdf` tem nomes opacos;
  associação definitiva exige revalidação do PDF, não apenas o nome do arquivo.
- FCC: `.textoInstituicao2` identifica título; o texto do concurso vizinho exclui
  vestibulares mesmo quando o nome da instituição não os identifica. Detalhe e
  PDF devem compartilhar o slug. O parâmetro `file` de
  `/rybena/web/index.html` contém a URL PDF efetivamente observada. Nenhum outro
  parâmetro é aceito. Reabertura, prorrogação e retificação não viram original.
- Avalia: identidade `concurso.jsp?id=` e título `h5.card-title`; PDFs no host
  oficial `arquivos-site.avalia.org.br/publicacoes/{UUID}.pdf`. O prefixo de data
  é separado do rótulo documental.634/621 declaram ausência de publicações;
 631 contém original e anexos. Fomento e Ganhe o Mundo ficam excluídos.
- Cebraspe: API pública, JSON estrutural e diretório CDN por evento. A resposta
  histórica tem duas entradas INSS_22 com IDs internos diferentes: ambas ficam
  excluídas, com diagnóstico e cobertura parcial, sem fusão automática.
- Cesgranrio: listagem pública paginada, conteúdos públicos por evento e PDF em
  `/media/gpoweb-prd-hibrido3/eventos/{ID}/conteudos/{UUID}.pdf`. O campo `eventoId`
  dos conteúdos repete IDs dos próprios conteúdos, portanto não é usado como
  vínculo. URL requisitada e diretório do evento vinculam o detalhe ao candidato;
  o PDF confirma a identidade textual. Políticas de ética não são editais.

## Proveniência das fórmulas de API e documentos

O HTML Cebraspe contém `/concursos/static/js/main.68af135b.chunk.js`, capturado
como `cebraspe-main.js`. O objeto de configuração declara
`eventoURL=https://apis.cebraspe.org.br/cebraspe/eventos`, `basename=/concursos/`
e `cdnLink=https://cdn.cebraspe.org.br/`. `componentDidMount` concatena
`eventoURL + /tipo + basename`; o detalhe concatena `eventoURL + / + identificador`.
`renderLink` usa, para PDFs nãoGUID, `cdnLink + tipoEvento + / + identificador +
/arquivos/ + nomeArquivo`. Todas essas fórmulas foram lidas antes da aquisição.
As variantes GUID e HTTP legado não foram autorizadas por esse contrato.

O detalhe institucional Cesgranrio SEMA aponta `/portal/avaliacoes/27`. A página
Angular tem `<base href="/">` e `main.1715d0bd4a4503a5.js`. A tentativa relativa
a `/portal/` retornou404 e permanece no manifesto. O bundle correto ultrapassou
2MiB; a investigação foi ampliada explicitamente para8MiB somenteJavaScript,
capturando5.358.238bytes. HTML permanece2MiB e PDF30MiB.

No bundle, `EventoService` declara `path="PortalEventos"` e faz GET em
`/api/${path}` com parâmetros da tela `nome`, `status`, `page`, `pageSize=10`.
`AvaliacaoDetalhePageComponent` usa o ID da rota para `obterEvento` e, sem login,
`obterEventoConteudosPublico`, definido como
`/api/PortalEventoConteudos/publico/${eventoId}`. A tela extrai links de `texto`
e usa `titulo` como rótulo. Somente esses mecanismos públicos foram utilizados.

SAS Azure observada: `sv,se,sr,sp,sig`, com `sr=c` e `sp=r`. O contrato aceita
apenas essas chaves, host e diretório exatos; IDs documentais ignoram a assinatura.
As fixtures/relatórios removem queries assinadas e distinguem hash original do
hash da representação sanitizada. Nenhum login ou comunicação externa ocorreu.

## Provas e limites

27 testes específicos passaram em `batch60-major-contracts-final.xml`; a regressão
anterior combinada com piloto/portais próprios passou131 testes antes da adição
do contrato Cesgranrio e dos últimos casos de duplicidade/SAS. Não se usa esse
número antigo como regressão final da integração.

Publicação canônica, replay contínuo completo e estabilidade das assinaturas
Azure no manifesto contínuo são provas separadas coordenadas pelo agente raiz.
Os ensaios aqui não alegam cobertura integral nem aquisição dos bytes de todos
os anexos e retificações. O padrão de60p permanece inalterado.
