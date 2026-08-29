from app.connectors.base import BaseConnector, CandidateItem, CrawlResult, CrawlRunData
from app.connectors.configurable import ConfigurableHTMLConnector, SourceDefinition
from app.connectors.institutional import InstitutionalSelectionConnector
from app.connectors.registry import MASTER_SOURCES, get_connector, seed_master_sources

__all__ = [
    'BaseConnector',
    'CandidateItem',
    'CrawlResult',
    'CrawlRunData',
    'ConfigurableHTMLConnector',
    'SourceDefinition',
    'InstitutionalSelectionConnector',
    'MASTER_SOURCES',
    'get_connector',
    'seed_master_sources',
]
