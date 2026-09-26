from __future__ import annotations

import logging
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.configurable import ConfigurableHTMLConnector, SourceDefinition
from app.connectors.dedicated import (
    ABCPConnector,
    AccessConnector,
    AOCPConnector,
    AvancaSPConnector,
    AvaliaConnector,
    CebraspeConnector,
    CesgranrioConnector,
    ConsulplanConnector,
    COTECConnector,
    CPConConnector,
    CONSEPOpenConnector,
    EPLOpenConnector,
    ExameConsultoresConnector,
    FAFIPAConnector,
    FCCConnector,
    FEPESEConnector,
    FGVConnector,
    FATECSelectionConnector,
    FumarcConnector,
    FUNVAPIConnector,
    FUNCERNConnector,
    IBADEConnector,
    IBAMConnector,
    IDECANConnector,
    IDIBConnector,
    IESESConnector,
    ADMTECConnector,
    LegatusConnector,
    NossoRumoConnector,
    ObjetivaConnector,
    OmniConnector,
    QuadrixConnector,
    UFUConnector,
    UniselvaAPIConnector,
    VerbenaConnector,
    EloOpenConnector,
    RBOOpenConnector,
)
from app.connectors.fundep import FundepAllConnector, FundepOpenConnector
from app.connectors.ibfc import IBFCOpenConnector
from app.connectors.ibgp import IBGPConnector
from app.connectors.imeso import IMESOAllConnector, IMESOOngoingConnector, IMESOOpenConnector
from app.connectors.institutional import InstitutionalSelectionConnector
from app.models import Source

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Catalog of All 99 Master Sources
# -----------------------------------------------------------------------------

