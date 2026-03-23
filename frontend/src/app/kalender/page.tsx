"use client";

import { Card } from "@/components/ui/Card";
import { CalendarDaysIcon } from "@heroicons/react/24/outline";

export default function KalenderPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Kalender</h2>

      <Card title="Outlook-Kalender">
        <div className="text-center py-8">
          <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-4 text-sm text-gray-500">
            Verbinde Microsoft 365 in den Einstellungen, um deinen Kalender zu sehen.
          </p>
        </div>
      </Card>
    </div>
  );
}
