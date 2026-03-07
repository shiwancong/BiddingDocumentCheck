"""
Agents模块
包含所有Agent的定义
"""

from .document_parser import DocumentParserAgent, ParsedDocument, Section, TableData
from .clause_identifier import ClauseIdentifierAgent, IdentifiedClause, ClauseType, CategoryType
from .quality_validator import QualityValidatorAgent, ValidationReport, ValidationSeverity

__all__ = [
    'DocumentParserAgent',
    'ParsedDocument',
    'Section',
    'TableData',
    'ClauseIdentifierAgent',
    'IdentifiedClause',
    'ClauseType',
    'CategoryType',
    'QualityValidatorAgent',
    'ValidationReport',
    'ValidationSeverity',
]
