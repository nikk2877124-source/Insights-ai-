"""Business insights generation.

This module provides a dedicated service for translating dataset profiling
metadata into business-oriented AI insights.

Design goals:
- SOLID: keep prompt-building and orchestration separate from the low-level
  LLM client.
- Safety: do not send raw dataset contents to the model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from app.services.ai_services import AIService


@dataclass(frozen=True)
class BusinessInsightsSections:
    """Container for the required insight sections."""

    executive_summary: str = "Executive Summary"
    key_findings: str = "Key Findings"
    risks: str = "Risks"
    opportunities: str = "Opportunities"
    recommended_actions: str = "Recommended Actions"


class BusinessInsightService:
    """Generate business insights from dataset profile metadata.

    The service expects:
    - dataset_profile: a profile dict as stored in DatasetProfile.profile_json
      (expected to include a "summary" key produced by ProfilingService).
    - summary_statistics: a small, derived structure containing only
      high-signal KPIs.

    It builds a structured prompt and asks Ollama to produce the requested
    sections.
    """

    def __init__(self, *, ai_service: AIService | None = None):
        """Create the service.

        Args:
            ai_service: optional dependency injection. If not provided, a
                default AIService instance is used.
        """

        self._ai_service = ai_service or AIService()
        self._sections = BusinessInsightsSections()

    @staticmethod
    def _normalize_summary_statistics(summary_statistics: Mapping[str, Any]) -> dict[str, Any]:
        """Ensure summary statistics is JSON-serializable and small."""
        if not isinstance(summary_statistics, Mapping):
            raise TypeError("summary_statistics must be a mapping")

        # Keep it safe: convert to plain dict with stable values.
        return json.loads(json.dumps(dict(summary_statistics), default=str))

    def build_prompt(
        self,
        *,
        dataset_profile: Mapping[str, Any],
        summary_statistics: Mapping[str, Any],
    ) -> str:
        """Build the structured prompt for Ollama.

        Important: only metadata/summary statistics are included.
        """

        # Prefer the profiling "summary" section if present, but also accept a
        # caller-provided small statistics dict.
        profile_summary = dataset_profile.get("summary") if isinstance(dataset_profile, Mapping) else None

        payload = {
            "summary_statistics": self._normalize_summary_statistics(summary_statistics),
            "profile_summary": json.loads(json.dumps(profile_summary, default=str)) if profile_summary is not None else None,
        }

        return (
            "You are an expert AI Business Analyst for InsightAI.\n\n"
            "Generate business-focused insights from dataset profiling metadata.\n"
            "You MUST NOT use or infer details that require raw dataset rows/values.\n\n"
            "RESPONSE FORMAT (plain text, no markdown):\n"
            f"1) {self._sections.executive_summary}\n"
            f"2) {self._sections.key_findings}\n"
            f"3) {self._sections.risks}\n"
            f"4) {self._sections.opportunities}\n"
            f"5) {self._sections.recommended_actions}\n\n"
            "RULES:\n"
            "- Keep each section 3-7 bullet points or short paragraphs (as appropriate).\n"
            "- Do not invent numbers; reference the provided statistics only.\n"
            "- If data is insufficient for a claim, state that clearly.\n\n"
            "INPUT (metadata only):\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        )

    def generate_business_insights(
        self,
        *,
        dataset_profile: Mapping[str, Any],
        summary_statistics: Mapping[str, Any],
    ) -> str:
        """Generate business insights.

        Args:
            dataset_profile: dataset profile JSON stored by the profiling flow.
            summary_statistics: a small derived dict of high-signal KPIs.

        Returns:
            The model output string containing all five required sections.
        """

        prompt = self.build_prompt(
            dataset_profile=dataset_profile,
            summary_statistics=summary_statistics,
        )
        return self._ai_service.generate_response(prompt)

