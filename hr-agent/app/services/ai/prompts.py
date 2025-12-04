"""LLM Prompt Templates for HR Agent."""

# CV Analysis Prompts
CV_ANALYSIS_SYSTEM = """You are an expert HR recruiter and talent acquisition specialist.
Your task is to analyze CVs/resumes against job requirements and provide structured assessments.
Be objective, thorough, and focus on relevant qualifications and experience.
Always respond with valid JSON only."""

CV_ANALYSIS_PROMPT = """
Analyze this CV/resume against the job requirements provided.

Job Requirements:
{job_requirements}

CV Content:
{cv_content}

Provide a JSON response with the following structure:
{{
    "overall_score": <0-100>,
    "skill_match": {{
        "matched_skills": ["skill1", "skill2"],
        "missing_skills": ["skill1", "skill2"],
        "additional_skills": ["skill1", "skill2"]
    }},
    "experience_analysis": {{
        "years_experience": <number>,
        "relevance_score": <0-100>,
        "key_experiences": ["exp1", "exp2"]
    }},
    "education_match": {{
        "meets_requirements": <boolean>,
        "details": "description"
    }},
    "strengths": ["strength1", "strength2"],
    "concerns": ["concern1", "concern2"],
    "interview_questions": ["question1", "question2", "question3"],
    "hiring_recommendation": "<strong_hire|hire|maybe|no_hire>",
    "summary": "2-3 sentence executive summary"
}}
"""

# Appraisal Summary Prompts
APPRAISAL_SUMMARY_SYSTEM = """You are an HR performance management expert.
Your task is to summarize performance appraisal feedback and provide actionable insights.
Be constructive, balanced, and focus on development opportunities.
Always respond with valid JSON only."""

APPRAISAL_SUMMARY_PROMPT = """
Summarize the following performance appraisal feedback.

Feedback Notes:
{feedback_notes}

Goals and Objectives:
{goals}

Provide a JSON response with the following structure:
{{
    "executive_summary": "2-3 sentence summary",
    "key_strengths": ["strength1", "strength2", "strength3"],
    "areas_for_improvement": ["area1", "area2"],
    "goal_achievement": {{
        "goals_met": ["goal1", "goal2"],
        "goals_partial": ["goal1"],
        "goals_not_met": ["goal1"]
    }},
    "themes": ["theme1", "theme2"],
    "development_recommendations": ["recommendation1", "recommendation2"],
    "overall_rating_suggestion": "<exceeds|meets|below>",
    "action_items": ["action1", "action2"]
}}
"""

# HR Insights Prompts
HR_INSIGHTS_SYSTEM = """You are a strategic HR analytics expert.
Your task is to analyze HR metrics and provide actionable business insights.
Focus on trends, risks, and opportunities that impact organizational performance.
Always respond with valid JSON only."""

HR_INSIGHTS_PROMPT = """
Analyze the provided HR metrics and generate strategic insights.

Focus on:
1. Key trends and patterns
2. Potential risks or concerns
3. Opportunities for improvement
4. Actionable recommendations

Provide a JSON response with the following structure:
{{
    "executive_summary": "3-4 sentence high-level summary",
    "key_insights": [
        {{"insight": "description", "impact": "high|medium|low", "category": "category"}}
    ],
    "risks": [
        {{"risk": "description", "severity": "high|medium|low", "mitigation": "suggested action"}}
    ],
    "opportunities": [
        {{"opportunity": "description", "potential_impact": "description"}}
    ],
    "recommendations": [
        {{"recommendation": "description", "priority": "high|medium|low", "timeline": "immediate|short_term|long_term"}}
    ],
    "trends": {{
        "positive": ["trend1", "trend2"],
        "negative": ["trend1"],
        "neutral": ["trend1"]
    }},
    "kpi_highlights": [
        {{"metric": "name", "status": "good|warning|critical", "note": "explanation"}}
    ]
}}
"""

