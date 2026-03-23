"use client";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import Link from "next/link";

const integrations = [
  {
    name: "Jira",
    description: "Bidirektionale Synchronisation von Projekten und Issues",
    status: "nicht verbunden",
    icon: "J",
    color: "bg-blue-500",
  },
  {
    name: "Confluence",
    description: "Seiten lesen, analysieren und erstellen",
    status: "nicht verbunden",
    icon: "C",
    color: "bg-blue-400",
  },
  {
    name: "Microsoft 365",
    description: "Outlook Kalender, E-Mails, Teams und To-Do",
    status: "nicht verbunden",
    icon: "M",
    color: "bg-orange-500",
  },
  {
    name: "GitHub",
    description: "Commits, Pull Requests und Code-Aktivität",
    status: "nicht verbunden",
    icon: "G",
    color: "bg-gray-800",
  },
];

export default function EinstellungenPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Einstellungen</h2>

      <Card title="Integrationen">
        <div className="space-y-4">
          {integrations.map((integration) => (
            <div
              key={integration.name}
              className="flex items-center justify-between rounded-lg border border-gray-100 p-4"
            >
              <div className="flex items-center gap-4">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-lg ${integration.color} text-white font-bold`}
                >
                  {integration.icon}
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {integration.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {integration.description}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge>{integration.status}</Badge>
                <Button variant="secondary" size="sm">
                  Verbinden
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="KI-Einstellungen">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Claude API</p>
              <p className="text-sm text-gray-500">
                KI-gestützte Tagesplanung, Priorisierung und Zusammenfassungen
              </p>
            </div>
            <Badge>API-Key erforderlich</Badge>
          </div>
        </div>
      </Card>
    </div>
  );
}
