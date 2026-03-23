// Projekte
export interface Project {
  id: number;
  name: string;
  key: string;
  description: string;
  status: "active" | "archived" | "paused";
  is_synced: boolean;
  jira_project_key: string | null;
  issue_count: number;
  created_at: string;
  updated_at: string;
}

export interface Sprint {
  id: number;
  project: number;
  name: string;
  goal: string;
  start_date: string | null;
  end_date: string | null;
  status: "planned" | "active" | "closed";
  jira_sprint_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Issue {
  id: number;
  key: string;
  title: string;
  description: string;
  issue_type: "epic" | "story" | "task" | "bug" | "subtask";
  status: string;
  priority: "highest" | "high" | "medium" | "low" | "lowest";
  assignee: number | null;
  assignee_name: string | null;
  project: number;
  project_key: string;
  sprint: number | null;
  story_points: number | null;
  due_date: string | null;
  label_names: string[];
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: number;
  issue: number;
  author: number;
  author_name: string;
  body: string;
  created_at: string;
  updated_at: string;
}

// Aufgaben / Planung
export interface PersonalTodo {
  id: number;
  title: string;
  description: string;
  priority: 1 | 2 | 3 | 4;
  status: "pending" | "in_progress" | "done" | "cancelled";
  due_date: string | null;
  estimated_hours: number | null;
  source: "manual" | "jira" | "confluence" | "email" | "teams" | "ai";
  linked_issue: number | null;
  ai_confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface DailyPlanItem {
  id: number;
  todo: number;
  todo_title: string;
  order: number;
  scheduled_start: string | null;
  time_block_minutes: number | null;
  ai_reasoning: string;
}

export interface DailyPlan {
  id: number;
  date: string;
  ai_summary: string;
  ai_reasoning: string;
  capacity_hours: number;
  items: DailyPlanItem[];
  created_at: string;
  updated_at: string;
}

// Integrationen
export interface IntegrationConfig {
  id: number;
  integration_type: string;
  is_enabled: boolean;
  settings: Record<string, unknown>;
  last_synced_at: string | null;
  sync_status: "idle" | "syncing" | "error";
  created_at: string;
  updated_at: string;
}

export interface SyncLog {
  id: number;
  integration: number;
  direction: "inbound" | "outbound" | "bidirectional";
  status: "started" | "completed" | "failed";
  records_processed: number;
  records_created: number;
  records_updated: number;
  errors: unknown[];
  started_at: string;
  completed_at: string | null;
}

export interface CalendarEvent {
  id: number;
  external_id: string;
  title: string;
  start_time: string;
  end_time: string;
  is_all_day: boolean;
  location: string;
  attendees: string[];
}

// Benachrichtigungen
export interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  severity: "info" | "warning" | "urgent";
  is_read: boolean;
  action_url: string;
  created_at: string;
}

// Issue Detail (erweitertes Interface für Einzelansicht)
export interface IssueDetail extends Issue {
  description: string;
  comments: Comment[];
  labels: { id: number; name: string; color: string }[];
  subtasks: Issue[];
  parent: number | null;
  reporter: number | null;
  jira_issue_key: string | null;
  jira_updated_at: string | null;
  metadata: Record<string, unknown>;
}

// Project Statistics
export interface ProjectStats {
  total: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  overdue_count: number;
  sprint_info?: {
    name: string;
    start_date: string | null;
    end_date: string | null;
    total_issues: number;
    done_issues: number;
  };
}

// Git-Aktivitäten
export interface GitActivity {
  id: number;
  project: number;
  event_type: "commit" | "pr_opened" | "pr_merged" | "pr_closed";
  event_type_display: string;
  author: string;
  title: string;
  url: string;
  event_date: string;
  linked_issue: number | null;
}

// Confluence
export interface ConfluencePage {
  id: number;
  confluence_page_id: string;
  space_key: string;
  title: string;
  content_text: string;
  last_confluence_update: string;
  ai_summary: string;
  ai_action_items: string[];
  ai_decisions: string[];
  ai_risks: string[];
  ai_processed_at: string | null;
  created_at: string;
  updated_at: string;
}

// API Responses
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