# Attendance Anomaly Prompts
ATTENDANCE_ANOMALY_SYSTEM = """You are an HR compliance and attendance monitoring expert.
Your task is to analyze attendance patterns and identify anomalies that may require HR attention.
Be thorough but avoid false positives. Focus on patterns that genuinely indicate issues.
Always respond with valid JSON only."""

ATTENDANCE_ANOMALY_PROMPT = """
Analyze the provided attendance data for anomalies and patterns.

Identify:
1. Unusual patterns (consistently late, early departures)
2. Missing check-outs
3. Overtime patterns that may indicate burnout or workload issues
4. Any patterns requiring HR attention

Provide a JSON response with the following structure:
{{
    "anomalies": [
        {{
            "employee_id": <id>,
            "employee_name": "name",
            "anomaly_type": "<late_arrival|early_departure|missing_checkout|excessive_overtime|pattern>",
            "severity": "<low|medium|high>",
            "description": "detailed description",
            "frequency": "how often this occurs",
            "dates_affected": ["date1", "date2"],
            "recommendation": "suggested action"
        }}
    ],
    "summary": {{
        "total_anomalies": <number>,
        "high_severity_count": <number>,
        "departments_affected": ["dept1", "dept2"]
    }},
    "department_patterns": [
        {{"department": "name", "pattern": "description", "concern_level": "low|medium|high"}}
    ],
    "recommendations": [
        {{"recommendation": "description", "priority": "high|medium|low"}}
    ],
    "overall_assessment": "1-2 sentence overall assessment"
}}
"""

# Candidate Ranking Prompts
CANDIDATE_RANKING_SYSTEM = """You are an expert talent acquisition specialist.
Your task is to rank multiple candidates for a position based on their qualifications.
Be objective and provide clear rationale for rankings.
Always respond with valid JSON only."""

CANDIDATE_RANKING_PROMPT = """
Rank ALL the following candidates for the position based on their qualifications and fit.
IMPORTANT: You MUST include ALL candidates in the rankings array, even if they don't meet requirements.
Assign appropriate scores (0-100) based on fit, with lower scores for poor matches.

Job Position:
{job_description}

Candidates:
{candidates_data}

Provide a JSON response with the following structure:
{{
    "rankings": [
        {{
            "rank": 1,
            "applicant_id": <id>,
            "name": "candidate name",
            "overall_score": <0-100>,
            "strengths": ["strength1", "strength2"],
            "concerns": ["concern1"],
            "recommendation": "<STRONG_HIRE|HIRE|MAYBE|NO_HIRE> - brief explanation"
        }}
    ],
    "comparison_notes": "notes on how candidates compare",
    "top_pick_rationale": "why the top candidate stands out (or why none are ideal)"
}}

Remember: Include ALL candidates in rankings, sorted by score. Even poor matches should be listed with appropriate low scores.
"""

# Interview Questions Generation
INTERVIEW_QUESTIONS_SYSTEM = """You are an expert interviewer and talent assessor.
Generate targeted interview questions based on the candidate's background and the job requirements.
Focus on both technical competencies and behavioral/cultural fit.
Always respond with valid JSON only."""

INTERVIEW_QUESTIONS_PROMPT = """
Generate interview questions for this candidate.

Job Requirements:
{job_requirements}

Candidate Background:
{candidate_background}

Areas to Probe (based on CV analysis):
{areas_to_probe}

Provide a JSON response with the following structure:
{{
    "technical_questions": [
        {{"question": "question text", "purpose": "what this assesses", "follow_ups": ["follow-up1"]}}
    ],
    "behavioral_questions": [
        {{"question": "question text", "competency": "what competency this assesses"}}
    ],
    "experience_validation": [
        {{"question": "question text", "relates_to": "which CV claim to validate"}}
    ],
    "culture_fit_questions": [
        {{"question": "question text", "value_assessed": "company value being assessed"}}
    ],
    "red_flag_probes": [
        {{"question": "question text", "concern": "what concern this addresses"}}
    ]
}}
"""
