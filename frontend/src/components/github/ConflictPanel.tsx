"use client";

import { Badge } from "@/components/ui/Badge";
import type { GitHubConflict } from "@/lib/types";
import { formatDate } from "@/lib/utils";

interface ConflictPanelProps {
  conflicts: GitHubConflict[];
}

export function ConflictPanel({ conflicts }: ConflictPanelProps) {
  if (!conflicts.length) return null;

  return (
    <div className="space-y-3">
      {conflicts.map((conflict) => (
        <div
          key={conflict.issue_key}
          className="rounded-lg border border-gray-200 bg-white p-4"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-900">
                {conflict.issue_key}
              </span>
              <span className="text-xs text-gray-500">
                GitHub #{conflict.github_issue_number}
              </span>
            </div>
            <div className="flex gap-1.5">
              {conflict.has_title_conflict && (
                <Badge className="bg-orange-100 text-orange-700 text-[10px]">
                  Titel-Konflikt
                </Badge>
              )}
              {conflict.has_status_conflict && (
                <Badge className="bg-red-100 text-red-700 text-[10px]">
                  Status-Konflikt
                </Badge>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            {/* Lokal */}
            <div className="space-y-1.5">
              <p className="font-medium text-gray-500 uppercase tracking-wide">
                Lokal
              </p>
              <p className="text-gray-900 truncate" title={conflict.local_title}>
                {conflict.local_title}
              </p>
              <div className="flex items-center gap-2">
                <Badge className="bg-gray-100 text-gray-700 text-[10px]">
                  {conflict.local_status}
                </Badge>
                <span className="text-gray-400">
                  {formatDate(conflict.local_updated)}
                </span>
              </div>
            </div>

            {/* Remote (GitHub) */}
            <div className="space-y-1.5">
              <p className="font-medium text-gray-500 uppercase tracking-wide">
                GitHub
              </p>
              <p className="text-gray-900 truncate" title={conflict.remote_title}>
                {conflict.remote_title}
              </p>
              <div className="flex items-center gap-2">
                <Badge className="bg-gray-100 text-gray-700 text-[10px]">
                  {conflict.remote_state}
                </Badge>
                <span className="text-gray-400">
                  {formatDate(conflict.remote_updated)}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
