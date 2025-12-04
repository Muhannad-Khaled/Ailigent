"""AI-Powered Workload Optimization."""

import logging
from typing import Any, Dict, List, Optional

from app.core.constants import (
    DEFAULT_WEEKLY_HOURS,
    WORKLOAD_OVERLOADED_THRESHOLD,
    WORKLOAD_UNDERUTILIZED_THRESHOLD,
)
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.prompts import WORKLOAD_ANALYSIS_PROMPT, TASK_DISTRIBUTION_PROMPT

logger = logging.getLogger(__name__)


class WorkloadOptimizer:
    """Uses AI to analyze workload and recommend optimal task distribution."""

    def __init__(self, gemini_client: GeminiClient):
        self.ai = gemini_client

    async def analyze_team_workload(
        self,
        employees: List[Dict],
        tasks: List[Dict],
        weekly_capacity: float = DEFAULT_WEEKLY_HOURS,
    ) -> Dict[str, Any]:
        """
        Analyze current team workload distribution.

        Args:
            employees: List of employee data with workload info
            tasks: List of pending tasks
            weekly_capacity: Weekly hours capacity per employee

        Returns:
            Analysis including balance score, overloaded/underutilized employees,
            and recommendations
        """
        if not self.ai.is_available():
            return self._basic_workload_analysis(employees, tasks, weekly_capacity)

        # Prepare data for AI analysis
        data = {
            "employees": [
                {
                    "id": e.get("user_id") or e.get("id"),
                    "name": e.get("employee_name") or e.get("name"),
                    "current_task_count": e.get("task_count", 0),
                    "remaining_hours": e.get("remaining_hours", 0),
                    "utilization_percentage": e.get("utilization", 0),
                    "high_priority_tasks": e.get("high_priority", 0),
                    "overdue_tasks": e.get("overdue", 0),
                    "capacity_hours": weekly_capacity,
                }
                for e in employees
            ],
            "pending_tasks_summary": {
                "total_count": len(tasks),
                "high_priority_count": sum(
                    1 for t in tasks if t.get("priority") in ("2", "3")
                ),
                "overdue_count": sum(1 for t in tasks if t.get("days_overdue", 0) > 0),
                "total_remaining_hours": sum(
                    t.get("remaining_hours", 0) or 0 for t in tasks
                ),
            },
            "team_summary": {
                "total_employees": len(employees),
                "average_utilization": (
                    sum(e.get("utilization", 0) for e in employees) / len(employees)
                    if employees
                    else 0
                ),
            },
        }

        try:
            analysis = await self.ai.analyze_json(
                prompt=WORKLOAD_ANALYSIS_PROMPT,
                data=data,
                system_instruction=(
                    "You are a workload analysis expert. Analyze the team capacity "
                    "and provide actionable insights. Focus on practical recommendations "
                    "that can be implemented immediately."
                ),
            )

            return analysis

        except Exception as e:
            logger.error(f"AI workload analysis failed: {e}")
            return self._basic_workload_analysis(employees, tasks, weekly_capacity)

    def _basic_workload_analysis(
        self,
        employees: List[Dict],
        tasks: List[Dict],
        weekly_capacity: float,
    ) -> Dict[str, Any]:
        """Fallback basic analysis without AI."""
        overloaded = []
        underutilized = []

        for emp in employees:
            utilization = emp.get("utilization", 0)
            emp_info = {
                "id": emp.get("user_id") or emp.get("id"),
                "name": emp.get("employee_name") or emp.get("name"),
                "utilization": utilization,
            }

            if utilization >= WORKLOAD_OVERLOADED_THRESHOLD * 100:
                emp_info["recommendation"] = "Redistribute some tasks to other team members"
                overloaded.append(emp_info)
            elif utilization <= WORKLOAD_UNDERUTILIZED_THRESHOLD * 100:
                emp_info["recommendation"] = "Can take on additional tasks"
                underutilized.append(emp_info)

        # Calculate balance score
        if not employees:
            balance_score = 0
        else:
            utilizations = [e.get("utilization", 0) for e in employees]
            avg = sum(utilizations) / len(utilizations)
            variance = sum((u - avg) ** 2 for u in utilizations) / len(utilizations)
            # Convert variance to score (lower variance = higher score)
            balance_score = max(0, 100 - variance)

        recommendations = []
        if overloaded:
            recommendations.append(
                f"Redistribute tasks from {len(overloaded)} overloaded employee(s)"
            )
        if underutilized:
            recommendations.append(
                f"Assign more tasks to {len(underutilized)} underutilized employee(s)"
            )

        return {
            "balance_score": round(balance_score, 1),
            "summary": f"Team has {len(overloaded)} overloaded and {len(underutilized)} underutilized members",
            "overloaded_employees": overloaded,
            "underutilized_employees": underutilized,
            "deadline_risks": [],
            "recommendations": recommendations or ["Workload distribution appears balanced"],
        }

    async def recommend_task_assignment(
        self,
        task: Dict,
        available_employees: List[Dict],
    ) -> Dict[str, Any]:
        """
        Recommend the best employee(s) for a specific task.

        Args:
            task: Task details including name, hours, priority, deadline
            available_employees: List of employees who can be assigned

        Returns:
            Recommendation with confidence score and reasoning
        """
        if not self.ai.is_available():
            return self._basic_assignment_recommendation(task, available_employees)

        if not available_employees:
            return {
                "recommended_employee_id": None,
                "recommended_employee_name": None,
                "confidence_score": 0,
                "reasoning": "No available employees to assign",
                "alternatives": [],
                "warnings": ["No employees are available for assignment"],
            }

        data = {
            "task": {
                "id": task.get("id"),
                "name": task.get("name"),
                "description": task.get("description", "")[:500],  # Truncate long descriptions
                "estimated_hours": task.get("planned_hours", 0) or task.get("remaining_hours", 0),
                "priority": task.get("priority", "1"),
                "deadline": task.get("date_deadline"),
                "tags": task.get("tag_ids", []),
            },
            "candidates": [
                {
                    "id": e.get("user_id") or e.get("id"),
                    "name": e.get("employee_name") or e.get("name"),
                    "current_workload_hours": e.get("remaining_hours", 0),
                    "current_task_count": e.get("task_count", 0),
                    "utilization_percentage": e.get("utilization", 0),
                    "high_priority_tasks": e.get("high_priority", 0),
                    "overdue_tasks": e.get("overdue", 0),
                }
                for e in available_employees[:10]  # Limit to top 10 candidates
            ],
        }

        try:
            recommendation = await self.ai.analyze_json(
                prompt=TASK_DISTRIBUTION_PROMPT,
                data=data,
                system_instruction=(
                    "You are a task assignment optimizer. Recommend the best employee "
                    "based on their current workload, capacity, and the task requirements. "
                    "Prioritize balanced workload distribution."
                ),
            )

            return recommendation

        except Exception as e:
            logger.error(f"AI assignment recommendation failed: {e}")
            return self._basic_assignment_recommendation(task, available_employees)

    def _basic_assignment_recommendation(
        self,
        task: Dict,
        available_employees: List[Dict],
    ) -> Dict[str, Any]:
        """Fallback basic assignment without AI."""
        if not available_employees:
            return {
                "recommended_employee_id": None,
                "recommended_employee_name": None,
                "confidence_score": 0,
                "reasoning": "No available employees",
                "alternatives": [],
                "warnings": ["No employees available for assignment"],
            }

        # Sort by utilization (lowest first)
        sorted_employees = sorted(
            available_employees,
            key=lambda x: x.get("utilization", 0),
        )

        best = sorted_employees[0]

        return {
            "recommended_employee_id": best.get("user_id") or best.get("id"),
            "recommended_employee_name": best.get("employee_name") or best.get("name"),
            "confidence_score": 70,  # Default confidence for basic recommendation
            "reasoning": f"Selected based on lowest current workload ({best.get('utilization', 0):.1f}% utilization)",
            "alternatives": [
                {
                    "id": e.get("user_id") or e.get("id"),
                    "name": e.get("employee_name") or e.get("name"),
                    "score": max(0, 100 - e.get("utilization", 0)),
                    "reason": f"{e.get('utilization', 0):.1f}% utilization",
                }
                for e in sorted_employees[1:4]
            ],
            "warnings": [],
        }

    async def suggest_rebalancing(
        self,
        team_workload: Dict,
    ) -> Dict[str, Any]:
        """
        Suggest task rebalancing when workload is uneven.

        Args:
            team_workload: Team workload summary with employee details

        Returns:
            Rebalancing suggestions
        """
        employees = team_workload.get("employees", [])

        overloaded = [e for e in employees if e.get("status") == "overloaded"]
        underutilized = [e for e in employees if e.get("status") == "underutilized"]

        if not overloaded or not underutilized:
            return {
                "rebalancing_needed": False,
                "message": "No significant workload imbalance detected",
                "suggestions": [],
            }

        suggestions = []
        for over in overloaded:
            for under in underutilized:
                capacity_available = (
                    DEFAULT_WEEKLY_HOURS * WORKLOAD_OVERLOADED_THRESHOLD
                    - under.get("remaining_hours", 0)
                )
                if capacity_available > 0:
                    suggestions.append({
                        "from_employee": over.get("employee_name"),
                        "from_id": over.get("user_id"),
                        "to_employee": under.get("employee_name"),
                        "to_id": under.get("user_id"),
                        "hours_to_transfer": min(
                            capacity_available,
                            over.get("remaining_hours", 0) - DEFAULT_WEEKLY_HOURS * 0.6,
                        ),
                        "reason": f"Transfer tasks to balance workload ({over.get('utilization', 0):.0f}% -> {under.get('utilization', 0):.0f}%)",
                    })

        return {
            "rebalancing_needed": True,
            "message": f"Found {len(overloaded)} overloaded and {len(underutilized)} underutilized employees",
            "suggestions": suggestions[:5],  # Limit to top 5 suggestions
        }
