import hashlib
import json
import logging

from django.utils import timezone
from datetime import timedelta

from .client import get_ai_client
from .models import AIResult
from .prompts import (
    CONFLUENCE_ANALYSIS_SYSTEM_PROMPT,
    DAILY_PLAN_SYSTEM_PROMPT,
    DAILY_PLAN_USER_PROMPT,
    EXTRACT_ACTIONS_SYSTEM_PROMPT,
    GITHUB_REPO_ANALYSIS_SYSTEM_PROMPT,
    GITHUB_REPO_ANALYSIS_USER_PROMPT,
    PRIORITIZE_SYSTEM_PROMPT,
    SUMMARIZE_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class AIService:
    """Service-Klasse für KI-gestützte Funktionen."""

    CACHE_TTL_HOURS = 24

    def __init__(self):
        self.client = get_ai_client()

    def _compute_hash(self, content: str, result_type: str) -> str:
        """Berechnet einen Hash für den Cache-Schlüssel."""
        raw = f"{result_type}:{content}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _get_cached(self, content_hash: str, result_type: str):
        """Prüft ob ein gecachtes Ergebnis vorhanden ist."""
        try:
            cached = AIResult.objects.filter(
                content_hash=content_hash,
                result_type=result_type,
                expires_at__gt=timezone.now(),
            ).latest("created_at")
            return cached.result
        except AIResult.DoesNotExist:
            return None

    def _cache_result(self, content_hash: str, result_type: str, result, input_preview: str = ""):
        """Speichert ein Ergebnis im Cache."""
        return AIResult.objects.create(
            content_hash=content_hash,
            result_type=result_type,
            input_preview=input_preview[:500],
            result=result,
            model_used=self.client.default_model,
            tokens_used=0,
            expires_at=timezone.now() + timedelta(hours=self.CACHE_TTL_HOURS),
        )

    def suggest_daily_plan(self, todos: list, calendar_events: list, capacity_hours: float) -> dict:
        """Erstellt einen KI-gestützten Tagesplan."""
        tasks_str = json.dumps(todos, ensure_ascii=False, default=str)
        events_str = json.dumps(calendar_events, ensure_ascii=False, default=str)
        content = f"{tasks_str}{events_str}{capacity_hours}"
        content_hash = self._compute_hash(content, AIResult.ResultType.DAILY_PLAN)

        cached = self._get_cached(content_hash, AIResult.ResultType.DAILY_PLAN)
        if cached:
            return cached

        prompt = DAILY_PLAN_USER_PROMPT.format(
            tasks=tasks_str,
            calendar_events=events_str,
            capacity_hours=capacity_hours,
        )
        result = self.client.generate_json(prompt, system_prompt=DAILY_PLAN_SYSTEM_PROMPT)
        self._cache_result(content_hash, AIResult.ResultType.DAILY_PLAN, result, tasks_str[:500])
        return result

    def prioritize_todos(self, todos: list) -> list:
        """Priorisiert eine Liste von Aufgaben mittels KI."""
        content = json.dumps(todos, ensure_ascii=False, default=str)
        content_hash = self._compute_hash(content, AIResult.ResultType.PRIORITIZATION)

        cached = self._get_cached(content_hash, AIResult.ResultType.PRIORITIZATION)
        if cached:
            return cached

        prompt = f"Priorisiere folgende Aufgaben:\n{content}"
        result = self.client.generate_json(prompt, system_prompt=PRIORITIZE_SYSTEM_PROMPT)
        self._cache_result(content_hash, AIResult.ResultType.PRIORITIZATION, result, content[:500])
        return result

    def summarize_content(self, content: str, content_type: str = "text") -> str:
        """Fasst Inhalte zusammen."""
        content_hash = self._compute_hash(content, AIResult.ResultType.SUMMARY)

        cached = self._get_cached(content_hash, AIResult.ResultType.SUMMARY)
        if cached:
            return cached

        prompt = f"Fasse folgenden {content_type}-Inhalt zusammen:\n\n{content}"
        result = self.client.generate(prompt, system_prompt=SUMMARIZE_SYSTEM_PROMPT)
        self._cache_result(content_hash, AIResult.ResultType.SUMMARY, result, content[:500])
        return result

    def extract_action_items(self, text: str) -> list:
        """Extrahiert Aktionspunkte aus einem Text."""
        content_hash = self._compute_hash(text, AIResult.ResultType.ACTION_ITEMS)

        cached = self._get_cached(content_hash, AIResult.ResultType.ACTION_ITEMS)
        if cached:
            return cached

        prompt = f"Extrahiere alle Aktionspunkte aus folgendem Text:\n\n{text}"
        result = self.client.generate_json(prompt, system_prompt=EXTRACT_ACTIONS_SYSTEM_PROMPT)
        self._cache_result(content_hash, AIResult.ResultType.ACTION_ITEMS, result, text[:500])
        return result

    def analyze_github_repo(self, repo_data: dict) -> dict:
        """Analysiert ein GitHub-Repository."""
        content = json.dumps(repo_data, ensure_ascii=False, default=str)
        content_hash = self._compute_hash(content, AIResult.ResultType.REPO_ANALYSIS)

        cached = self._get_cached(content_hash, AIResult.ResultType.REPO_ANALYSIS)
        if cached:
            return cached

        prompt = GITHUB_REPO_ANALYSIS_USER_PROMPT.format(
            repo_name=repo_data.get("repo_name", ""),
            description=repo_data.get("description", ""),
            primary_language=repo_data.get("primary_language", ""),
            languages=repo_data.get("languages", ""),
            stars=repo_data.get("stars", 0),
            forks=repo_data.get("forks", 0),
            open_issues=repo_data.get("open_issues", 0),
            topics=", ".join(repo_data.get("topics", [])),
            readme=repo_data.get("readme", "")[:5000],
            recent_commits=repo_data.get("recent_commits", ""),
        )
        result = self.client.generate_json(prompt, system_prompt=GITHUB_REPO_ANALYSIS_SYSTEM_PROMPT)
        self._cache_result(content_hash, AIResult.ResultType.REPO_ANALYSIS, result, content[:500])
        return result

    def analyze_confluence_page(self, page_content: str) -> dict:
        """Analysiert eine Confluence-Seite."""
        content_hash = self._compute_hash(page_content, AIResult.ResultType.EXTRACTION)

        cached = self._get_cached(content_hash, AIResult.ResultType.EXTRACTION)
        if cached:
            return cached

        prompt = f"Analysiere folgende Confluence-Seite:\n\n{page_content}"
        result = self.client.generate_json(prompt, system_prompt=CONFLUENCE_ANALYSIS_SYSTEM_PROMPT)
        self._cache_result(content_hash, AIResult.ResultType.EXTRACTION, result, page_content[:500])
        return result
