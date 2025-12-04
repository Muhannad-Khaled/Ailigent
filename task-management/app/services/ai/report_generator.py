"""AI-Powered Report Generation."""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.services.ai.gemini_client import GeminiClient
from app.services.ai.prompts import PRODUCTIVITY_REPORT_PROMPT

logger = logging.getLogger(__name__)


class AIReportGenerator:
    """Generates AI-enhanced productivity reports."""

    def __init__(self, gemini_client: GeminiClient):
        self.ai = gemini_client

    async def generate_productivity_report(
        self,
        completion_metrics: Dict,
        stage_metrics: List[Dict],
        employee_performance: List[Dict],
        report_type: str = "daily",
    ) -> Dict[str, Any]:
        """
        Generate comprehensive productivity report with AI insights.

        Args:
            completion_metrics: Task completion statistics
            stage_metrics: Stage distribution data
            employee_performance: Employee workload/performance data
            report_type: Type of report (daily, weekly, monthly)

        Returns:
            Complete productivity report with AI insights
        """
        report_id = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"

        base_report = {
            "report_id": report_id,
            "report_type": report_type,
            "period_start": completion_metrics.get("period_start"),
            "period_end": completion_metrics.get("period_end"),
            "generated_at": datetime.now().isoformat(),
            "metrics": completion_metrics,
            "stage_metrics": stage_metrics,
            "team_performance": employee_performance,
        }

        if not self.ai.is_available():
            # Return basic report without AI insights
            base_report.update({
                "executive_summary": self._generate_basic_summary(completion_metrics),
                "insights": self._generate_basic_insights(completion_metrics, stage_metrics),
                "recommendations": self._generate_basic_recommendations(completion_metrics, employee_performance),
                "risks": self._identify_basic_risks(completion_metrics, employee_performance),
                "top_performers": [],
                "needs_improvement": [],
            })
            return base_report

        # Prepare data for AI analysis
        data = {
            "completion_metrics": completion_metrics,
            "stage_distribution": [
                {
                    "stage": s.get("stage_name"),
                    "task_count": s.get("task_count"),
                    "percentage": s.get("percentage"),
                    "is_closed": s.get("is_closed"),
                }
                for s in stage_metrics
            ],
            "team_performance": [
                {
                    "name": e.get("employee_name") or e.get("name"),
                    "task_count": e.get("task_count", 0),
                    "utilization": e.get("utilization", 0),
                    "overdue": e.get("overdue", 0),
                    "status": e.get("status", "unknown"),
                }
                for e in employee_performance
            ],
            "report_type": report_type,
        }

        try:
            ai_insights = await self.ai.analyze_json(
                prompt=PRODUCTIVITY_REPORT_PROMPT,
                data=data,
                system_instruction=(
                    "You are a productivity analyst. Generate actionable insights "
                    "based on the metrics provided. Be specific and data-driven. "
                    "Focus on trends and areas that need attention."
                ),
            )

            base_report.update({
                "executive_summary": ai_insights.get("executive_summary", ""),
                "key_metrics_analysis": ai_insights.get("key_metrics", {}),
                "insights": ai_insights.get("insights", []),
                "recommendations": ai_insights.get("recommendations", []),
                "risks": ai_insights.get("risks", []),
                "top_performers": ai_insights.get("team_performance", {}).get("top_performers", []),
                "needs_improvement": ai_insights.get("team_performance", {}).get("improvement_needed", []),
                "trend_analysis": ai_insights.get("team_performance", {}).get("trend_analysis", ""),
            })

        except Exception as e:
            logger.error(f"AI report generation failed: {e}")
            base_report.update({
                "executive_summary": self._generate_basic_summary(completion_metrics),
                "insights": self._generate_basic_insights(completion_metrics, stage_metrics),
                "recommendations": self._generate_basic_recommendations(completion_metrics, employee_performance),
                "risks": self._identify_basic_risks(completion_metrics, employee_performance),
                "top_performers": [],
                "needs_improvement": [],
            })

        return base_report

    def _generate_basic_summary(self, metrics: Dict) -> str:
        """Generate basic executive summary without AI."""
        completion_rate = metrics.get("completion_rate", 0)
        on_time_rate = metrics.get("on_time_rate", 0)
        overdue = metrics.get("overdue", 0)

        if completion_rate >= 80 and on_time_rate >= 80:
            status = "performing well"
        elif completion_rate >= 60:
            status = "showing moderate performance"
        else:
            status = "needs attention"

        return (
            f"Team is {status} with a {completion_rate:.1f}% completion rate "
            f"and {on_time_rate:.1f}% on-time delivery. "
            f"Currently {overdue} task(s) are overdue."
        )

    def _generate_basic_insights(
        self,
        metrics: Dict,
        stage_metrics: List[Dict],
    ) -> List[str]:
        """Generate basic insights without AI."""
        insights = []

        completion_rate = metrics.get("completion_rate", 0)
        if completion_rate < 50:
            insights.append(
                f"Completion rate ({completion_rate:.1f}%) is below 50%. "
                "Review task prioritization and resource allocation."
            )

        on_time_rate = metrics.get("on_time_rate", 0)
        if on_time_rate < 70:
            insights.append(
                f"On-time delivery ({on_time_rate:.1f}%) needs improvement. "
                "Consider reviewing deadline setting practices."
            )

        # Check for stage bottlenecks
        for stage in stage_metrics:
            if stage.get("percentage", 0) > 30 and not stage.get("is_closed"):
                insights.append(
                    f"{stage['stage_name']} stage has {stage['percentage']:.1f}% "
                    "of all tasks. Consider reviewing this stage's workflow."
                )

        if not insights:
            insights.append("No significant issues detected in current period.")

        return insights

    def _generate_basic_recommendations(
        self,
        metrics: Dict,
        employees: List[Dict],
    ) -> List[str]:
        """Generate basic recommendations without AI."""
        recommendations = []

        overdue = metrics.get("overdue", 0)
        if overdue > 0:
            recommendations.append(
                f"Address the {overdue} overdue task(s) immediately. "
                "Prioritize by impact and reassign if necessary."
            )

        overloaded = [e for e in employees if e.get("status") == "overloaded"]
        if overloaded:
            names = ", ".join(e.get("employee_name", "Unknown")[:20] for e in overloaded[:3])
            recommendations.append(
                f"Redistribute tasks from overloaded team members ({names}). "
                "Consider deadline extensions where possible."
            )

        underutilized = [e for e in employees if e.get("status") == "underutilized"]
        if underutilized:
            recommendations.append(
                f"{len(underutilized)} team member(s) have capacity available. "
                "Consider assigning more tasks to balance the workload."
            )

        if not recommendations:
            recommendations.append(
                "Continue current practices. Monitor metrics for any changes."
            )

        return recommendations

    def _identify_basic_risks(
        self,
        metrics: Dict,
        employees: List[Dict],
    ) -> List[str]:
        """Identify basic risks without AI."""
        risks = []

        overdue = metrics.get("overdue", 0)
        total = metrics.get("total_created", 0)
        if total > 0 and (overdue / total) > 0.2:
            risks.append(
                f"High overdue ratio ({overdue}/{total}). "
                "Risk of cascading delays and team burnout."
            )

        heavily_overloaded = [
            e for e in employees
            if e.get("utilization", 0) > 100
        ]
        if heavily_overloaded:
            risks.append(
                f"{len(heavily_overloaded)} employee(s) are over 100% utilization. "
                "High risk of burnout and quality issues."
            )

        return risks

    async def generate_daily_summary(
        self,
        tasks_completed: int,
        tasks_created: int,
        overdue_count: int,
        blocked_count: int,
    ) -> Dict[str, Any]:
        """Generate a quick daily summary."""
        return {
            "date": date.today().isoformat(),
            "summary": {
                "tasks_completed": tasks_completed,
                "tasks_created": tasks_created,
                "overdue_count": overdue_count,
                "blocked_count": blocked_count,
                "net_progress": tasks_completed - tasks_created,
            },
            "status": (
                "positive" if tasks_completed >= tasks_created
                else "attention_needed"
            ),
            "headline": (
                f"Completed {tasks_completed} tasks. "
                f"{overdue_count} overdue, {blocked_count} blocked."
            ),
        }
