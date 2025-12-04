"""Clause Extraction Service using AI."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.clause import ClauseType, ExtractedClause, ClauseExtractionResult, RiskLevel
from app.services.ai.gemini_client import GeminiClient, get_gemini_client
from app.services.ai.prompts import (
    CLAUSE_EXTRACTION_PROMPT,
    CLAUSE_RISK_ANALYSIS_PROMPT,
    KEY_DATE_EXTRACTION_PROMPT,
)
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


class ClauseExtractor:
    """Service for extracting and analyzing contract clauses using AI."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.ai = gemini_client or get_gemini_client()

    async def extract_clauses(
        self,
        document_text: str,
        contract_id: int,
        document_id: int,
    ) -> ClauseExtractionResult:
        """
        Extract clauses from contract document text.

        Args:
            document_text: The contract text to analyze
            contract_id: ID of the contract
            document_id: ID of the source document

        Returns:
            ClauseExtractionResult with extracted clauses
        """
        start_time = datetime.utcnow()

        try:
            result = await self.ai.analyze_json(
                prompt=CLAUSE_EXTRACTION_PROMPT,
                data={"contract_text": document_text[:50000]},  # Limit text length
                system_instruction="You are a legal contract analyst specializing in clause extraction.",
            )

            clauses = []
            for clause_data in result.get("clauses", []):
                clause_type = self._map_clause_type(clause_data.get("clause_type", "other"))
                clauses.append(
                    ExtractedClause(
                        clause_type=clause_type,
                        title=clause_data.get("title", "Untitled"),
                        content=clause_data.get("content", ""),
                        section_reference=clause_data.get("section_reference"),
                        confidence=clause_data.get("confidence", 0.8),
                    )
                )

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return ClauseExtractionResult(
                contract_id=contract_id,
                document_id=document_id,
                total_clauses=len(clauses),
                clauses=clauses,
                extraction_timestamp=datetime.utcnow(),
                processing_time_seconds=processing_time,
            )

        except Exception as e:
            logger.error(f"Clause extraction failed: {e}")
            raise AIServiceError(
                "Failed to extract clauses from document",
                details={"error": str(e)},
            )

    def _map_clause_type(self, type_str: str) -> ClauseType:
        """Map string to ClauseType enum."""
        type_mapping = {
            "payment_terms": ClauseType.PAYMENT_TERMS,
            "payment": ClauseType.PAYMENT_TERMS,
            "delivery": ClauseType.DELIVERY,
            "warranty": ClauseType.WARRANTY,
            "liability": ClauseType.LIABILITY,
            "termination": ClauseType.TERMINATION,
            "confidentiality": ClauseType.CONFIDENTIALITY,
            "penalty": ClauseType.PENALTY,
            "renewal": ClauseType.RENEWAL,
            "force_majeure": ClauseType.FORCE_MAJEURE,
            "compliance": ClauseType.COMPLIANCE,
            "indemnification": ClauseType.INDEMNIFICATION,
            "intellectual_property": ClauseType.INTELLECTUAL_PROPERTY,
            "ip": ClauseType.INTELLECTUAL_PROPERTY,
            "dispute_resolution": ClauseType.DISPUTE_RESOLUTION,
            "dispute": ClauseType.DISPUTE_RESOLUTION,
            "governing_law": ClauseType.GOVERNING_LAW,
            "jurisdiction": ClauseType.GOVERNING_LAW,
        }
        return type_mapping.get(type_str.lower(), ClauseType.OTHER)

    async def analyze_clause_risk(
        self,
        clause_content: str,
        clause_type: str,
    ) -> Dict[str, Any]:
        """
        Analyze risk for a specific clause.

        Args:
            clause_content: The clause text
            clause_type: Type of the clause

        Returns:
            Risk analysis results
        """
        try:
            result = await self.ai.analyze_json(
                prompt=CLAUSE_RISK_ANALYSIS_PROMPT,
                data={
                    "clause_content": clause_content,
                    "clause_type": clause_type,
                },
                system_instruction="You are a legal risk analyst specializing in contract review.",
            )

            # Map risk level
            risk_level_str = result.get("risk_level", "medium").lower()
            risk_level_mapping = {
                "low": RiskLevel.LOW,
                "medium": RiskLevel.MEDIUM,
                "high": RiskLevel.HIGH,
                "critical": RiskLevel.CRITICAL,
            }
            result["risk_level"] = risk_level_mapping.get(risk_level_str, RiskLevel.MEDIUM)

            return result

        except Exception as e:
            logger.error(f"Clause risk analysis failed: {e}")
            raise AIServiceError(
                "Failed to analyze clause risk",
                details={"error": str(e)},
            )

    async def extract_key_dates(
        self,
        document_text: str,
    ) -> Dict[str, Any]:
        """
        Extract key dates from contract text.

        Args:
            document_text: The contract text

        Returns:
            Extracted dates and summary
        """
        try:
            return await self.ai.analyze_json(
                prompt=KEY_DATE_EXTRACTION_PROMPT,
                data={"contract_text": document_text[:30000]},
                system_instruction="You are a contract analyst specializing in deadline and date tracking.",
            )

        except Exception as e:
            logger.error(f"Date extraction failed: {e}")
            raise AIServiceError(
                "Failed to extract dates from document",
                details={"error": str(e)},
            )

    async def batch_analyze_clauses(
        self,
        clauses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple clauses for risk.

        Args:
            clauses: List of clause dictionaries with content and type

        Returns:
            List of clauses with risk analysis added
        """
        results = []
        for clause in clauses:
            try:
                analysis = await self.analyze_clause_risk(
                    clause_content=clause.get("content", ""),
                    clause_type=clause.get("clause_type", "other"),
                )
                results.append({
                    **clause,
                    "risk_analysis": analysis,
                })
            except Exception as e:
                logger.warning(f"Failed to analyze clause: {e}")
                results.append({
                    **clause,
                    "risk_analysis": None,
                    "analysis_error": str(e),
                })

        return results


def get_clause_extractor() -> ClauseExtractor:
    """Get clause extractor instance."""
    return ClauseExtractor()
