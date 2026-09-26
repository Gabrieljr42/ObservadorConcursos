"""Record final batch plan before its bounded portal work begins."""
import json
from datetime import datetime,timezone
from pathlib import Path

def main():
    path=Path('../docs/tenderproof-rollout-plan.json')
    plan=json.loads(path.read_text(encoding='utf-8'))
    previous=next(b for b in plan['batches'] if b['cumulative_sources']==60)
    assert previous['gate']=='accepted_bounded_partial_scope_with_blocked_sources'
    batch=next(b for b in plan['batches'] if b['cumulative_sources']==99)
    groups={
        'organizers_and_verbena':['nossorumo_open','klc_open','oppus_open','legatus_open','fepese_open','ieses_open','verbena_selection'],
        'personnel_foundations':['funpec_selection','fade_selection','fapex_selection','fatec_selection','faped_selection','fapese_selection','fappr_selection','fapergs_selection'],
        'institutional_southeast_northeast':['fapemig_selection','fapes_selection','fapesq_selection','fapepi_selection','fapema_selection','fapece_selection','fapern_selection','fapeal_selection','facepe_selection','fapesb_selection','faperj_selection','fapesp_selection'],
        'institutional_other_regions':['fapesc_selection','fundect_selection','fapemat_selection','fapeg_selection','fapdf_selection','fapt_selection','fapeam_selection','fapespa_selection','fapeap_selection','faperr_selection','fapero_selection','fapac_selection']}
    assert set(sum(groups.values(),[]))==set(batch['sources']) and len(sum(groups.values(),[]))==39
    batch.update(gate='implementation_in_progress',started_at=datetime.now(timezone.utc).isoformat(),strategy_groups=groups,
        strategies='Reuse proven HTML/API transport and documentary contracts only after per-source evidence. Personnel foundations may expose CMS or dedicated HR portals; funding portals require explicit personnel selection routes. Technology markers alone do not justify shared adapters.',
        expected_adaptations='Public pagination/tabs, source-scoped identifiers, document association, official auxiliary hosts, and personnel-only item filters; preserve missing/ambiguous contracts.',
        known_dependencies='Public availability and valid TLS; Oppus challenge, FAPECE DNS, FAPERN HTTP failure, FAPEAP TLS and FAPESQ login redirect previously observed. Recheck official alternatives without bypass. Scholarship/funding opportunities cannot stand in for personnel selection.',
        validation_plan='Per-source bounded official captures plus contract tests; two acquisition cycles where an unambiguous original is accessible; explicitly controlled novelty, repeated continuous cycles, process recovery, mixed queue and isolated canonical review. Record absent in-scope samples separately from legitimate empty and extraction failure.',
        operational_limits={'html_bytes':2097152,'request_timeout_s':25,'pdf_bytes':31457280,'pdf_pages_default':60,'cycles':2,'listing_pages_per_sample':1,'detail_samples_per_cycle':3,'same_host_queue_workers':2,'retry_base_s_rehearsal':1,'browser_enabled':False,'paid_services':False,'production_enabled':False},
        scope='Personnel recruitment and employment-related selections only; exclude admissions, scholarships, grants, research funding, procurement and general calls. Preserve category and original ID; no count completion by out-of-scope data.')
    path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Batch99 preimplementation plan recorded:39 entries, four independent groups')

if __name__=='__main__':main()
