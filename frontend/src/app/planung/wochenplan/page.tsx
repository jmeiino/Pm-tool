"use client";

import { Card } from "@/components/ui/Card";

const weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"];

export default function WochenplanPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Wochenplan</h2>
      <div className="grid grid-cols-5 gap-4">
        {weekdays.map((day) => (
          <Card key={day} title={day}>
            <p className="text-sm text-gray-400">
              Aufgaben hierhin ziehen...
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}
