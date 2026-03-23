"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  HomeIcon,
  FolderIcon,
  CheckCircleIcon,
  CalendarDaysIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  ClipboardDocumentListIcon,
} from "@heroicons/react/24/outline";

const navigation = [
  { name: "Dashboard", href: "/", icon: HomeIcon },
  { name: "Projekte", href: "/projekte", icon: FolderIcon },
  { name: "Aufgaben", href: "/todos", icon: CheckCircleIcon },
  { name: "Tagesplan", href: "/planung/tagesplan", icon: ClipboardDocumentListIcon },
  { name: "Wochenplan", href: "/planung/wochenplan", icon: CalendarDaysIcon },
  { name: "Confluence", href: "/confluence", icon: DocumentTextIcon },
  { name: "Kalender", href: "/kalender", icon: CalendarDaysIcon },
  { name: "Einstellungen", href: "/einstellungen", icon: Cog6ToothIcon },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 flex-shrink-0 border-r border-gray-200 bg-white lg:flex lg:flex-col">
      <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6">
        <div className="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center">
          <span className="text-sm font-bold text-white">PM</span>
        </div>
        <span className="text-lg font-semibold text-gray-900">PM-Tool</span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
