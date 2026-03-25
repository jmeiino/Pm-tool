import { create } from "zustand";

export type ImportTab = "jira" | "github" | "confluence";

interface GitHubRepoTarget {
  createNew: boolean;
  existingProjectId?: number;
  projectName?: string;
}

interface JiraFilters {
  assignee: string;
  status: string;
  sprint: string;
}

interface ImportWizardState {
  activeTab: ImportTab;
  setActiveTab: (tab: ImportTab) => void;

  // Jira
  jiraSelectedProjects: Set<string>;
  jiraSelectedIssues: Set<string>;
  jiraFilters: JiraFilters;
  toggleJiraProject: (id: string) => void;
  toggleJiraIssue: (id: string) => void;
  setJiraFilter: (key: keyof JiraFilters, value: string) => void;
  selectAllJiraIssues: (ids: string[]) => void;
  deselectAllJiraIssues: (ids: string[]) => void;

  // GitHub
  githubSelectedRepos: Set<string>;
  githubRepoTargets: Record<string, GitHubRepoTarget>;
  githubSelectedIssues: Record<string, Set<number>>;
  githubMineOnly: boolean;
  toggleGitHubRepo: (fullName: string) => void;
  setGitHubRepoTarget: (fullName: string, target: GitHubRepoTarget) => void;
  toggleGitHubIssue: (repoFullName: string, issueId: number) => void;
  setGitHubMineOnly: (value: boolean) => void;

  // Confluence
  confluenceSelectedSpaces: Set<string>;
  confluenceSelectedPages: Set<string>;
  confluenceMyPagesOnly: boolean;
  toggleConfluenceSpace: (key: string) => void;
  toggleConfluencePage: (id: string) => void;
  setConfluenceMyPagesOnly: (value: boolean) => void;

  // Common
  reset: () => void;
}

const initialState = {
  activeTab: "jira" as ImportTab,
  jiraSelectedProjects: new Set<string>(),
  jiraSelectedIssues: new Set<string>(),
  jiraFilters: { assignee: "", status: "", sprint: "" },
  githubSelectedRepos: new Set<string>(),
  githubRepoTargets: {} as Record<string, GitHubRepoTarget>,
  githubSelectedIssues: {} as Record<string, Set<number>>,
  githubMineOnly: false,
  confluenceSelectedSpaces: new Set<string>(),
  confluenceSelectedPages: new Set<string>(),
  confluenceMyPagesOnly: false,
};

export const useImportWizardStore = create<ImportWizardState>((set) => ({
  ...initialState,

  setActiveTab: (tab) => set({ activeTab: tab }),

  // Jira
  toggleJiraProject: (id) =>
    set((state) => {
      const next = new Set(state.jiraSelectedProjects);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { jiraSelectedProjects: next };
    }),

  toggleJiraIssue: (id) =>
    set((state) => {
      const next = new Set(state.jiraSelectedIssues);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { jiraSelectedIssues: next };
    }),

  setJiraFilter: (key, value) =>
    set((state) => ({
      jiraFilters: { ...state.jiraFilters, [key]: value },
    })),

  selectAllJiraIssues: (ids) =>
    set((state) => {
      const next = new Set(state.jiraSelectedIssues);
      ids.forEach((id) => next.add(id));
      return { jiraSelectedIssues: next };
    }),

  deselectAllJiraIssues: (ids) =>
    set((state) => {
      const next = new Set(state.jiraSelectedIssues);
      ids.forEach((id) => next.delete(id));
      return { jiraSelectedIssues: next };
    }),

  // GitHub
  toggleGitHubRepo: (fullName) =>
    set((state) => {
      const next = new Set(state.githubSelectedRepos);
      if (next.has(fullName)) {
        next.delete(fullName);
      } else {
        next.add(fullName);
      }
      return { githubSelectedRepos: next };
    }),

  setGitHubRepoTarget: (fullName, target) =>
    set((state) => ({
      githubRepoTargets: { ...state.githubRepoTargets, [fullName]: target },
    })),

  toggleGitHubIssue: (repoFullName, issueId) =>
    set((state) => {
      const repoIssues = new Set(state.githubSelectedIssues[repoFullName] || []);
      if (repoIssues.has(issueId)) repoIssues.delete(issueId);
      else repoIssues.add(issueId);
      return {
        githubSelectedIssues: {
          ...state.githubSelectedIssues,
          [repoFullName]: repoIssues,
        },
      };
    }),

  setGitHubMineOnly: (value) => set({ githubMineOnly: value }),

  // Confluence
  toggleConfluenceSpace: (key) =>
    set((state) => {
      const next = new Set(state.confluenceSelectedSpaces);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return { confluenceSelectedSpaces: next };
    }),

  toggleConfluencePage: (id) =>
    set((state) => {
      const next = new Set(state.confluenceSelectedPages);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { confluenceSelectedPages: next };
    }),

  setConfluenceMyPagesOnly: (value) => set({ confluenceMyPagesOnly: value }),

  // Common
  reset: () => set(initialState),
}));