MASTER_SOURCES: list[SourceDefinition] = [
    # 1. IBFC
    SourceDefinition(
        source_type='ibfc_open',
        name='IBFC - Inscrições Abertas',
        banca='IBFC',
        base_url='https://concursos.ibfc.org.br',
        list_urls=['https://concursos.ibfc.org.br/index/abertos/'],
        frequency_minutes=180,
    ),
    # 2. IDECAN
    SourceDefinition(
        source_type='idecan_open',
        name='IDECAN - Concursos',
        banca='IDECAN',
        base_url='https://portal.concursos.idecan.org.br',
        list_urls=['https://portal.concursos.idecan.org.br/edital/index/abertos'],
        frequency_minutes=240,
    ),
    # 3. Instituto AOCP
    SourceDefinition(
        source_type='aocp_open',
        name='Instituto AOCP - Concursos',
        banca='Instituto AOCP',
        base_url='https://www.institutoaocp.org.br',
        list_urls=['https://www.institutoaocp.org.br', 'https://www.institutoaocp.org.br/concursos.jsp'],
        frequency_minutes=240,
    ),
    # 4. CONSULPAM
    SourceDefinition(
        source_type='consulpam_open',
        name='CONSULPAM Concursos',
        banca='CONSULPAM',
        base_url='https://www.consulpam.com.br',
        list_urls=['https://www.consulpam.com.br/index.php?menu=concursos', 'https://consulpam.selecao.net.br/index/abertos/'],
        detail_url_patterns=[r'index\.php\?menu=concursos&acao=ver&id=\d+', r'/informacoes/\d+'],
        card_selectors=['table tr', '.concurso', '.item-concurso', '.card'],
        frequency_minutes=360,
    ),
    # 5. IBAM
    SourceDefinition(
        source_type='ibam_open',
        name='IBAM Concursos',
        banca='IBAM',
        base_url='https://www.ibam-concursos.org.br',
        list_urls=['https://www.ibam-concursos.org.br'],
        frequency_minutes=360,
    ),
    # 6. IBADE
    SourceDefinition(
        source_type='ibade_open',
        name='IBADE Concursos',
        banca='IBADE',
        base_url='https://portal.ibade.selecao.site',
        list_urls=['https://portal.ibade.selecao.site/edital'],
        frequency_minutes=360,
    ),
    # 7. CONSULPLAN / CONSULPLAN.NET
    SourceDefinition(
        source_type='consulplan_open',
        name='CONSULPLAN / Instituto Consulplan',
        banca='Instituto Consulplan',
        base_url='https://www.consulplan.net',
        list_urls=['https://www.consulplan.net', 'https://institutoconsulplan.org.br'],
        frequency_minutes=360,
    ),
    # 8. SEPROD
    SourceDefinition(
        source_type='seprod_open',
        name='SEPROD Concursos',
        banca='SEPROD',
        base_url='https://www.seprod.com.br',
        list_urls=['https://www.seprod.com.br/concursos/?utm_refererencia=em_andamento'],
        verify_ssl=False,
        frequency_minutes=360,
    ),
    # 9. FCC
    SourceDefinition(
        source_type='fcc_open',
        name='Fundação Carlos Chagas - FCC',
        banca='FCC',
        base_url='https://www.concursosfcc.com.br',
        list_urls=['https://www.concursosfcc.com.br/concursoAndamento.html'],
        frequency_minutes=360,
    ),
    # 10. FGV
    SourceDefinition(
        source_type='fgv_open',
        name='FGV Conhecimento Concursos',
        banca='FGV',
        base_url='https://conhecimento.fgv.br',
        list_urls=['https://conhecimento.fgv.br/concursos'],
        frequency_minutes=360,
    ),
    # 11. CEBRASPE / CESPE
    SourceDefinition(
        source_type='cebraspe_open',
        name='Cebraspe Concursos',
        banca='CEBRASPE',
        base_url='https://www.cebraspe.org.br',
        list_urls=['https://www.cebraspe.org.br/concursos/'],
        frequency_minutes=360,
    ),
    # 12. CESGRANRIO
    SourceDefinition(
        source_type='cesgranrio_open',
        name='Fundação Cesgranrio',
        banca='CESGRANRIO',
        base_url='https://www.cesgranrio.org.br',
        list_urls=['https://www.cesgranrio.org.br/concursos/'],
        frequency_minutes=360,
    ),
    # 13. IDCAP
    SourceDefinition(
        source_type='idcap_open',
        name='IDCAP Concursos',
        banca='IDCAP',
        base_url='https://www.idcap.org.br',
        list_urls=['https://www.idcap.org.br'],
        frequency_minutes=360,
    ),
    # 14. IBGP
    SourceDefinition(
        source_type='ibgp_open',
        name='IBGP - Inscrições Abertas',
        banca='IBGP',
        base_url='https://novo.ibgpconcursos.com.br',
        list_urls=['https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp'],
        frequency_minutes=180,
    ),
    # 15. FUNDEP
    SourceDefinition(
        source_type='fundep_open',
        name='FUNDEP - Gestão de Concursos',
        banca='FUNDEP',
        base_url='https://www.gestaodeconcursos.com.br',
        list_urls=['https://www.gestaodeconcursos.com.br/site/site/default.aspx'],
        frequency_minutes=360,
    ),
    # 16. FUMARC
    SourceDefinition(
        source_type='fumarc_open',
        name='FUMARC Concursos',
        banca='FUMARC',
        base_url='https://www.fumarc.com.br',
        list_urls=['https://www.fumarc.com.br/SitePages/Home.aspx'],
        verify_ssl=False,
        frequency_minutes=720,
    ),
    # 17. IMESO
    SourceDefinition(
        source_type='imeso_open',
        name='IMESO - Concursos e Seletivos',
        banca='IMESO',
        base_url='https://portal.imeso.com.br',
        list_urls=['https://portal.imeso.com.br/edital'],
        frequency_minutes=240,
    ),
    # 18. OMNI Concursos
    SourceDefinition(
        source_type='omni_open',
        name='OMNI Concursos Públicos',
        banca='OMNI Concursos',
        base_url='https://portal.omniconcursospublicos.com.br',
        list_urls=['https://portal.omniconcursospublicos.com.br'],
        frequency_minutes=360,
    ),
    # 19. ACCESS
    SourceDefinition(
        source_type='access_open',
        name='Instituto ACCESS',
        banca='Instituto ACCESS',
        base_url='https://access.selecao.net.br',
        list_urls=['https://access.selecao.net.br/index/abertos/'],
        frequency_minutes=360,
    ),
    # 20. EXAME Auditores
    SourceDefinition(
        source_type='exame_open',
        name='Exame Consultores e Auditores',
        banca='EXAME Auditores',
        base_url='https://concursos.exameconsultores.com.br',
        list_urls=['https://concursos.exameconsultores.com.br/index/1/'],
        frequency_minutes=360,
    ),
    # 21. EPL Concursos
    SourceDefinition(
        source_type='epl_open',
        name='EPL Concursos',
        banca='EPL Concursos',
        base_url='https://www.eplconcursos.com.br',
        list_urls=['https://www.eplconcursos.com.br'],
        frequency_minutes=360,
    ),
    # 22. ABCP
    SourceDefinition(
        source_type='abcp_open',
        name='ABCP Concursos',
        banca='ABCP',
        base_url='https://abcp.selecao.net.br',
        list_urls=['https://abcp.selecao.net.br/index/abertos/'],
        detail_url_patterns=[r'/informacoes/\d+/?'],
        frequency_minutes=360,
    ),
    # 23. UNIFIL
    SourceDefinition(
        source_type='unifil_open',
        name='Instituto UniFil',
        banca='UNIFIL',
        base_url='https://main.institutounifil.com.br',
        list_urls=['https://main.institutounifil.com.br'],
        frequency_minutes=360,
    ),
    # 24. OBJETIVA Concursos
    SourceDefinition(
        source_type='objetiva_open',
        name='OBJETIVA Concursos',
        banca='OBJETIVA Concursos',
        base_url='https://concursos.objetivas.com.br',
        list_urls=['https://concursos.objetivas.com.br'],
        frequency_minutes=360,
    ),
    # 25. Leandro Ferreira & Consultoria
    SourceDefinition(
        source_type='leandroferreira_open',
        name='Leandro Ferreira & Consultoria',
        banca='Leandro Ferreira Consultoria',
        base_url='https://www.leandroferreira.com.br',
        list_urls=['https://www.leandroferreira.com.br'],
        frequency_minutes=360,
    ),
    # 26. COTEC / FADENOR
    SourceDefinition(
        source_type='cotec_open',
        name='COTEC / FADENOR Concursos',
        banca='COTEC / FADENOR',
        base_url='https://www.cotec.fadenor.com.br',
        list_urls=['https://www.cotec.fadenor.com.br/index/abertos/'],
        frequency_minutes=360,
    ),
    # 27. Instituto Águia
    SourceDefinition(
        source_type='aguia_open',
        name='Instituto Águia Concursos',
        banca='Instituto Águia',
        base_url='https://portal.institutoaguia.org.br',
        list_urls=['https://portal.institutoaguia.org.br/edital'],
        frequency_minutes=360,
    ),
    # 28. IUDS
    SourceDefinition(
        source_type='iuds_open',
        name='IUDS Concursos',
        banca='IUDS',
        base_url='https://www.iuds.org.br',
        list_urls=['https://www.iuds.org.br'],
        frequency_minutes=360,
    ),
    # 29. Reis & Reis
    SourceDefinition(
        source_type='reisesreis_open',
        name='Reis & Reis Auditores Associados',
        banca='Reis & Reis',
        base_url='https://novo.reisauditores.com.br',
        list_urls=['https://novo.reisauditores.com.br/concursos-em-andamento'],
        frequency_minutes=360,
    ),
    # 30. MS Concursos
    SourceDefinition(
        source_type='msconcursos_open',
        name='MS Concursos',
        banca='MS Concursos',
        base_url='https://www.msconcursos.com.br',
        list_urls=['https://www.msconcursos.com.br'],
        frequency_minutes=360,
    ),
    # 31. FACET Concursos
    SourceDefinition(
        source_type='facet_open',
        name='FACET Concursos',
        banca='FACET Concursos',
        base_url='https://www.facetconcursos.com.br',
        list_urls=['https://www.facetconcursos.com.br'],
        frequency_minutes=360,
    ),
    # 32. EDUCA PB
    SourceDefinition(
        source_type='educapb_open',
        name='EDUCA PB Concursos',
        banca='EDUCA PB',
        base_url='https://www.educapb.com.br',
        list_urls=['https://www.educapb.com.br'],
        frequency_minutes=360,
    ),
    # 33. ADM&TEC
    SourceDefinition(
        source_type='admtec_open',
        name='Instituto ADM&TEC',
        banca='ADM&TEC',
        base_url='https://admtec.org.br',
        list_urls=['https://admtec.org.br/'],
        frequency_minutes=360,
    ),
    # 34. CONTEMAX
    SourceDefinition(
        source_type='contemax_open',
        name='CONTEMAX Consultoria',
        banca='CONTEMAX',
        base_url='https://www.contemaxconsultoria.com.br',
        list_urls=['https://www.contemaxconsultoria.com.br'],
        frequency_minutes=360,
    ),
    # 35. CPCon / UEPB
    SourceDefinition(
        source_type='cpcon_open',
        name='CPCon / UEPB Concursos',
        banca='CPCon / UEPB',
        base_url='https://cpcon.uepb.edu.br',
        list_urls=['https://cpcon.uepb.edu.br'],
        frequency_minutes=360,
    ),
    # 36. FUNVAPI
    SourceDefinition(
        source_type='funvapi_open',
        name='FUNVAPI Concursos',
        banca='FUNVAPI',
        base_url='https://www.funvapi.com.br',
        list_urls=['https://www.funvapi.com.br'],
        frequency_minutes=360,
    ),
    # 37. CONSEP
    SourceDefinition(
        source_type='consep_open',
        name='CONSEP - Consultoria e Estudos',
        banca='CONSEP',
        base_url='https://www.consep-pi.com.br',
        list_urls=['https://www.consep-pi.com.br'],
        frequency_minutes=360,
    ),
    # 38. Instituto Consulplan
    SourceDefinition(
        source_type='institutoconsulplan_open',
        name='Instituto Consulplan',
        banca='Instituto Consulplan',
        base_url='https://institutoconsulplan.azurewebsites.net',
        list_urls=['https://institutoconsulplan.azurewebsites.net/Concursos'],
        frequency_minutes=240,
    ),
    # 39. Instituto Avalia
    SourceDefinition(
        source_type='avalia_open',
        name='Instituto Avalia',
        banca='Instituto Avalia',
        base_url='https://www2.avalia.org.br',
        list_urls=['https://www2.avalia.org.br/concursos.jsp'],
        frequency_minutes=360,
    ),
    # 40. UFU / DIRPS
    SourceDefinition(
        source_type='ufu_selection',
        name='UFU / DIRPS - Seleções e Concursos',
        banca='UFU / DIRPS',
        base_url='https://www.portalselecao.ufu.br',
        list_urls=['https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos'],
        category='institutional_selection',
        frequency_minutes=360,
    ),
    # 41. IDGRAN
    SourceDefinition(
        source_type='idgran_open',
        name='IDGRAN Concursos',
        banca='IDGRAN',
        base_url='https://idgran.com.br',
        list_urls=['https://idgran.com.br'],
        frequency_minutes=360,
    ),
    # 42. Quadrix
    SourceDefinition(
        source_type='quadrix_open',
        name='Instituto Quadrix',
        banca='Quadrix',
        base_url='https://quadrix.org.br',
        list_urls=['https://quadrix.org.br/index/abertos/', 'https://quadrix.org.br/index/1/'],
        frequency_minutes=240,
    ),
    # 43. Gualimp
    SourceDefinition(
        source_type='gualimp_open',
        name='Gualimp Assessoria e Consultoria',
        banca='Gualimp',
        base_url='https://www.gualimp.com.br',
        list_urls=['https://www.gualimp.com.br'],
        frequency_minutes=360,
    ),
    # 44. Instituto Verbena / UFG
    SourceDefinition(
        source_type='verbena_selection',
        name='Instituto Verbena / UFG',
        banca='Instituto Verbena / UFG',
        base_url='https://institutoverbena.ufg.br',
        list_urls=['https://institutoverbena.ufg.br'],
        category='institutional_selection',
        frequency_minutes=360,
    ),
    # 45. IDIB
    SourceDefinition(
        source_type='idib_open',
        name='Instituto IDIB',
        banca='IDIB',
        base_url='https://idib.org.br',
        list_urls=['https://idib.org.br'],
        frequency_minutes=240,
    ),
    # 46. JCM Consultoria
    SourceDefinition(
        source_type='jcm_open',
        name='JCM Consultoria Municipal',
        banca='JCM Consultoria',
        base_url='https://eventos.concursosjcm.com.br',
        list_urls=['https://eventos.concursosjcm.com.br'],
        empty_state_patterns=[r'nenhum\s+item\s+cadastrado'],
        frequency_minutes=360,
    ),
    # 47. Elo Assessoria
    SourceDefinition(
        source_type='elo_open',
        name='Elo Assessoria e Serviços',
        banca='Elo Assessoria',
        base_url='https://eloassessoriaeservicos.com.br',
        list_urls=['https://eloassessoriaeservicos.com.br/concursos'],
        frequency_minutes=360,
    ),
    # 48. Apta Assessoria
    SourceDefinition(
        source_type='apta_open',
        name='Apta Concursos e Assessoria',
        banca='Apta Assessoria',
        base_url='https://www.aptaconcursos.com.br',
        list_urls=['https://www.aptaconcursos.com.br'],
        frequency_minutes=360,
    ),
    # 49. Legalle Concursos
    SourceDefinition(
        source_type='legalle_open',
        name='Legalle Concursos',
        banca='Legalle Concursos',
        base_url='https://portal.editais.legalleconcursos.com.br',
        list_urls=['https://portal.editais.legalleconcursos.com.br/edital'],
        frequency_minutes=360,
    ),
    # 50. RBO Assessoria
    SourceDefinition(
        source_type='rbo_open',
        name='RBO Concursos e Assessoria',
        banca='RBO Assessoria',
        base_url='https://rboconcursos.selecao.net.br',
        list_urls=['https://rboconcursos.selecao.net.br/index/abertos/'],
        detail_url_patterns=[r'/informacoes/\d+/?'],
        frequency_minutes=360,
    ),
    # 51. SHDias
    SourceDefinition(
        source_type='shdias_open',
        name='SHDias Consultoria e Concursos',
        banca='SHDias',
        base_url='https://www.shdias.com.br',
        list_urls=['https://www.shdias.com.br/concursos/'],
        frequency_minutes=360,
    ),
    # 52. Zambini
    SourceDefinition(
        source_type='zambini_open',
        name='Instituto Zambini',
        banca='Zambini',
        base_url='https://www.zambini.org.br',
        list_urls=['https://www.zambini.org.br/portal/concursos'],
        frequency_minutes=360,
    ),
    # 53. Nosso Rumo
    SourceDefinition(
        source_type='nossorumo_open',
        name='Instituto Nosso Rumo',
        banca='Nosso Rumo',
        base_url='https://www.nossorumo.org.br',
        list_urls=['https://www.nossorumo.org.br'],
        frequency_minutes=240,
    ),
    # 54. Avança SP
    SourceDefinition(
        source_type='avancasp_open',
        name='Avança SP Concursos',
        banca='Avança SP',
        base_url='https://avancasp.selecao.net.br',
        list_urls=['https://avancasp.selecao.net.br/index/abertos/'],
        frequency_minutes=240,
    ),
    # 55. Instituto Mais
    SourceDefinition(
        source_type='institutomais_open',
        name='Instituto Mais de Gestão e Concursos',
        banca='Instituto Mais',
        base_url='https://www.institutomais.org.br',
        list_urls=['https://www.institutomais.org.br/Concursos/ConcursosAbertos'],
        detail_url_patterns=[r'/Concursos/Detalhe/\d+'],
        # This official listing is already the "Concursos Abertos" scope;
        # detail pages contain historical dates that must not veto a row that
        # remains visibly listed there.
        mode='all',
        frequency_minutes=360,
    ),
    # 56. Publiconsult
    SourceDefinition(
        source_type='publiconsult_open',
        name='Publiconsult Concursos',
        banca='Publiconsult',
        base_url='https://publiconsult.com.br',
        list_urls=['https://publiconsult.com.br/Concurso/Index'],
        detail_url_patterns=[r'/Concurso/(?!Index)[^/?#]+', r'[?&](?:id|codigo)=\d+'],
        frequency_minutes=360,
    ),
    # 57. KLC Concursos
    SourceDefinition(
        source_type='klc_open',
        name='KLC Concursos',
        banca='KLC Concursos',
        base_url='https://www.klcconcursos.com.br',
        list_urls=['https://www.klcconcursos.com.br'],
        frequency_minutes=360,
    ),
    # 58. Sigma Assessoria
    SourceDefinition(
        source_type='sigma_open',
        name='Sigma Assessoria e Consultoria',
        banca='Sigma Assessoria',
        base_url='https://concursos.sigmaassessoria.com.br',
        list_urls=['https://concursos.sigmaassessoria.com.br'],
        frequency_minutes=360,
    ),
    # 59. W2 Auditores
    SourceDefinition(
        source_type='w2_open',
        name='W2 Auditores e Consultores',
        banca='W2 Auditores',
        base_url='https://www.w2consultores.com.br',
        list_urls=['https://www.w2consultores.com.br/index/todos/'],
        frequency_minutes=360,
    ),
    # 60. Fênix Concursos
    SourceDefinition(
        source_type='fenix_open',
        name='Fênix Concursos',
        banca='Fênix Concursos',
        base_url='https://portal.fenix.selecao.site',
        list_urls=['https://portal.fenix.selecao.site/edital'],
        detail_url_patterns=[r'/edital/ver/\d+'],
        frequency_minutes=360,
    ),
    # 61. Oppus Concursos
    SourceDefinition(
        source_type='oppus_open',
        name='Oppus Concursos',
        banca='Oppus Concursos',
        base_url='https://www.oppusconcursos.com.br',
        list_urls=['https://www.oppusconcursos.com.br'],
        frequency_minutes=360,
    ),
    # 62. Instituto Legatus
    SourceDefinition(
        source_type='legatus_open',
        name='Instituto Legatus',
        banca='Instituto Legatus',
        base_url='https://www.legatus.org.br',
        list_urls=['https://www.legatus.org.br'],
        frequency_minutes=360,
    ),
    # 63. FEPESE
    SourceDefinition(
        source_type='fepese_open',
        name='Fundação FEPESE',
        banca='FEPESE',
        base_url='https://fepese.org.br',
        list_urls=['https://fepese.org.br/concursos/'],
        frequency_minutes=360,
    ),
    # 64. FUNCERN
    SourceDefinition(
        source_type='funcern_selection',
        name='FUNCERN Concursos e Seleções',
        banca='FUNCERN',
        base_url='https://funcern.br',
        list_urls=['https://funcern.br/concursos/'],
        category='institutional_selection',
        frequency_minutes=360,
    ),
    # 65. FAPEMIG
    SourceDefinition(
        source_type='fapemig_selection',
        name='FAPEMIG - Seleções de Pessoal e Editais',
        banca='FAPEMIG',
        base_url='https://fapemig.br',
        list_urls=['https://fapemig.br/pt/editais/'],
        category='institutional_selection',
        default_uf='MG',
        default_orgao='FAPEMIG',
        frequency_minutes=720,
    ),
    # 66. FAPES
    SourceDefinition(
        source_type='fapes_selection',
        name='FAPES (Espírito Santo) - Seleções',
        banca='FAPES',
        base_url='https://fapes.es.gov.br',
        list_urls=['https://fapes.es.gov.br/editais'],
        category='institutional_selection',
        default_uf='ES',
        default_orgao='FAPES',
        frequency_minutes=720,
    ),
    # 67. FAPESQ
    SourceDefinition(
        source_type='fapesq_selection',
        name='FAPESQ (Paraíba) - Seleções',
        banca='FAPESQ',
        base_url='https://fapesq.rpp.br',
        list_urls=['https://fapesq.rpp.br/editais/'],
        category='institutional_selection',
        default_uf='PB',
        default_orgao='FAPESQ',
        frequency_minutes=720,
    ),
    # 68. Fundação Uniselva
    SourceDefinition(
        source_type='uniselva_selection',
        name='Fundação Uniselva - Processos Seletivos',
        banca='Fundação Uniselva',
        base_url='https://inscricao.fundacaouniselva.org.br',
        list_urls=['https://inscricao.fundacaouniselva.org.br/selecoes'],
        category='institutional_selection',
        default_uf='MT',
        default_cidade='Cuiabá',
        default_orgao='Fundação Uniselva',
        frequency_minutes=720,
    ),
    # 69. Fundação FAFIPA
    SourceDefinition(
        source_type='fafipa_open',
        name='Fundação de Apoio à FAFIPA',
        banca='Fundação FAFIPA',
        base_url='https://concursos.fundacaofafipa.org.br',
        list_urls=['https://concursos.fundacaofafipa.org.br/'],
        frequency_minutes=360,
    ),
    # 70. IESES
    SourceDefinition(
        source_type='ieses_open',
        name='Instituto IESES',
        banca='IESES',
        base_url='https://ieses.org',
        list_urls=['https://ieses.org/projetos'],
        frequency_minutes=360,
    ),
    # 71. FUNPEC
    SourceDefinition(
        source_type='funpec_selection',
        name='FUNPEC - Processos Seletivos',
        banca='FUNPEC',
        base_url='https://funpec.br',
        list_urls=['https://funpec.br/processos-seletivos/'],
        category='institutional_selection',
        default_uf='RN',
        default_cidade='Natal',
        default_orgao='FUNPEC',
        frequency_minutes=720,
    ),
    # 72. FADE
    SourceDefinition(
        source_type='fade_selection',
        name='FADE - Fundação de Apoio ao Desenvolvimento',
        banca='FADE',
        base_url='https://fade.org.br',
        list_urls=['https://fade.org.br'],
        category='institutional_selection',
        frequency_minutes=720,
    ),
    # 73. FAPEX
    SourceDefinition(
        source_type='fapex_selection',
        name='FAPEX - Fundação de Apoio à Pesquisa e Extensão',
        banca='FAPEX',
        base_url='https://fapex.org.br',
        list_urls=['https://master.fapex.org.br/portalrh/'],
        category='institutional_selection',
        frequency_minutes=720,
    ),
    # 74. FATEC
    SourceDefinition(
        source_type='fatec_selection',
        name='FATEC - Fundação de Apoio',
        banca='FATEC',
        base_url='https://www.fatecsm.org.br',
        list_urls=['https://www.fatecsm.org.br/processos-seletivos/'],
        category='institutional_selection',
        frequency_minutes=720,
    ),
    # 75. FAPED
    SourceDefinition(
        source_type='faped_selection',
        name='FAPED - Fundação de Apoio',
        banca='FAPED',
        base_url='https://faped.org.br',
        list_urls=['https://faped.org.br'],
        category='institutional_selection',
        frequency_minutes=720,
    ),
    # 76. FAPESE
    SourceDefinition(
        source_type='fapese_selection',
        name='FAPESE - Fundação de Apoio à Extensão e Pesquisa',
        banca='FAPESE',
        base_url='https://fapese.org.br',
        list_urls=['https://fapese.org.br'],
        category='institutional_selection',
        frequency_minutes=720,
    ),
    # 77. FAPEPI
    SourceDefinition(
        source_type='fapepi_selection',
        name='FAPEPI (Piauí) - Seleções',
        banca='FAPEPI',
        base_url='https://www.fapepi.pi.gov.br',
        list_urls=['https://www.fapepi.pi.gov.br/editais-fapepi/'],
        category='institutional_selection',
        default_uf='PI',
        frequency_minutes=720,
    ),
    # 78. FAPEMA
    SourceDefinition(
        source_type='fapema_selection',
        name='FAPEMA (Maranhão) - Seleções',
        banca='FAPEMA',
        base_url='https://www.fapema.br',
        list_urls=['https://www.fapema.br/inicio/'],
        category='institutional_selection',
        default_uf='MA',
        frequency_minutes=720,
    ),
    # 79. FUNCAP — preserve the legacy source key used by the inventory.
    SourceDefinition(
        source_type='fapece_selection',
        name='FUNCAP (Ceará) - Seleções',
        banca='FUNCAP',
        base_url='https://www.ce.gov.br/funcap/',
        list_urls=['https://montenegro.funcap.ce.gov.br/sugba/editais-site-wordpress/'],
        category='institutional_selection',
        default_uf='CE',
        frequency_minutes=720,
    ),
    # 80. FAPERN
    SourceDefinition(
        source_type='fapern_selection',
        name='FAPERN (Rio Grande do Norte) - Seleções',
        banca='FAPERN',
        base_url='https://fapern.rn.gov.br',
        list_urls=['https://fapern.rn.gov.br'],
        category='institutional_selection',
        default_uf='RN',
        frequency_minutes=720,
    ),
    # 81. FAPEAL
    SourceDefinition(
        source_type='fapeal_selection',
        name='FAPEAL (Alagoas) - Seleções',
        banca='FAPEAL',
        base_url='https://fapeal.br',
        list_urls=['https://fapeal.br'],
        category='institutional_selection',
        default_uf='AL',
        frequency_minutes=720,
    ),
    # 82. FACEPE
    SourceDefinition(
        source_type='facepe_selection',
        name='FACEPE (Pernambuco) - Seleções',
        banca='FACEPE',
        base_url='https://www.facepe.br',
        list_urls=['https://www.facepe.br'],
        category='institutional_selection',
        default_uf='PE',
        frequency_minutes=720,
    ),
    # 83. FAPESB
    SourceDefinition(
        source_type='fapesb_selection',
        name='FAPESB (Bahia) - Seleções',
        banca='FAPESB',
        base_url='https://fapesb.ba.gov.br',
        list_urls=['https://www.fapesb.ba.gov.br/category/edital/'],
        category='institutional_selection',
        default_cidade='Salvador',
        default_uf='BA',
        frequency_minutes=720,
    ),
    # 84. FAPERJ
    SourceDefinition(
        source_type='faperj_selection',
        name='FAPERJ (Rio de Janeiro) - Seleções',
        banca='FAPERJ',
        base_url='https://faperj.br',
        list_urls=['https://faperj.br'],
        category='institutional_selection',
        default_cidade='Rio de Janeiro',
        default_uf='RJ',
        frequency_minutes=720,
    ),
    # 85. FAPESP
    SourceDefinition(
        source_type='fapesp_selection',
        name='FAPESP (São Paulo) - Oportunidades e Seleções',
        banca='FAPESP',
        base_url='https://fapesp.br',
        list_urls=['https://fapesp.br/oportunidades/'],
        category='institutional_selection',
        default_cidade='São Paulo',
        default_uf='SP',
        frequency_minutes=720,
    ),
    # 86. FAPPR
    SourceDefinition(
        source_type='fappr_selection',
        name='Fundação Araucária / FAPPR (Paraná)',
        banca='FAPPR',
        base_url='https://fappr.pr.gov.br',
        list_urls=['https://fappr.pr.gov.br/Pagina/Processos-Seletivos'],
        category='institutional_selection',
        default_cidade='Curitiba',
        default_uf='PR',
        frequency_minutes=720,
    ),
    # 87. FAPESC
    SourceDefinition(
        source_type='fapesc_selection',
        name='FAPESC (Santa Catarina) - Seleções',
        banca='FAPESC',
        base_url='https://fapesc.sc.gov.br',
        list_urls=['https://fapesc.sc.gov.br'],
        category='institutional_selection',
        default_cidade='Florianópolis',
        default_uf='SC',
        frequency_minutes=720,
    ),
    # 88. FAPERGS
    SourceDefinition(
        source_type='fapergs_selection',
        name='FAPERGS (Rio Grande do Sul) - Seleções',
        banca='FAPERGS',
        base_url='https://fapergs.rs.gov.br',
        list_urls=['https://fapergs.rs.gov.br/selecao-2025'],
        category='institutional_selection',
        default_cidade='Porto Alegre',
        default_uf='RS',
        frequency_minutes=720,
    ),
    # 89. FUNDECT
    SourceDefinition(
        source_type='fundect_selection',
        name='FUNDECT (Mato Grosso do Sul) - Seleções',
        banca='FUNDECT',
        base_url='https://www.fundect.ms.gov.br',
        list_urls=['https://www.fundect.ms.gov.br/informativos/consultas/'],
        category='institutional_selection',
        default_cidade='Campo Grande',
        default_uf='MS',
        frequency_minutes=720,
    ),
    # 90. FAPEMAT
    SourceDefinition(
        source_type='fapemat_selection',
        name='FAPEMAT (Mato Grosso) - Seleções',
        banca='FAPEMAT',
        base_url='https://fapemat.mt.gov.br',
        list_urls=['https://fapemat.mt.gov.br'],
        category='institutional_selection',
        default_cidade='Cuiabá',
        default_uf='MT',
        frequency_minutes=720,
    ),
    # 91. FAPEG
    SourceDefinition(
        source_type='fapeg_selection',
        name='FAPEG (Goiás) - Seleções',
        banca='FAPEG',
        base_url='https://goias.gov.br/fapeg',
        list_urls=[
            'https://goias.gov.br/administracao/processos-seletivos-simplificados/',
            'https://goias.gov.br/fapeg/editais/inscricoes-abertas/',
            'https://goias.gov.br/fapeg/editais/em-andamento/',
            'https://goias.gov.br/fapeg/editais/encerrados/',
        ],
        category='institutional_selection',
        default_cidade='Goiânia',
        default_uf='GO',
        frequency_minutes=720,
    ),
    # 92. FAPDF
    SourceDefinition(
        source_type='fapdf_selection',
        name='FAPDF (Distrito Federal) - Seleções',
        banca='FAPDF',
        base_url='https://fap.df.gov.br',
        list_urls=['https://fap.df.gov.br'],
        category='institutional_selection',
        default_cidade='Brasília',
        default_uf='DF',
        frequency_minutes=720,
    ),
    # 93. FAPT
    SourceDefinition(
        source_type='fapt_selection',
        name='FAPT (Tocantins) - Seleções',
        banca='FAPT',
        base_url='https://fapt.to.gov.br',
        list_urls=['https://fapt.to.gov.br'],
        category='institutional_selection',
        default_cidade='Palmas',
        default_uf='TO',
        frequency_minutes=720,
    ),
    # 94. FAPEAM
    SourceDefinition(
        source_type='fapeam_selection',
        name='FAPEAM (Amazonas) - Seleções',
        banca='FAPEAM',
        base_url='https://fapeam.am.gov.br',
        list_urls=['https://fapeam.am.gov.br'],
        category='institutional_selection',
        default_cidade='Manaus',
        default_uf='AM',
        frequency_minutes=720,
    ),
    # 95. FAPESPA
    SourceDefinition(
        source_type='fapespa_selection',
        name='FAPESPA (Pará) - Seleções',
        banca='FAPESPA',
        base_url='https://fapespa.pa.gov.br',
        list_urls=['https://fapespa.pa.gov.br'],
        category='institutional_selection',
        default_cidade='Belém',
        default_uf='PA',
        frequency_minutes=720,
    ),
    # 96. FAPEAP
    SourceDefinition(
        source_type='fapeap_selection',
        name='FAPEAP (Amapá) - Seleções',
        banca='FAPEAP',
        base_url='https://fapeap.ap.gov.br',
        list_urls=['https://fapeap.ap.gov.br'],
        category='institutional_selection',
        default_cidade='Macapá',
        default_uf='AP',
        frequency_minutes=720,
    ),
    # 97. FAPERR
    SourceDefinition(
        source_type='faperr_selection',
        name='FAPERR (Roraima) - Seleções',
        banca='FAPERR',
        base_url='https://faperr.rr.gov.br',
        list_urls=['https://faperr.rr.gov.br'],
        category='institutional_selection',
        default_cidade='Boa Vista',
        default_uf='RR',
        frequency_minutes=720,
    ),
    # 98. FAPERO
    SourceDefinition(
        source_type='fapero_selection',
        name='FAPERO (Rondônia) - Seleções',
        banca='FAPERO',
        base_url='https://rondonia.ro.gov.br/fapero',
        list_urls=['https://rondonia.ro.gov.br/fapero/publicacoes/'],
        category='institutional_selection',
        default_cidade='Porto Velho',
        default_uf='RO',
        frequency_minutes=720,
    ),
    # 99. FAPAC
    SourceDefinition(
        source_type='fapac_selection',
        name='FAPAC (Acre) - Seleções',
        banca='FAPAC',
        base_url='https://fapac.ac.gov.br',
        list_urls=['https://fapac.ac.gov.br'],
        category='institutional_selection',
        default_cidade='Rio Branco',
        default_uf='AC',
        frequency_minutes=720,
    ),
]

