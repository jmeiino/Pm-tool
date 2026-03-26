import { z } from "zod";

export const projectCreateSchema = z.object({
  name: z.string().min(1, "Name ist erforderlich"),
  key: z
    .string()
    .min(2, "Mindestens 2 Zeichen")
    .max(20, "Maximal 20 Zeichen")
    .regex(/^[A-Z0-9]+$/, "Nur Großbuchstaben und Zahlen"),
  description: z.string().optional().default(""),
  status: z.enum(["active", "archived", "paused"]).default("active"),
});

export const issueCreateSchema = z.object({
  project: z.number({ required_error: "Projekt ist erforderlich" }),
  title: z.string().min(1, "Titel ist erforderlich"),
  description: z.string().optional().default(""),
  issue_type: z
    .enum(["epic", "story", "task", "bug", "subtask"])
    .default("task"),
  priority: z
    .enum(["highest", "high", "medium", "low", "lowest"])
    .default("medium"),
  assignee: z.number().nullable().optional(),
  sprint: z.number().nullable().optional(),
  story_points: z.any().optional(),
  due_date: z.preprocess((v) => (v === "" ? null : v), z.string().nullable().optional()),
  labels: z.array(z.number()).optional().default([]),
});

export const todoCreateSchema = z.object({
  title: z.string().min(1, "Titel ist erforderlich"),
  description: z.string().optional().default(""),
  priority: z.number().min(1).max(4).default(3),
  due_date: z.preprocess((v) => (v === "" ? null : v), z.string().nullable().optional()),
  estimated_hours: z.any().optional(),
  linked_issue: z.number().nullable().optional(),
});

export type ProjectCreateInput = z.infer<typeof projectCreateSchema>;
export type IssueCreateInput = z.infer<typeof issueCreateSchema>;
export type TodoCreateInput = z.infer<typeof todoCreateSchema>;
