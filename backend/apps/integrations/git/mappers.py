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
    """Leite Prioritaet aus GitHub Labels ab."""
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

    data = {
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

    # Assignee mappen (#18)
    assignee = gh_issue.get("assignee")
    if assignee:
        data["github_assignee_login"] = assignee.get("login", "")
    else:
        data["github_assignee_login"] = ""

    return data


LOCAL_STATUS_TO_GITHUB_STATE = {
    "to_do": "open",
    "in_progress": "open",
    "in_review": "open",
    "done": "closed",
}

LOCAL_TYPE_TO_GITHUB_LABEL = {
    Issue.IssueType.BUG: "bug",
    Issue.IssueType.STORY: "enhancement",
    Issue.IssueType.EPIC: "epic",
}


def local_issue_to_github(issue) -> dict:
    """Map lokales Issue auf GitHub Issue Update-Payload."""
    payload: dict = {
        "title": issue.title,
        "body": issue.description or "",
        "state": LOCAL_STATUS_TO_GITHUB_STATE.get(issue.status, "open"),
    }

    # Labels aus Issue-Typ ableiten
    label = LOCAL_TYPE_TO_GITHUB_LABEL.get(issue.issue_type)
    if label:
        payload["labels"] = [label]

    # Assignee (#18)
    if issue.github_assignee_login:
        payload["assignees"] = [issue.github_assignee_login]

    return payload


def github_milestone_to_sprint(milestone: dict, project) -> dict:
    """Map GitHub Milestone auf Sprint Model-Felder (#21)."""
    from django.utils.dateparse import parse_date

    state = milestone.get("state", "open")
    if state == "closed":
        sprint_status = "closed"
    else:
        sprint_status = "active"

    due_on = milestone.get("due_on")
    end_date = None
    if due_on:
        end_date = parse_date(due_on[:10])

    return {
        "project": project,
        "name": milestone.get("title", ""),
        "goal": milestone.get("description") or "",
        "end_date": end_date,
        "status": sprint_status,
        "github_milestone_id": milestone.get("id"),
    }