DEFINITIONS_BY_SOURCE_TYPE: dict[str, SourceDefinition] = {d.source_type: d for d in MASTER_SOURCES}

DEDICATED_CLASSES: dict[str, type] = {
    'ibfc_open': IBFCOpenConnector,
    'imeso_open': IMESOOpenConnector,
    'imeso_ongoing': IMESOOngoingConnector,
    'imeso_all': IMESOAllConnector,
    'fundep_open': FundepOpenConnector,
    'fundep_all': FundepAllConnector,
    'ibgp_open': IBGPConnector,
    'ibgp_ongoing': IBGPConnector,
    'idecan_open': IDECANConnector,
    'consulplan_open': ConsulplanConnector,
    'institutoconsulplan_open': ConsulplanConnector,
    'aocp_open': AOCPConnector,
    'fumarc_open': FumarcConnector,
    'fcc_open': FCCConnector,
    'fgv_open': FGVConnector,
    'cebraspe_open': CebraspeConnector,
    'cesgranrio_open': CesgranrioConnector,
    'ibam_open': IBAMConnector,
    'ibade_open': IBADEConnector,
    'quadrix_open': QuadrixConnector,
    'idib_open': IDIBConnector,
    'fepese_open': FEPESEConnector,
    'ieses_open': IESESConnector,
    'uniselva_selection': UniselvaAPIConnector,
    'fafipa_open': FAFIPAConnector,
    'cotec_open': COTECConnector,
    'ufu_selection': UFUConnector,
    'cpcon_open': CPConConnector,
    'funvapi_open': FUNVAPIConnector,
    'consep_open': CONSEPOpenConnector,
    'epl_open': EPLOpenConnector,
    'exame_open': ExameConsultoresConnector,
    'admtec_open': ADMTECConnector,
    'funcern_selection': FUNCERNConnector,
    'verbena_selection': VerbenaConnector,
    'avalia_open': AvaliaConnector,
    'omni_open': OmniConnector,
    'access_open': AccessConnector,
    'abcp_open': ABCPConnector,
    'objetiva_open': ObjetivaConnector,
    'legatus_open': LegatusConnector,
    'avancasp_open': AvancaSPConnector,
    'nossorumo_open': NossoRumoConnector,
    'elo_open': EloOpenConnector,
    'rbo_open': RBOOpenConnector,
    'fatec_selection': FATECSelectionConnector,
}


