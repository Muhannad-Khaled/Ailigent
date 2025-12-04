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
        max_tokens: int = 2048,
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

    async def analyze_cv(
        self,
        cv_text: str,
        job_requirements: str,
    ) -> Dict[str, Any]:
        """
        Analyze a CV against job requirements.

        Args:
            cv_text: Extracted text from CV
            job_requirements: Job description and requirements

        Returns:
            Analysis results including score and recommendations
        """
        from app.services.ai.prompts import CV_ANALYSIS_PROMPT, CV_ANALYSIS_SYSTEM

        prompt = CV_ANALYSIS_PROMPT.format(
            job_requirements=job_requirements,
            cv_content=cv_text,
        )

        return await self.analyze_json(
            prompt=prompt,
            data={},
            system_instruction=CV_ANALYSIS_SYSTEM,
        )

    async def summarize_appraisal(
        self,
        feedback_notes: str,
        goals: str,
    ) -> Dict[str, Any]:
        """
        Summarize appraisal feedback.

        Args:
            feedback_notes: All feedback notes for the appraisal
            goals: Employee goals and objectives

        Returns:
            Summary with key insights
        """
        from app.services.ai.prompts import APPRAISAL_SUMMARY_PROMPT, APPRAISAL_SUMMARY_SYSTEM

        prompt = APPRAISAL_SUMMARY_PROMPT.format(
            feedback_notes=feedback_notes,
            goals=goals,
        )

        return await self.analyze_json(
            prompt=prompt,
            data={},
            system_instruction=APPRAISAL_SUMMARY_SYSTEM,
        )

    async def generate_hr_insights(
        self,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate HR insights from metrics.

        Args:
            metrics: HR metrics data

        Returns:
            AI-generated insights
        """
        from app.services.ai.prompts import HR_INSIGHTS_PROMPT, HR_INSIGHTS_SYSTEM

        return await self.analyze_json(
            prompt=HR_INSIGHTS_PROMPT,
            data=metrics,
            system_instruction=HR_INSIGHTS_SYSTEM,
        )

    async def detect_attendance_anomalies(
        self,
        attendance_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze attendance data for anomalies.

        Args:
            attendance_data: Attendance records to analyze

        Returns:
            Detected anomalies with recommendations
        """
        from app.services.ai.prompts import ATTENDANCE_ANOMALY_PROMPT, ATTENDANCE_ANOMALY_SYSTEM

        return await self.analyze_json(
            prompt=ATTENDANCE_ANOMALY_PROMPT,
            data=attendance_data,
            system_instruction=ATTENDANCE_ANOMALY_SYSTEM,
        )

    async def rank_candidates(
        self,
        job_description: str,
        candidates_data: list,
    ) -> Dict[str, Any]:
        """
        Rank multiple candidates for a job position.

        Args:
            job_description: Job title and requirements
            candidates_data: List of candidate info with CV text

        Returns:
            Rankings with scores and rationale
        """
        from app.services.ai.prompts import CANDIDATE_RANKING_PROMPT, CANDIDATE_RANKING_SYSTEM

        # Format candidates data
        formatted_candidates = "\n\n".join([
            f"--- Candidate {i+1} ---\n"
            f"ID: {c.get('id')}\n"
            f"Name: {c.get('name')}\n"
            f"Email: {c.get('email')}\n"
            f"CV/Notes:\n{c.get('cv_text', 'No CV text available')}"
            for i, c in enumerate(candidates_data)
        ])

        prompt = CANDIDATE_RANKING_PROMPT.format(
            job_description=job_description,
            candidates_data=formatted_candidates,
        )

        return await self.analyze_json(
            prompt=prompt,
            data={},
            system_instruction=CANDIDATE_RANKING_SYSTEM,
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
