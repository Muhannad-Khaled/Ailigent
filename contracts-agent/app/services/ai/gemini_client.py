"""Google Gemini API Client."""

import json
import logging
from typing import Any, Dict, Optional

from google import genai

from app.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper for Google Gemini API."""

    _instance: Optional["GeminiClient"] = None

    def __new__(cls) -> "GeminiClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured. AI features will be unavailable.")
            self.client = None
        else:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

        self.model = settings.GEMINI_MODEL
        self._initialized = True

    def is_available(self) -> bool:
        """Check if Gemini client is available."""
        return self.client is not None

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate text completion.

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
        if not self.client:
            raise AIServiceError(
                "Gemini client not initialized. Check GEMINI_API_KEY configuration."
            )

        try:
            config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )

            return response.text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
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
        Generate structured JSON response.

        Args:
            prompt: Analysis prompt
            data: Data to analyze
            system_instruction: System context/instructions

        Returns:
            Parsed JSON response

        Raises:
            AIServiceError: If analysis fails
        """
        full_prompt = f"{prompt}\n\nData to analyze:\n```json\n{json.dumps(data, indent=2, default=str)}\n```"

        full_instruction = (
            f"{system_instruction}\n\n"
            "IMPORTANT: Respond ONLY with valid JSON. "
            "Do not include any markdown formatting, code blocks, or explanatory text. "
            "Your entire response must be parseable as JSON."
        )

        response = await self.generate(
            prompt=full_prompt,
            system_instruction=full_instruction,
            temperature=0.3,  # Lower temperature for structured output
        )

        # Clean response and parse JSON
        try:
            # Remove potential markdown formatting
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

    async def analyze_contract_text(
        self,
        contract_text: str,
        analysis_type: str = "full",
    ) -> Dict[str, Any]:
        """
        Analyze contract text using AI.

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

    async def health_check(self) -> Dict[str, Any]:
        """Check Gemini API connectivity."""
        if not self.client:
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
                "test_response": response.strip(),
            }

        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }


_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get the singleton Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
