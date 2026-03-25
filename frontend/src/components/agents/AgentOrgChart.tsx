"use client";

import { AgentStatusBadge } from "./AgentStatusBadge";
import type { AgentProfile } from "@/lib/types";

interface AgentOrgChartProps {
  agents: AgentProfile[];
  activeAgentId?: number | null;
}

export function AgentOrgChart({ agents, activeAgentId }: AgentOrgChartProps) {
  const ceo = agents.find((a) => a.role === "ceo");
  const departments = agents.filter((a) => a.role === "department_head");
  const specialists = agents.filter((a) => a.role === "specialist");
  const qa = agents.filter((a) => a.role === "qa");

  const getSpecialists = (dept: string) =>
    specialists.filter((s) => s.department === dept);

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-medium text-gray-500 uppercase">Organisation</h4>

      {/* CEO */}
      {ceo && (
        <AgentNode agent={ceo} isActive={ceo.id === activeAgentId} />
      )}

      {/* Departments */}
      {departments.map((dept) => (
        <div key={dept.id} className="ml-4 space-y-1">
          <AgentNode agent={dept} isActive={dept.id === activeAgentId} />
          {getSpecialists(dept.department).map((spec) => (
            <div key={spec.id} className="ml-4">
              <AgentNode agent={spec} isActive={spec.id === activeAgentId} />
            </div>
          ))}
        </div>
      ))}

      {/* QA */}
      {qa.map((q) => (
        <div key={q.id} className="ml-4">
          <AgentNode agent={q} isActive={q.id === activeAgentId} />
        </div>
      ))}

      {/* Legende */}
      <div className="mt-4 space-y-1 border-t border-gray-100 pt-2">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <AgentStatusBadge status="idle" /> Verfügbar
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <AgentStatusBadge status="working" /> Arbeitet
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <AgentStatusBadge status="waiting" /> Wartet
        </div>
      </div>
    </div>
  );
}

function AgentNode({ agent, isActive }: { agent: AgentProfile; isActive: boolean }) {
  return (
    <div
      className={`flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors ${
        isActive ? "bg-primary-50 ring-1 ring-primary-300" : "hover:bg-gray-50"
      }`}
    >
      <div
        className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white"
        style={{ backgroundColor: agent.avatar_color }}
      >
        {agent.name.charAt(0)}
      </div>
      <div className="flex-1 min-w-0">
        <span className="text-xs font-medium text-gray-900 truncate block">
          {agent.name}
        </span>
        <span className="text-[10px] text-gray-400">{agent.role_display}</span>
      </div>
      <AgentStatusBadge status={agent.status} />
    </div>
  );
}
