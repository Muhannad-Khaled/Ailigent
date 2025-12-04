"""AI-Powered Bottleneck Detection."""

import logging
from datetime import datetime, date
from typing import Any, Dict, List

from app.core.constants import (
    BOTTLENECK_STAGE_CONGESTION,
    BOTTLENECK_BLOCKED_RATIO,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.prompts import BOTTLENECK_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class BottleneckDetector:
    """Analyzes task flow and identifies bottlenecks using AI."""

    def __init__(self, gemini_client: GeminiClient):
        self.ai = gemini_client

    async def detect_bottlenecks(
        self,
        tasks: List[Dict],
        employees: List[Dict],
        stages: List[Dict],
    ) -> Dict[str, Any]:
        """
        Comprehensive bottleneck analysis.

        Args:
            tasks: All tasks in the system
            employees: Employee workload data
            stages: Task stage information

        Returns:
            Analysis with bottlenecks, patterns, and priority actions
        """
        # Calculate metrics for analysis
        stage_metrics = self._calculate_stage_metrics(tasks, stages)
        employee_metrics = self._calculate_employee_metrics(employees)
        time_patterns = self._analyze_time_patterns(tasks)
        blocked_analysis = self._analyze_blocked_tasks(tasks)

        if not self.ai.is_available():
            return self._basic_bottleneck_analysis(
                stage_metrics, employee_metrics, blocked_analysis
            )

        data = {
            "stage_analysis": stage_metrics,
            "employee_analysis": employee_metrics,
            "time_patterns": time_patterns,
            "blocked_tasks": blocked_analysis,
            "summary": {
                "total_tasks": len(tasks),
                "overdue_count": sum(1 for t in tasks if self._is_overdue(t)),
                "blocked_count": sum(
                    1 for t in tasks if t.get("kanban_state") == "blocked"
                ),
                "high_priority_count": sum(
                    1 for t in tasks if t.get("priority") in ("2", "3")
                ),
            },
        }

        try:
            analysis = await self.ai.analyze_json(
                prompt=BOTTLENECK_ANALYSIS_PROMPT,
                data=data,
                system_instruction=(
                    "You are a process optimization expert. Identify bottlenecks "
                    "in the workflow and provide specific, actionable recommendations. "
                    "Focus on issues that have the highest impact on productivity."
                ),
            )

            # Add severity counts
            bottlenecks = analysis.get("bottlenecks", [])
            analysis["critical_count"] = sum(
                1 for b in bottlenecks if b.get("severity") == SEVERITY_CRITICAL
            )
            analysis["high_count"] = sum(
                1 for b in bottlenecks if b.get("severity") == SEVERITY_HIGH
            )
            analysis["medium_count"] = sum(
                1 for b in bottlenecks if b.get("severity") == SEVERITY_MEDIUM
            )
            analysis["low_count"] = sum(
                1 for b in bottlenecks if b.get("severity") == SEVERITY_LOW
            )

            return analysis

        except Exception as e:
            logger.error(f"AI bottleneck analysis failed: {e}")
            return self._basic_bottleneck_analysis(
                stage_metrics, employee_metrics, blocked_analysis
            )

    def _calculate_stage_metrics(
        self,
        tasks: List[Dict],
        stages: List[Dict],
    ) -> List[Dict]:
        """Calculate metrics per stage."""
        total_tasks = len(tasks)
        if total_tasks == 0:
            return []

        # Group tasks by stage
        stage_tasks = {}
        for task in tasks:
            stage_id = None
            stage_info = task.get("stage_id")
            if isinstance(stage_info, list) and len(stage_info) > 0:
                stage_id = stage_info[0]
            if stage_id not in stage_tasks:
                stage_tasks[stage_id] = []
            stage_tasks[stage_id].append(task)

        metrics = []
        for stage in stages:
            stage_id = stage.get("id")
            tasks_in_stage = stage_tasks.get(stage_id, [])
            count = len(tasks_in_stage)
            ratio = count / total_tasks if total_tasks > 0 else 0

            overdue_count = sum(1 for t in tasks_in_stage if self._is_overdue(t))
            blocked_count = sum(
                1 for t in tasks_in_stage if t.get("kanban_state") == "blocked"
            )

            metrics.append({
                "stage_id": stage_id,
                "stage_name": stage.get("name"),
                "is_closed": stage.get("is_closed", False),
                "task_count": count,
                "percentage": round(ratio * 100, 1),
                "overdue_in_stage": overdue_count,
                "blocked_in_stage": blocked_count,
                "is_bottleneck": ratio > BOTTLENECK_STAGE_CONGESTION,
            })

        return metrics

    def _calculate_employee_metrics(self, employees: List[Dict]) -> List[Dict]:
        """Calculate metrics per employee."""
        return [
            {
                "employee_name": e.get("employee_name") or e.get("name"),
                "user_id": e.get("user_id"),
                "task_count": e.get("task_count", 0),
                "remaining_hours": e.get("remaining_hours", 0),
                "utilization": e.get("utilization", 0),
                "overdue_count": e.get("overdue", 0),
                "high_priority_count": e.get("high_priority", 0),
                "status": e.get("status", "balanced"),
            }
            for e in employees
        ]

    def _analyze_time_patterns(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Analyze time-based patterns in tasks."""
        overdue_tasks = [t for t in tasks if self._is_overdue(t)]

        if not overdue_tasks:
            return {
                "overdue_pattern": "No overdue tasks detected",
                "average_days_overdue": 0,
                "most_overdue_days": 0,
            }

        today = date.today()
        days_overdue = []

        for task in overdue_tasks:
            deadline = task.get("date_deadline")
            if deadline:
                try:
                    deadline_date = datetime.fromisoformat(deadline).date()
                    days = (today - deadline_date).days
                    days_overdue.append(days)
                except (ValueError, TypeError):
                    pass

        if not days_overdue:
            return {
                "overdue_pattern": "Unable to calculate overdue days",
                "average_days_overdue": 0,
                "most_overdue_days": 0,
            }

        avg_days = sum(days_overdue) / len(days_overdue)

        return {
            "overdue_pattern": f"{len(overdue_tasks)} tasks overdue",
            "average_days_overdue": round(avg_days, 1),
            "most_overdue_days": max(days_overdue),
            "distribution": {
                "1_day": sum(1 for d in days_overdue if d == 1),
                "2_3_days": sum(1 for d in days_overdue if 2 <= d <= 3),
                "4_7_days": sum(1 for d in days_overdue if 4 <= d <= 7),
                "over_week": sum(1 for d in days_overdue if d > 7),
            },
        }

    def _analyze_blocked_tasks(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Analyze blocked tasks."""
        blocked = [t for t in tasks if t.get("kanban_state") == "blocked"]
        total = len(tasks)

        blocked_ratio = len(blocked) / total if total > 0 else 0

        return {
            "blocked_count": len(blocked),
            "blocked_ratio": round(blocked_ratio * 100, 1),
            "is_concerning": blocked_ratio > BOTTLENECK_BLOCKED_RATIO,
            "blocked_tasks": [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "priority": t.get("priority"),
                    "assignees": t.get("user_ids", []),
                }
                for t in blocked[:10]  # Limit to 10
            ],
        }

    def _is_overdue(self, task: Dict) -> bool:
        """Check if a task is overdue."""
        deadline = task.get("date_deadline")
        if not deadline:
            return False
        try:
            deadline_date = datetime.fromisoformat(deadline).date()
            return deadline_date < date.today()
        except (ValueError, TypeError):
            return False

    def _basic_bottleneck_analysis(
        self,
        stage_metrics: List[Dict],
        employee_metrics: List[Dict],
        blocked_analysis: Dict,
    ) -> Dict[str, Any]:
        """Fallback basic analysis without AI."""
        bottlenecks = []

        # Stage bottlenecks
        for stage in stage_metrics:
            if stage.get("is_bottleneck") and not stage.get("is_closed"):
                severity = SEVERITY_HIGH if stage["percentage"] > 40 else SEVERITY_MEDIUM
                bottlenecks.append({
                    "type": "stage",
                    "location": stage["stage_name"],
                    "severity": severity,
                    "impact": f"{stage['task_count']} tasks ({stage['percentage']}%)",
                    "root_cause": f"Tasks accumulating in {stage['stage_name']} stage",
                    "recommendation": f"Review workflow in {stage['stage_name']}, consider adding resources",
                })

        # Employee bottlenecks
        overloaded = [e for e in employee_metrics if e.get("status") == "overloaded"]
        for emp in overloaded:
            if emp.get("overdue_count", 0) > 2:
                bottlenecks.append({
                    "type": "employee",
                    "location": emp["employee_name"],
                    "severity": SEVERITY_HIGH,
                    "impact": f"{emp['overdue_count']} overdue tasks",
                    "root_cause": f"Employee overloaded with {emp['utilization']:.0f}% utilization",
                    "recommendation": "Redistribute tasks to reduce workload",
                })

        # Blocked tasks bottleneck
        if blocked_analysis.get("is_concerning"):
            bottlenecks.append({
                "type": "process",
                "location": "Blocked Tasks",
                "severity": SEVERITY_HIGH,
                "impact": f"{blocked_analysis['blocked_count']} tasks blocked",
                "root_cause": "High number of blocked tasks indicates process issues",
                "recommendation": "Review blocked tasks and resolve blockers",
            })

        # Sort by severity
        severity_order = {
            SEVERITY_CRITICAL: 0,
            SEVERITY_HIGH: 1,
            SEVERITY_MEDIUM: 2,
            SEVERITY_LOW: 3,
        }
        bottlenecks.sort(key=lambda x: severity_order.get(x.get("severity"), 99))

        return {
            "bottlenecks": bottlenecks,
            "patterns": [],
            "priority_actions": [b["recommendation"] for b in bottlenecks[:3]],
            "summary": f"Detected {len(bottlenecks)} potential bottleneck(s)",
            "critical_count": sum(1 for b in bottlenecks if b["severity"] == SEVERITY_CRITICAL),
            "high_count": sum(1 for b in bottlenecks if b["severity"] == SEVERITY_HIGH),
            "medium_count": sum(1 for b in bottlenecks if b["severity"] == SEVERITY_MEDIUM),
            "low_count": sum(1 for b in bottlenecks if b["severity"] == SEVERITY_LOW),
        }
