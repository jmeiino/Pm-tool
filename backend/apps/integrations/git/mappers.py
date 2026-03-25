"""Mapping-Funktionen zwischen GitHub- und lokalen Datenformaten."""

from apps.projects.models import Issue


GITHUB_LABEL_TO_ISSUE_TYPE = {
    "bug": Issue.IssueType.BUG,
    "enhancement": Issue.IssueType.STORY,
    "feature": Issue.IssueType.STORY,
    "epic": Issue.IssueType.EPIC,
}

GITHUB_STATE_MAP = {
    "open": "to_do",
    "closed": "done",
}


def github_labels_to_issue_type(labels: list[dict]) -> str:
    """Leite Issue-Typ aus GitHub Labels ab."""
    for label in labels:
        label_name = label.get("name", "").lower()
        if label_name in GITHUB_LABEL_TO_ISSUE_TYPE:
            return GITHUB_LABEL_TO_ISSUE_TYPE[label_name]
    return Issue.IssueType.TASK


def github_labels_to_priority(labels: list[dict]) -> str:
    """Leite Priorität aus GitHub Labels ab."""
    priority_map = {
        "priority: critical": Issue.Priority.HIGHEST,
        "priority: high": Issue.Priority.HIGH,
        "priority: medium": Issue.Priority.MEDIUM,
        "priority: low": Issue.Priority.LOW,
    }
    for label in labels:
        label_name = label.get("name", "").lower()
        if label_name in priority_map:
            return priority_map[label_name]
    return Issue.Priority.MEDIUM


def github_issue_to_local(gh_issue: dict, project, repo_full_name: str) -> dict:
    """Map GitHub Issue API-Response auf lokale Issue Model-Felder."""
    labels = gh_issue.get("labels", [])

    return {
        "project": project,
        "title": gh_issue.get("title", ""),
        "description": gh_issue.get("body") or "",
        "issue_type": github_labels_to_issue_type(labels),
        "status": GITHUB_STATE_MAP.get(gh_issue.get("state", "open"), "to_do"),
        "priority": github_labels_to_priority(labels),
        "due_date": None,
        "github_issue_id": gh_issue.get("id"),
        "github_issue_number": gh_issue.get("number"),
        "github_repo_full_name": repo_full_name,
    }