def get_connector(source_type: str, base_url: str | None = None, list_url: str | None = None):
    """Connector factory for any of the 99 registered sources."""
    # 1. Check dedicated connector class
    dedicated_cls = DEDICATED_CLASSES.get(source_type)
    if dedicated_cls:
        if base_url:
            return dedicated_cls(base_url=base_url, list_url=list_url)
        definition = DEFINITIONS_BY_SOURCE_TYPE.get(source_type)
        return dedicated_cls(
            base_url=definition.base_url if definition else 'https://example.com',
            list_url=list_url or (definition.list_urls[0] if definition and definition.list_urls else None),
        )

    # 2. Check configurable/institutional definition
    definition = DEFINITIONS_BY_SOURCE_TYPE.get(source_type)
    if definition:
        if definition.category == 'institutional_selection':
            return InstitutionalSelectionConnector(definition, base_url=base_url, list_url=list_url)
        return ConfigurableHTMLConnector(definition, base_url=base_url, list_url=list_url)

    # 3. Fallback generic
    raise ValueError(f'Tipo de fonte não registrado no catálogo: {source_type}')


def seed_master_sources(db: Session) -> dict[str, int]:
    """Idempotently ensure all 99 master sources are seeded into PostgreSQL."""
    created = 0
    updated = 0
    unchanged = 0

    for defn in MASTER_SOURCES:
        primary_list_url = defn.list_urls[0] if defn.list_urls else defn.base_url
        existing = db.execute(
            select(Source).where(Source.source_type == defn.source_type)
        ).scalar_one_or_none()

        if existing is None:
            source = Source(
                name=defn.name,
                base_url=defn.base_url,
                list_url=primary_list_url,
                source_type=defn.source_type,
                active=True,
                frequency_minutes=defn.frequency_minutes,
            )
            db.add(source)
            created += 1
        else:
            changed = False
            if existing.name != defn.name:
                existing.name = defn.name
                changed = True
            if existing.base_url != defn.base_url:
                existing.base_url = defn.base_url
                changed = True
            if existing.list_url != primary_list_url:
                existing.list_url = primary_list_url
                changed = True
            if existing.frequency_minutes != defn.frequency_minutes:
                existing.frequency_minutes = defn.frequency_minutes
                changed = True
            if changed:
                updated += 1
            else:
                unchanged += 1

    db.commit()
    return {
        'total_master_sources': len(MASTER_SOURCES),
        'created': created,
        'updated': updated,
        'unchanged': unchanged,
    }
