"""
LangChain-based HR Analysis Client.

This module replaces the direct Google Gemini integration with LangChain,
providing structured output parsing with Pydantic models for HR analysis tasks.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


# ==================== Pydantic Output Models ====================

class SkillMatch(BaseModel):
    """Skill matching analysis"""
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    additional_skills: List[str] = Field(default_factory=list)


class ExperienceAnalysis(BaseModel):
    """Experience analysis result"""
    years_experience: float = Field(default=0)
    relevance_score: int = Field(default=0, ge=0, le=100)
    key_experiences: List[str] = Field(default_factory=list)


class EducationMatch(BaseModel):
    """Education matching result"""
    meets_requirements: bool = Field(default=False)
    details: str = Field(default="")


class CVAnalysisResult(BaseModel):
    """Full CV analysis result"""
    overall_score: int = Field(ge=0, le=100, description="Overall match score 0-100")
    skill_match: SkillMatch = Field(default_factory=SkillMatch)
    experience_analysis: ExperienceAnalysis = Field(default_factory=ExperienceAnalysis)
    education_match: EducationMatch = Field(default_factory=EducationMatch)
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    interview_questions: List[str] = Field(default_factory=list)
    hiring_recommendation: str = Field(description="strong_hire, hire, maybe, or no_hire")
    summary: str = Field(description="2-3 sentence executive summary")


class GoalAchievement(BaseModel):
    """Goal achievement tracking"""
    goals_met: List[str] = Field(default_factory=list)
    goals_partial: List[str] = Field(default_factory=list)
    goals_not_met: List[str] = Field(default_factory=list)


class AppraisalSummaryResult(BaseModel):
    """Appraisal summary result"""
    executive_summary: str = Field(description="2-3 sentence summary")
    key_strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    goal_achievement: GoalAchievement = Field(default_factory=GoalAchievement)
    themes: List[str] = Field(default_factory=list)
    development_recommendations: List[str] = Field(default_factory=list)
    overall_rating_suggestion: str = Field(description="exceeds, meets, or below")
    action_items: List[str] = Field(default_factory=list)


class Insight(BaseModel):
    """Single HR insight"""
    insight: str
    impact: str = Field(description="high, medium, or low")
    category: str


class Risk(BaseModel):
    """Single risk item"""
    risk: str
    severity: str = Field(description="high, medium, or low")
    mitigation: str


class Opportunity(BaseModel):
    """Single opportunity item"""
    opportunity: str
    potential_impact: str


class Recommendation(BaseModel):
    """Single recommendation"""
    recommendation: str
    priority: str = Field(description="high, medium, or low")
    timeline: str = Field(description="immediate, short_term, or long_term")


class Trends(BaseModel):
    """HR trends analysis"""
    positive: List[str] = Field(default_factory=list)
    negative: List[str] = Field(default_factory=list)
    neutral: List[str] = Field(default_factory=list)


class KPIHighlight(BaseModel):
    """KPI highlight"""
    metric: str
    status: str = Field(description="good, warning, or critical")
    note: str


class HRInsightsResult(BaseModel):
    """HR insights analysis result"""
    executive_summary: str = Field(description="3-4 sentence summary")
    key_insights: List[Insight] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    opportunities: List[Opportunity] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    trends: Trends = Field(default_factory=Trends)
    kpi_highlights: List[KPIHighlight] = Field(default_factory=list)


class AttendanceAnomaly(BaseModel):
    """Single attendance anomaly"""
    employee_id: int
    employee_name: str
    anomaly_type: str = Field(description="late_arrival, early_departure, missing_checkout, excessive_overtime, pattern")
    severity: str = Field(description="low, medium, or high")
    description: str
    frequency: str
    dates_affected: List[str] = Field(default_factory=list)
    recommendation: str


class AnomalySummary(BaseModel):
    """Anomaly summary stats"""
    total_anomalies: int = Field(default=0)
    high_severity_count: int = Field(default=0)
    departments_affected: List[str] = Field(default_factory=list)


class DepartmentPattern(BaseModel):
    """Department-level attendance pattern"""
    department: str
    pattern: str
    concern_level: str = Field(description="low, medium, or high")


class AttendanceAnomalyResult(BaseModel):
    """Attendance anomaly detection result"""
    anomalies: List[AttendanceAnomaly] = Field(default_factory=list)
    summary: AnomalySummary = Field(default_factory=AnomalySummary)
    department_patterns: List[DepartmentPattern] = Field(default_factory=list)
    recommendations: List[Dict[str, str]] = Field(default_factory=list)
    overall_assessment: str = Field(description="1-2 sentence assessment")


class CandidateRank(BaseModel):
    """Single candidate ranking"""
    rank: int
    applicant_id: int
    name: str
    overall_score: int = Field(ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    recommendation: str


class CandidateRankingResult(BaseModel):
    """Candidate ranking result"""
    rankings: List[CandidateRank] = Field(default_factory=list)
    comparison_notes: str = Field(default="")
    top_pick_rationale: str = Field(default="")


# ==================== LangChain Client ====================

class LangChainHRClient:
    """
    LangChain-based wrapper for HR analysis using Google Gemini.

    Features:
    - CV analysis with structured Pydantic output
    - Appraisal feedback summarization
    - HR insights generation
    - Attendance anomaly detection
    - Candidate ranking
    """

    _instance: Optional["LangChainHRClient"] = None

    def __new__(cls) -> "LangChainHRClient":
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
                temperature=0.3,
                max_output_tokens=4096,
            )

            self.llm_creative = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                max_output_tokens=2048,
            )

        self.model = settings.GEMINI_MODEL
        self._initialized = True
        logger.info(f"LangChainHRClient initialized with model: {self.model}")

    def is_available(self) -> bool:
        """Check if LangChain client is available."""
        return self.llm is not None

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate text completion using LangChain."""
        if not self.llm:
            raise AIServiceError(
                "LangChain client not initialized. Check GEMINI_API_KEY configuration."
            )

        try:
            messages = []
            if system_instruction:
                messages.append(SystemMessage(content=system_instruction))
            messages.append(HumanMessage(content=prompt))

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
        """Generate structured JSON response."""
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

        response = await self.generate(
            prompt=full_prompt,
            system_instruction=full_instruction,
            temperature=0.3,
        )

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
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
        """Analyze a CV against job requirements."""
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

    async def analyze_cv_structured(
        self,
        cv_text: str,
        job_requirements: str,
    ) -> CVAnalysisResult:
        """Analyze a CV with structured Pydantic output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=CVAnalysisResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert HR recruiter and talent acquisition specialist.
Your task is to analyze CVs/resumes against job requirements and provide structured assessments.
Be objective, thorough, and focus on relevant qualifications and experience.

{format_instructions}"""),
            ("human", """Analyze this CV/resume against the job requirements provided.

Job Requirements:
{job_requirements}

CV Content:
{cv_content}

Provide a comprehensive analysis including overall score, skill match, experience analysis,
strengths, concerns, interview questions, and hiring recommendation."""),
        ])

        try:
            chain = prompt | self.llm | parser
            result = await chain.ainvoke({
                "job_requirements": job_requirements,
                "cv_content": cv_text[:30000],
                "format_instructions": parser.get_format_instructions(),
            })
            return result
        except Exception as e:
            logger.error(f"Structured CV analysis failed: {e}")
            # Fall back to JSON method
            json_result = await self.analyze_cv(cv_text, job_requirements)
            return CVAnalysisResult(**json_result)

    async def summarize_appraisal(
        self,
        feedback_notes: str,
        goals: str,
    ) -> Dict[str, Any]:
        """Summarize appraisal feedback."""
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

    async def summarize_appraisal_structured(
        self,
        feedback_notes: str,
        goals: str,
    ) -> AppraisalSummaryResult:
        """Summarize appraisal with structured output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=AppraisalSummaryResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an HR performance management expert.
Your task is to summarize performance appraisal feedback and provide actionable insights.
Be constructive, balanced, and focus on development opportunities.

{format_instructions}"""),
            ("human", """Summarize the following performance appraisal feedback.

Feedback Notes:
{feedback_notes}

Goals and Objectives:
{goals}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            return await chain.ainvoke({
                "feedback_notes": feedback_notes,
                "goals": goals,
                "format_instructions": parser.get_format_instructions(),
            })
        except Exception as e:
            logger.error(f"Structured appraisal summary failed: {e}")
            json_result = await self.summarize_appraisal(feedback_notes, goals)
            return AppraisalSummaryResult(**json_result)

    async def generate_hr_insights(
        self,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate HR insights from metrics."""
        from app.services.ai.prompts import HR_INSIGHTS_PROMPT, HR_INSIGHTS_SYSTEM

        return await self.analyze_json(
            prompt=HR_INSIGHTS_PROMPT,
            data=metrics,
            system_instruction=HR_INSIGHTS_SYSTEM,
        )

    async def generate_hr_insights_structured(
        self,
        metrics: Dict[str, Any],
    ) -> HRInsightsResult:
        """Generate HR insights with structured output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=HRInsightsResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strategic HR analytics expert.
Your task is to analyze HR metrics and provide actionable business insights.
Focus on trends, risks, and opportunities that impact organizational performance.

{format_instructions}"""),
            ("human", """Analyze the provided HR metrics and generate strategic insights.

Metrics Data:
{metrics}

Focus on:
1. Key trends and patterns
2. Potential risks or concerns
3. Opportunities for improvement
4. Actionable recommendations"""),
        ])

        try:
            chain = prompt | self.llm | parser
            return await chain.ainvoke({
                "metrics": json.dumps(metrics, indent=2, default=str),
                "format_instructions": parser.get_format_instructions(),
            })
        except Exception as e:
            logger.error(f"Structured HR insights failed: {e}")
            json_result = await self.generate_hr_insights(metrics)
            return HRInsightsResult(**json_result)

    async def detect_attendance_anomalies(
        self,
        attendance_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze attendance data for anomalies."""
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
        """Rank multiple candidates for a job position."""
        from app.services.ai.prompts import CANDIDATE_RANKING_PROMPT, CANDIDATE_RANKING_SYSTEM

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

    async def rank_candidates_structured(
        self,
        job_description: str,
        candidates_data: list,
    ) -> CandidateRankingResult:
        """Rank candidates with structured output."""
        if not self.llm:
            raise AIServiceError("LangChain client not initialized.")

        parser = PydanticOutputParser(pydantic_object=CandidateRankingResult)

        formatted_candidates = "\n\n".join([
            f"--- Candidate {i+1} ---\n"
            f"ID: {c.get('id')}\n"
            f"Name: {c.get('name')}\n"
            f"Email: {c.get('email')}\n"
            f"CV/Notes:\n{c.get('cv_text', 'No CV text available')}"
            for i, c in enumerate(candidates_data)
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert talent acquisition specialist.
Your task is to rank multiple candidates for a position based on their qualifications.
Be objective and provide clear rationale for rankings.
IMPORTANT: Include ALL candidates in the rankings, even if they don't meet requirements.

{format_instructions}"""),
            ("human", """Rank ALL the following candidates for the position.

Job Position:
{job_description}

Candidates:
{candidates_data}"""),
        ])

        try:
            chain = prompt | self.llm | parser
            return await chain.ainvoke({
                "job_description": job_description,
                "candidates_data": formatted_candidates,
                "format_instructions": parser.get_format_instructions(),
            })
        except Exception as e:
            logger.error(f"Structured candidate ranking failed: {e}")
            json_result = await self.rank_candidates(job_description, candidates_data)
            return CandidateRankingResult(**json_result)

    async def health_check(self) -> Dict[str, Any]:
        """Check LangChain/Gemini API connectivity."""
        if not self.llm:
            return {
                "available": False,
                "error": "Client not initialized",
            }

        try:
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

_langchain_client: Optional[LangChainHRClient] = None


def get_langchain_hr_client() -> LangChainHRClient:
    """Get the singleton LangChain HR client instance."""
    global _langchain_client
    if _langchain_client is None:
        _langchain_client = LangChainHRClient()
    return _langchain_client


# ==================== Backward Compatibility Aliases ====================
GeminiClient = LangChainHRClient
get_gemini_client = get_langchain_hr_client
