"""
LangChain-based Contract Analysis Client.

This module replaces the direct Google Gemini integration with LangChain,
providing structured output parsing with Pydantic models and better
error handling for contract analysis.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


# ==================== Pydantic Output Models ====================

class PartyInfo(BaseModel):
    """Party information in a contract"""
    name: str = Field(description="Party name")
    role: str = Field(description="Role in the contract (e.g., buyer, seller, provider)")


class ObligationInfo(BaseModel):
    """Obligation information"""
    party: str = Field(description="Party responsible")
    obligation: str = Field(description="Description of the obligation")


class FinancialTerms(BaseModel):
    """Financial terms structure"""
    value: Optional[str] = Field(default=None, description="Contract value")
    currency: Optional[str] = Field(default=None, description="Currency")
    payment_schedule: Optional[str] = Field(default=None, description="Payment schedule")
    penalties: Optional[str] = Field(default=None, description="Penalty terms")


class ImportantDate(BaseModel):
    """Important date in contract"""
    type: str = Field(description="Type of date (start, end, milestone, etc.)")
    date: str = Field(description="Date value or description")
    description: str = Field(description="What this date represents")


class RiskInfo(BaseModel):
    """Risk information"""
    level: str = Field(description="Risk level (low, medium, high, critical)")
    description: str = Field(description="Risk description")
    mitigation: Optional[str] = Field(default=None, description="Mitigation strategy")


class ContractAnalysisResult(BaseModel):
    """Full contract analysis result"""
    summary: str = Field(description="Executive summary of the contract")
    contract_type: str = Field(description="Type of contract")
    parties: List[PartyInfo] = Field(default_factory=list, description="Parties involved")
    obligations: List[ObligationInfo] = Field(default_factory=list, description="Key obligations")
    financial_terms: Optional[FinancialTerms] = Field(default=None, description="Financial terms")
    important_dates: List[ImportantDate] = Field(default_factory=list, description="Important dates")
    risks: List[RiskInfo] = Field(default_factory=list, description="Identified risks")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class ExtractedClause(BaseModel):
    """Single extracted clause"""
    clause_type: str = Field(description="Type of clause")
    title: str = Field(description="Clause title")
    content: str = Field(description="Full clause text")
    section_reference: Optional[str] = Field(default=None, description="Section reference")
    confidence: float = Field(default=0.8, description="Extraction confidence")


class ClauseExtractionResponse(BaseModel):
    """Clause extraction result"""
    clauses: List[ExtractedClause] = Field(default_factory=list, description="Extracted clauses")
    total_count: int = Field(description="Total number of clauses found")


class ClauseRiskAnalysis(BaseModel):
    """Risk analysis for a clause"""
    risk_level: str = Field(description="Risk level (low, medium, high, critical)")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    key_obligations: List[str] = Field(default_factory=list, description="Key obligations")
    key_dates: List[ImportantDate] = Field(default_factory=list, description="Key dates")
    financial_impact: Optional[str] = Field(default=None, description="Financial impact")
    recommendations: List[str] = Field(default_factory=list, description="Mitigation recommendations")
    confidence: float = Field(default=0.8, description="Analysis confidence")


class DateExtractionResult(BaseModel):
    """Date extraction result"""
    dates: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted dates")
    date_summary: str = Field(description="Summary of contract timeline")


# ==================== LangChain Client ====================

class LangChainContractClient:
    """
    LangChain-based wrapper for contract analysis using Google Gemini.

    Features:
    - Structured output with Pydantic models
    - Better error handling and JSON parsing
    - Singleton pattern for efficient resource usage
    """

    _instance: Optional["LangChainContractClient"] = None

    def __new__(cls) -> "LangChainContractClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured. AI features will be unavailable.")
            self.llm = None
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,  # Lower temperature for structured analysis
                max_output_tokens=8192,
            )

            # Higher temperature LLM for creative tasks
            self.llm_creative = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                max_output_tokens=4096,
            )

        self.model = settings.GEMINI_MODEL
        self._initialized = True
        logger.info(f"LangChainContractClient initialized with model: {self.model}")

    def is_available(self) -> bool:
        """Check if LangChain client is available."""
        return self.llm is not None

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate text completion using LangChain.

        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            system_instruction: Optional system instruction

        Returns:
            Generated text response

        Raises:
            AIServiceError: If generation fails
        """
        if not self.llm:
            raise AIServiceError(
                "LangChain client not initialized. Check GEMINI_API_KEY configuration."
            )

        try:
            messages = []
            if system_instruction:
                messages.append(SystemMessage(content=system_instruction))
            messages.append(HumanMessage(content=prompt))

            # Use appropriate LLM based on temperature
            llm = self.llm_creative if temperature >= 0.5 else self.llm

            response = await llm.ainvoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"LangChain generation error: {e}")
            raise AIServiceError(
                "Failed to generate AI response",
                details={"error": str(e)},
            )

    async def analyze_json(
        self,
        prompt: str,
        data: Dict[str, Any],
        system_instruction: str,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response using LangChain.

        Args:
            prompt: Analysis prompt
            data: Data to analyze
            system_instruction: System context/instructions

        Returns:
            Parsed JSON response

        Raises:
            AIServiceError: If analysis fails
        """
        if not self.llm:
            raise AIServiceError(
                "LangChain client not initialized. Check GEMINI_API_KEY configuration."
            )

        full_prompt = f"{prompt}\n\nData to analyze:\n```json\n{json.dumps(data, indent=2, default=str)}\n```"

        full_instruction = (
            f"{system_instruction}\n\n"
            "IMPORTANT: Respond ONLY with valid JSON. "
            "Do not include any markdown formatting, code blocks, or explanatory text. "
            "Your entire response must be parseable as JSON."
        )

        try:
            response = await self.generate(
                prompt=full_prompt,
                system_instruction=full_instruction,
                temperature=0.3,  # Lower temperature for structured output
            )

            # Clean response and parse JSON
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Remove code block markers
                lines = cleaned.split("\n")
                cleaned = "\n".join(
                    line for line in lines
                    if not line.strip().startswith("```")
                )

            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response[:500]}")
            raise AIServiceError(
                "AI response was not valid JSON",
                details={"error": str(e), "response_preview": response[:200]},
            )

    async def analyze_contract_structured(
        self,
        contract_text: str,
    ) -> ContractAnalysisResult:
        """
        Analyze contract text with structured Pydantic output.

        Args:
            contract_text: The contract text to analyze

        Returns:
            ContractAnalysisResult with structured analysis
        """
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=ContractAnalysisResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a contract analysis expert. Analyze contracts thoroughly and accurately.
Focus on identifying key terms, obligations, risks, and important dates.
Be precise and cite specific sections when possible.

{format_instructions}"""),
            ("human", """Provide a comprehensive analysis of this contract including:
1. Executive summary (2-3 sentences)
2. Contract type and purpose
3. Key parties involved
4. Main obligations for each party
5. Financial terms and value
6. Important dates and deadlines
7. Key risks and concerns
8. Recommendations

Contract text:
{contract_text}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            result = await chain.ainvoke({
                "contract_text": contract_text[:50000],
                "format_instructions": parser.get_format_instructions(),
            })
            return result
        except Exception as e:
            logger.error(f"Structured contract analysis failed: {e}")
            # Fall back to JSON method
            return await self._analyze_contract_fallback(contract_text)

    async def _analyze_contract_fallback(
        self,
        contract_text: str,
    ) -> ContractAnalysisResult:
        """Fallback analysis using JSON parsing."""
        result = await self.analyze_contract_text(contract_text, "full")
        return ContractAnalysisResult(
            summary=result.get("summary", ""),
            contract_type=result.get("contract_type", "Unknown"),
            parties=[PartyInfo(**p) for p in result.get("parties", [])],
            obligations=[ObligationInfo(**o) for o in result.get("obligations", [])],
            financial_terms=FinancialTerms(**result.get("financial_terms", {})) if result.get("financial_terms") else None,
            important_dates=[ImportantDate(**d) for d in result.get("important_dates", [])],
            risks=[RiskInfo(**r) for r in result.get("risks", [])],
            recommendations=result.get("recommendations", []),
        )

    async def analyze_contract_text(
        self,
        contract_text: str,
        analysis_type: str = "full",
    ) -> Dict[str, Any]:
        """
        Analyze contract text using AI (JSON output).

        Args:
            contract_text: The contract text to analyze
            analysis_type: Type of analysis (full, clauses, risk, dates)

        Returns:
            Analysis results as dictionary
        """
        if analysis_type == "clauses":
            prompt = """Extract and categorize all clauses from this contract.
For each clause, provide:
- type (payment_terms, delivery, warranty, liability, termination, confidentiality, penalty, renewal, force_majeure, compliance, other)
- title
- content (the exact text)
- section_reference (if available)
"""
        elif analysis_type == "risk":
            prompt = """Analyze the risk factors in this contract.
For each risk, provide:
- clause_reference
- risk_level (low, medium, high, critical)
- risk_description
- potential_impact
- mitigation_recommendation
"""
        elif analysis_type == "dates":
            prompt = """Extract all important dates and deadlines from this contract.
For each date, provide:
- date_type (start, end, milestone, deadline, renewal, termination_notice)
- date_value (ISO format if possible, or description)
- description
- is_recurring (true/false)
"""
        else:  # full analysis
            prompt = """Provide a comprehensive analysis of this contract including:
1. summary: Executive summary of the contract
2. parties: List of parties involved
3. contract_type: Type of contract
4. key_terms: Important terms and conditions
5. obligations: Key obligations for each party
6. financial_terms: Payment terms, amounts, penalties
7. important_dates: Key dates and deadlines
8. risk_assessment: Overall risk level and factors
9. recommendations: Suggestions for the contract holder
"""

        system_instruction = """You are a contract analysis expert. Analyze contracts thoroughly and accurately.
Focus on identifying key terms, obligations, risks, and important dates.
Be precise and cite specific sections when possible."""

        return await self.analyze_json(
            prompt=f"{prompt}\n\nContract text:\n{contract_text}",
            data={},
            system_instruction=system_instruction,
        )

    async def extract_clauses_structured(
        self,
        contract_text: str,
    ) -> ClauseExtractionResponse:
        """
        Extract clauses with structured Pydantic output.

        Args:
            contract_text: Contract text to analyze

        Returns:
            ClauseExtractionResponse with extracted clauses
        """
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=ClauseExtractionResponse)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a legal contract analyst specializing in clause extraction.
Extract all distinct clauses from contracts accurately.

{format_instructions}"""),
            ("human", """Extract all distinct clauses from this contract document.

For each clause, identify:
1. clause_type: One of [payment_terms, delivery, warranty, liability, termination, confidentiality, penalty, renewal, force_majeure, compliance, indemnification, intellectual_property, dispute_resolution, governing_law, other]
2. title: A descriptive title for the clause
3. content: The full text of the clause
4. section_reference: The section number/reference if available

Contract text:
{contract_text}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            result = await chain.ainvoke({
                "contract_text": contract_text[:50000],
                "format_instructions": parser.get_format_instructions(),
            })
            return result
        except Exception as e:
            logger.error(f"Structured clause extraction failed: {e}")
            raise AIServiceError(
                "Failed to extract clauses",
                details={"error": str(e)},
            )

    async def analyze_clause_risk_structured(
        self,
        clause_content: str,
        clause_type: str,
    ) -> ClauseRiskAnalysis:
        """
        Analyze clause risk with structured output.

        Args:
            clause_content: The clause text
            clause_type: Type of clause

        Returns:
            ClauseRiskAnalysis with risk assessment
        """
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=ClauseRiskAnalysis)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a legal risk analyst specializing in contract review.
Analyze contract clauses for potential risks.

{format_instructions}"""),
            ("human", """Analyze this contract clause for potential risks.

Clause Type: {clause_type}

Clause Content:
{clause_content}

Evaluate:
1. Risk level: low, medium, high, or critical
2. Risk factors: Specific concerns with this clause
3. Key obligations: What actions are required
4. Key dates: Any deadlines or time-sensitive elements
5. Financial impact: Potential monetary implications
6. Recommendations: How to mitigate identified risks"""),
        ])

        try:
            chain = prompt | self.llm | parser
            result = await chain.ainvoke({
                "clause_content": clause_content,
                "clause_type": clause_type,
                "format_instructions": parser.get_format_instructions(),
            })
            return result
        except Exception as e:
            logger.error(f"Structured risk analysis failed: {e}")
            raise AIServiceError(
                "Failed to analyze clause risk",
                details={"error": str(e)},
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check LangChain/Gemini API connectivity."""
        if not self.llm:
            return {
                "available": False,
                "error": "Client not initialized",
            }

        try:
            # Simple test generation
            response = await self.generate(
                prompt="Respond with only: OK",
                max_tokens=10,
                temperature=0,
            )

            return {
                "available": True,
                "model": self.model,
                "framework": "langchain",
                "test_response": response.strip(),
            }

        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }


# ==================== Singleton Access ====================

_langchain_client: Optional[LangChainContractClient] = None


def get_langchain_client() -> LangChainContractClient:
    """Get the singleton LangChain client instance."""
    global _langchain_client
    if _langchain_client is None:
        _langchain_client = LangChainContractClient()
    return _langchain_client


# ==================== Backward Compatibility Alias ====================
GeminiClient = LangChainContractClient
get_gemini_client = get_langchain_client
