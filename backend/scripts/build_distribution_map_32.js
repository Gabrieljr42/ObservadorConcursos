const fs = require('fs');
const apiPath = 'backend/.tenderproof/product-completion/delivery-api-current-20260912T195115192916Z.json';
const indexPath = 'backend/.tenderproof/product-completion/T004-INDICE-DOCUMENTOS-32-runtime-compact.json';
const outJson = 'docs/T004-DISTRIBUICAO-32-20260912.json';
const outMd = 'docs/T004-DISTRIBUICAO-32-20260912.md';
const fields = ['cidade','uf','cargos','vagas','salario_min','salario_max','taxa','escolaridade','prova_data'];
const knownRunners = {
  3: 'backend/scripts/delivery_apply_pedrinhas.py',
  30: 'backend/scripts/ibam_caruaru_proposal.py'
};
const api = JSON.parse(fs.readFileSync(apiPath, 'utf8'));
const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
const byId = new Map(index.records.map(r => [r.concurso_id, r]));
const rows = api.catalogue.map(c => {
  const r = byId.get(c.id) || {};
  const missing = fields.filter(f => c[f] === null || c[f] === undefined || c[f] === '' || (f === 'cargos' && !Array.isArray(c[f])));
  const runner = knownRunners[c.id] || null;
  return {
    id: c.id,
    source: r.source || 'unknown_in_runtime_index',
    title: c.titulo,
    missing_fields_api: missing,
    cargos_count_api: Array.isArray(c.cargos) ? c.cargos.length : null,
    runner_ready: Boolean(runner),
    runner,
    run_id: r.run_id || null,
    artifact_sha256: r.artifact_sha256 || null,
    artifact_path: r.artifact_path || null,
    lookup_status: r.lookup_status || 'not_indexed',
    evidence: r.evidence || null,
    document_status: r.document_status || 'not_proven_in_index',
    distribution_note: c.id === 11 ? 'Maranguape: 43 cargos já estruturados; runner de conteúdo específico não identificado neste índice.' : c.id === 3 ? 'Localidade comprovada em revisão T005; cidade/UF ainda ausentes na API.' : c.id === 4 ? 'Localidade comprovada em revisão T005; cidade/UF ainda ausentes na API.' : c.id === 2 ? 'Ibiúna permanece bloqueado por numeração documental conflitante.' : ''
  };
}).sort((a,b) => a.id - b.id);
const result = {
  schema_version: 1,
  generated_at: new Date().toISOString(),
  api_snapshot: apiPath,
  api_at: api.at,
  runtime_index: indexPath,
  counts: {
    records: rows.length,
    without_cargos_in_api: rows.filter(r => r.cargos_count_api === null).length,
    without_locality_in_api: rows.filter(r => r.missing_fields_api.includes('cidade') || r.missing_fields_api.includes('uf')).length,
    runners_ready: rows.filter(r => r.runner_ready).length,
    runtime_lookup_found: rows.filter(r => r.lookup_status === 'found').length,
    runtime_lookup_not_found: rows.filter(r => r.lookup_status === 'lookup_not_found').length
  },
  interpretation: 'missing_fields_api descreve o snapshot API e não prova ausência na fonte. runner_ready só é true quando um runner de conteúdo preservado foi identificado. ID 12 teve lookup runtime não encontrado; IDs 3/4 possuem evidência de localidade indicada pela revisão T005.',
  records: rows
};
fs.writeFileSync(outJson, JSON.stringify(result, null, 2) + '\n');
const lines = [
  '# T004 — distribuição dos 32 registros (12/09/2026)',
  '',
  `Snapshot API: \`${apiPath}\` (${api.at}). Índice runtime: \`${indexPath}\`.`,
  '',
  `Contagens: ${result.counts.records} registros; ${result.counts.without_cargos_in_api} sem cargos no API; ${result.counts.without_locality_in_api} sem cidade/UF no API; ${result.counts.runners_ready} runners específicos identificados; runtime ${result.counts.runtime_lookup_found}/${result.counts.records} encontrados (ID 12 não encontrado).`,
  '',
  '| ID | fonte | campos faltantes no API | cargos | runner pronto | run/artifact | nota |',
  '|---:|---|---|---:|---|---|---|',
  ...rows.map(r => `| ${r.id} | ${r.source} | ${r.missing_fields_api.join(', ') || '—'} | ${r.cargos_count_api ?? 'N/I'} | ${r.runner_ready ? '`' + r.runner + '`' : 'não identificado'} | ${r.run_id ? '`' + r.run_id + '` / `' + r.artifact_sha256.slice(0,12) + '…`' : 'lookup não encontrado'} | ${r.distribution_note || '—'} |`),
  '',
  'A classificação de lacunas é limitada ao retorno atual da API: “ausente no API” continua distinto de ausente na fonte ou falha de extração. O próximo trabalho deve reservar grupos disjuntos e conferir documentos pelos SHA/caminhos do índice antes de qualquer proposta.'
];
fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(JSON.stringify(result.counts));
