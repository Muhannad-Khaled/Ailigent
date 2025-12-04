"""LLM Prompt Templates for AI Features."""

WORKLOAD_ANALYSIS_PROMPT = """
Analyze the team workload distribution based on the provided data.

Evaluate:
1. Overall workload balance across the team (0-100 score)
2. Identify overloaded employees (>80% utilization)
3. Identify underutilized employees (<50% utilization)
4. Check for deadline conflicts and risks
5. Assess skill coverage gaps

Return a JSON response with exactly this structure:
{
    "balance_score": <number 0-100>,
    "summary": "<brief summary of workload state>",
    "overloaded_employees": [
        {
            "id": <employee_id>,
            "name": "<name>",
            "utilization": <percentage>,
            "recommendation": "<specific action>"
        }
    ],
    "underutilized_employees": [
        {
            "id": <employee_id>,
            "name": "<name>",
            "utilization": <percentage>,
            "recommendation": "<specific action>"
        }
    ],
    "deadline_risks": [
        {
            "task_id": <id>,
            "task_name": "<name>",
            "risk_level": "<high|medium|low>",
            "reason": "<why this is at risk>"
        }
    ],
    "recommendations": [
        "<actionable recommendation 1>",
        "<actionable recommendation 2>"
    ]
}
"""

TASK_DISTRIBUTION_PROMPT = """
Recommend the best employee assignment for the given task.

Consider these factors in order of importance:
1. Current workload and remaining capacity (most important)
2. Skills match with task requirements
3. Deadline urgency
4. Historical completion rate

Return a JSON response with exactly this structure:
{
    "recommended_employee_id": <id>,
    "recommended_employee_name": "<name>",
    "confidence_score": <number 0-100>,
    "reasoning": "<2-3 sentence explanation>",
    "alternatives": [
        {
            "id": <id>,
            "name": "<name>",
            "score": <number 0-100>,
            "reason": "<why this is an alternative>"
        }
    ],
    "warnings": [
        "<any concerns about this assignment>"
    ]
}
"""

BOTTLENECK_ANALYSIS_PROMPT = """
Analyze the workflow data to identify bottlenecks and blockers.

Identify:
1. Stages where tasks accumulate (stage bottlenecks)
2. Employees who are blocking points (capacity bottlenecks)
3. Common patterns in delays
4. Root causes of overdue tasks

Return a JSON response with exactly this structure:
{
    "bottlenecks": [
        {
            "type": "<stage|employee|process|dependency>",
            "location": "<stage name or employee name>",
            "severity": "<critical|high|medium|low>",
            "impact": "<number of affected tasks or hours>",
            "root_cause": "<identified cause>",
            "recommendation": "<specific action to resolve>"
        }
    ],
    "patterns": [
        {
            "pattern": "<description of pattern>",
            "frequency": "<how often it occurs>",
            "impact": "<effect on productivity>"
        }
    ],
    "priority_actions": [
        "<most urgent action 1>",
        "<action 2>",
        "<action 3>"
    ],
    "summary": "<executive summary of bottleneck analysis>"
}
"""

PRODUCTIVITY_REPORT_PROMPT = """
Generate a comprehensive productivity report based on the provided metrics.

Include analysis of:
1. Task completion rates and trends
2. Team and individual performance
3. Time management and deadline adherence
4. Areas of improvement

Return a JSON response with exactly this structure:
{
    "executive_summary": "<2-3 sentence high-level summary>",
    "key_metrics": {
        "overall_health": "<healthy|warning|critical>",
        "productivity_trend": "<improving|stable|declining>",
        "biggest_win": "<highlight a positive metric>",
        "biggest_concern": "<highlight an area needing attention>"
    },
    "team_performance": {
        "top_performers": ["<name 1>", "<name 2>"],
        "improvement_needed": ["<name 1>"],
        "trend_analysis": "<brief analysis of team trends>"
    },
    "insights": [
        "<insight 1 based on data>",
        "<insight 2 based on data>"
    ],
    "recommendations": [
        "<actionable recommendation 1>",
        "<actionable recommendation 2>"
    ],
    "risks": [
        "<identified risk 1>",
        "<identified risk 2>"
    ]
}
"""

TASK_PRIORITY_PROMPT = """
Analyze the task and suggest appropriate priority and handling.

Consider:
1. Business impact
2. Dependencies on other tasks
3. Deadline urgency
4. Resource requirements

Return a JSON response with exactly this structure:
{
    "suggested_priority": "<urgent|high|normal|low>",
    "urgency_score": <number 0-100>,
    "reasoning": "<explanation for priority suggestion>",
    "handling_recommendations": [
        "<how to handle this task effectively>"
    ],
    "potential_blockers": [
        "<things that might block this task>"
    ]
}
"""

OVERDUE_ANALYSIS_PROMPT = """
Analyze the overdue tasks and provide actionable insights.

Consider:
1. Patterns in why tasks are overdue
2. Common blockers
3. Employee-specific issues
4. Process improvements needed

Return a JSON response with exactly this structure:
{
    "analysis_summary": "<overview of overdue situation>",
    "root_causes": [
        {
            "cause": "<identified cause>",
            "affected_tasks": <number>,
            "severity": "<critical|high|medium|low>"
        }
    ],
    "employee_patterns": [
        {
            "employee_name": "<name>",
            "overdue_count": <number>,
            "likely_reason": "<why they have overdue tasks>",
            "recommendation": "<specific action>"
        }
    ],
    "immediate_actions": [
        "<action 1 to take now>",
        "<action 2 to take now>"
    ],
    "process_improvements": [
        "<long-term improvement suggestion>"
    ]
}
"""
