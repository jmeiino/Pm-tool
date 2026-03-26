"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { PaperAirplaneIcon } from "@heroicons/react/24/outline";

interface AgentChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function AgentChatInput({ onSend, disabled, placeholder }: AgentChatInputProps) {
  const [content, setContent] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    onSend(content.trim());
    setContent("");
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-gray-200 bg-gray-50 px-4 py-3">
      <input
        type="text"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={placeholder || "Nachricht an die Agents..."}
        disabled={disabled}
        className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand disabled:opacity-50"
      />
      <Button type="submit" disabled={disabled || !content.trim()} size="sm">
        <PaperAirplaneIcon className="h-4 w-4" />
      </Button>
    </form>
  );
}
