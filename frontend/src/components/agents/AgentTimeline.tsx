"use client";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { AgentMessage as AgentMessageType } from "@/lib/types";

interface AgentTimelineProps {
  messages: AgentMessageType[];
  onDecision?: (messageId: number, option: string) => void;
}

const typeConfig: Record<string, { badge: string; variant: "default" | "success" | "warning" | "danger" | "info" }> = {
  text: { badge: "", variant: "default" },
  decision: { badge: "Entscheidung", variant: "info" },
  question: { badge: "Rückfrage", variant: "warning" },
  handoff: { badge: "Übergabe", variant: "info" },
  status_change: { badge: "Status", variant: "default" },
  deliverable: { badge: "Ergebnis", variant: "success" },
  error: { badge: "Fehler", variant: "danger" },
  system: { badge: "System", variant: "default" },
};

export function AgentTimeline({ messages, onDecision }: AgentTimelineProps) {
  return (
    <div className="space-y-3">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} onDecision={onDecision} />
      ))}
    </div>
  );
}

function MessageBubble({
  message,
  onDecision,
}: {
  message: AgentMessageType;
  onDecision?: (messageId: number, option: string) => void;
}) {
  const isUser = message.sender_type === "user";
  const isSystem = message.sender_type === "system" || message.message_type === "system";
  const config = typeConfig[message.message_type] || typeConfig.text;
  const decisionOptions = (message.metadata?.decision_options as string[]) || [];

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-500">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      {!isUser && (
        <div
          className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
          style={{ backgroundColor: message.sender_avatar_color }}
        >
          {message.sender_name.charAt(0)}
        </div>
      )}

      {/* Bubble */}
      <div
        className={`max-w-[75%] rounded-lg px-3 py-2 ${
          isUser
            ? "bg-primary-600 text-white"
            : "border border-gray-200 bg-white"
        }`}
      >
        {/* Header */}
        <div className={`flex items-center gap-2 ${isUser ? "justify-end" : ""}`}>
          <span className={`text-xs font-medium ${isUser ? "text-primary-100" : "text-gray-900"}`}>
            {message.sender_name}
          </span>
          {config.badge && <Badge variant={config.variant}>{config.badge}</Badge>}
          <span className={`text-[10px] ${isUser ? "text-primary-200" : "text-gray-400"}`}>
            {new Date(message.created_at).toLocaleTimeString("de-DE", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        {/* Content */}
        <p className={`mt-1 text-sm ${isUser ? "text-white" : "text-gray-700"}`}>
          {message.content}
        </p>

        {/* Handoff-Info */}
        {message.message_type === "handoff" && message.metadata?.to_agent && (
          <div className="mt-2 rounded bg-blue-50 px-2 py-1 text-xs text-blue-700">
            → Übergabe an {message.metadata.to_agent as string}
          </div>
        )}

        {/* Decision Buttons */}
        {message.is_decision_pending && decisionOptions.length > 0 && onDecision && (
          <div className="mt-2 flex flex-wrap gap-2">
            {decisionOptions.map((option) => (
              <Button
                key={option}
                variant="secondary"
                size="sm"
                onClick={() => onDecision(message.id, option)}
              >
                {option}
              </Button>
            ))}
          </div>
        )}

        {/* Deliverable */}
        {message.message_type === "deliverable" && message.metadata?.deliverable && (
          <div className="mt-2 rounded border border-green-200 bg-green-50 p-2">
            <span className="text-xs font-medium text-green-800">
              {(message.metadata.deliverable as Record<string, string>).name || "Ergebnis"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
