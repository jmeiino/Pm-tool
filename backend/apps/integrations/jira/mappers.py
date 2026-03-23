"""Mapping-Funktionen zwischen Jira- und lokalen Datenformaten."""

from apps.projects.models import Issue

JIRA_PRIORITY_MAP = {
    "Highest": Issue.Priority.HIGHEST,
    "High": Issue.Priority.HIGH,
    "Medium": Issue.Priority.MEDIUM,
    "Low": Issue.Priority.LOW,
    "Lowest": Issue.Priority.LOWEST,
}

JIRA_STATUS_MAP = {
    "To Do": "to_do",
    "Open": "to_do",
    "Backlog": "to_do",
    "In Progress": "in_progress",
    "In Review": "in_review",
    "Review": "in_review",
    "Done": "done",
    "Closed": "done",
    "Resolved": "done",
}

JIRA_ISSUE_TYPE_MAP = {
    "Epic": Issue.IssueType.EPIC,
    "Story": Issue.IssueType.STORY,
    "Task": Issue.IssueType.TASK,
    "Bug": Issue.IssueType.BUG,
    "Sub-task": Issue.IssueType.SUBTASK,
    "Subtask": Issue.IssueType.SUBTASK,
}


def jira_priority_to_local(jira_priority: str | None) -> str:
    if not jira_priority:
        return Issue.Priority.MEDIUM
    return JIRA_PRIORITY_MAP.get(jira_priority, Issue.Priority.MEDIUM)


def jira_status_to_local(jira_status: str | None) -> str:
    if not jira_status:
        return "to_do"
    return JIRA_STATUS_MAP.get(jira_status, jira_status.lower().replace(" ", "_"))


def jira_issue_type_to_local(jira_type: str | None) -> str:
    if not jira_type:
        return Issue.IssueType.TASK
    return JIRA_ISSUE_TYPE_MAP.get(jira_type, Issue.IssueType.TASK)


def jira_issue_to_local(jira_data: dict, project) -> dict:
    """Map Jira issue data to local Issue model fields."""
    fields = jira_data.get("fields", {})

    _assignee = fields.get("assignee")  # noqa: F841 — reserved for future user-matching
    _reporter = fields.get("reporter")  # noqa: F841 — reserved for future user-matching

    return {
        "project": project,
        "title": fields.get("summary", ""),
        "description": fields.get("description") or "",
        "issue_type": jira_issue_type_to_local(
            fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None
        ),
        "status": jira_status_to_local(fields.get("status", {}).get("name") if fields.get("status") else None),
        "priority": jira_priority_to_local(fields.get("priority", {}).get("name") if fields.get("priority") else None),
        "story_points": fields.get("story_points") or fields.get("customfield_10016"),
        "due_date": fields.get("duedate"),
        "jira_issue_id": jira_data.get("id"),
        "jira_issue_key": jira_data.get("key"),
        "jira_updated_at": fields.get("updated"),
    }


def local_issue_to_jira(issue) -> dict:
    """Map local Issue model to Jira create/update payload."""
    local_to_jira_priority = {v: k for k, v in JIRA_PRIORITY_MAP.items()}
    local_to_jira_type = {v: k for k, v in JIRA_ISSUE_TYPE_MAP.items()}

    fields = {
        "summary": issue.title,
        "description": issue.description or "",
        "issuetype": {"name": local_to_jira_type.get(issue.issue_type, "Task")},
        "priority": {"name": local_to_jira_priority.get(issue.priority, "Medium")},
    }

    if issue.due_date:
        fields["duedate"] = issue.due_date.isoformat()

    if issue.story_points:
        fields["story_points"] = issue.story_points

    return fields
