# Datenmodell

Uebersicht aller Django-Modelle, ihrer Beziehungen und wichtigsten Felder.

---

## Modell-Diagramm

```
User
 ├── Project ──── Sprint
 │       └── Issue ──── Comment
 │             │        Label ◄──► Issue (M2M)
 │             │
 ├── PersonalTodo ◄── (linked_issue)
 │       │
 ├── DailyPlan ──── DailyPlanItem ──► PersonalTodo
 │       │
 ├── WeeklyPlan ──► DailyPlan (M2M)
 │
 ├── IntegrationConfig ──── SyncLog
 │
 ├── CalendarEvent
 ├── Notification
 │
 ├── AgentCompanyConfig ──── AgentProfile
 │                     └──── AgentTask ──── AgentMessage
 │
 ConfluencePage (standalone)
 GitActivity ──► Project, Issue
 GitRepoAnalysis (standalone)
 AIResult (Cache)
```

---

## Modelle im Detail

### core

| Modell | Felder | Beschreibung |
|---|---|---|
| `TimeStampedModel` | `created_at`, `updated_at` | Abstrakte Basis fuer alle Modelle |

### users

| Modell | Felder | Beschreibung |
|---|---|---|
| `User` | `username`, `email`, `timezone`, `daily_capacity_hours`, `preferences` (JSON) | Erweitertes Django-User-Modell |

### projects

| Modell | Wichtige Felder | Beschreibung |
|---|---|---|
| `Project` | `name`, `key`, `description`, `owner` (FK→User), `status` (active/archived/paused), `jira_sync`, `jira_project_key` | Projekt mit optionaler Jira-Verknuepfung |
| `Sprint` | `name`, `project` (FK), `status` (planned/active/closed), `start_date`, `end_date`, `jira_sprint_id` | Sprint innerhalb eines Projekts |
| `Issue` | `title`, `project` (FK), `sprint` (FK), `assignee` (FK→User), `reporter` (FK→User), `issue_type` (Epic/Story/Task/Bug/Subtask), `priority` (highest–lowest), `status` (backlog→done), `jira_id`, `github_id`, `labels` (M2M) | Aufgabe/Ticket |
| `Comment` | `issue` (FK), `author` (FK→User), `body`, `jira_comment_id` | Kommentar zu einem Issue |
| `Label` | `name`, `color` | Farbiges Label (M2M mit Issue) |

### todos

| Modell | Wichtige Felder | Beschreibung |
|---|---|---|
| `PersonalTodo` | `user` (FK), `title`, `description`, `source` (manual/jira/confluence/email/teams/ai), `priority` (1–5), `status` (open/in_progress/done/cancelled), `due_date`, `estimated_hours`, `linked_issue` (FK→Issue), `ai_confidence` | Persoenliche Aufgabe |
| `DailyPlan` | `user` (FK), `date`, `ai_summary`, `capacity_hours`, `notes` | Tagesplan |
| `DailyPlanItem` | `daily_plan` (FK), `todo` (FK→PersonalTodo), `order`, `time_block_start`, `time_block_minutes`, `completed` | Zeitblock im Tagesplan |
| `WeeklyPlan` | `user` (FK), `week_start`, `daily_plans` (M2M→DailyPlan), `goals`, `retrospective` | Wochenplan |

### integrations

| Modell | Wichtige Felder | Beschreibung |
|---|---|---|
| `IntegrationConfig` | `user` (FK), `integration_type` (jira/confluence/github/microsoft), `credentials` (JSON), `settings` (JSON), `is_active`, `last_sync_at` | Integration-Konfiguration |
| `SyncLog` | `integration` (FK), `status` (success/partial/failed), `records_created`, `records_updated`, `errors` (JSON), `duration_seconds` | Protokoll eines Sync-Vorgangs |
| `ConfluencePage` | `confluence_page_id`, `space_key`, `title`, `content_text`, `author`, `ai_summary`, `ai_action_items` (JSON), `ai_decisions` (JSON), `ai_risks` (JSON) | Importierte Confluence-Seite |
| `CalendarEvent` | `user` (FK), `external_id`, `title`, `start_time`, `end_time`, `location`, `attendees` (JSON), `is_all_day` | Synchronisiertes Kalender-Event |
| `GitActivity` | `project` (FK), `event_type` (commit/pr_opened/pr_merged/pr_closed), `title`, `author`, `url`, `linked_issue` (FK→Issue), `sha`, `branch` | GitHub-Commit oder Pull Request |
| `GitRepoAnalysis` | `repo_full_name`, `description`, `languages` (JSON), `stars`, `forks`, `topics` (JSON), `ai_summary`, `ai_tech_stack` (JSON), `ai_strengths` (JSON), `ai_improvements` (JSON), `ai_next_steps` (JSON) | KI-analysiertes Repository |

### ai

| Modell | Wichtige Felder | Beschreibung |
|---|---|---|
| `AIResult` | `content_hash`, `result_type`, `provider`, `model`, `result` (JSON), `expires_at` | Gecachtes KI-Ergebnis (24h TTL) |

### agents

| Modell | Wichtige Felder | Beschreibung |
|---|---|---|
| `AgentCompanyConfig` | `user` (FK), `name`, `base_url`, `api_key`, `webhook_secret`, `is_active` | Konfiguration fuer Agent-Microservice |
| `AgentProfile` | `company` (FK), `external_id`, `name`, `role` (ceo/department_head/specialist/qa), `department`, `status` (idle/working/waiting/offline), `capabilities` (JSON), `ai_provider` | KI-Agent-Profil |
| `AgentTask` | `company` (FK), `issue` (FK→Issue), `assigned_agent` (FK→AgentProfile), `status` (pending→completed/failed/cancelled), `priority` (1–5), `task_type` (software/content/design/research), `instructions`, `result_summary`, `deliverables` (JSON) | Delegierte Aufgabe |
| `AgentMessage` | `task` (FK), `sender_agent` (FK), `sender_user` (FK), `message_type` (text/decision/question/handoff/status_change/deliverable/error/system), `content`, `is_decision_pending`, `decision_options` (JSON) | Nachricht innerhalb einer Aufgabe |

### notifications

| Modell | Wichtige Felder | Beschreibung |
|---|---|---|
| `Notification` | `user` (FK), `notification_type`, `title`, `message`, `severity` (info/warning/error), `is_read`, `link` | Benutzer-Benachrichtigung |
