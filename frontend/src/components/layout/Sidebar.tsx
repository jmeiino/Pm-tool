"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/stores/useAppStore";
import {
  HomeIcon,
  FolderIcon,
  CheckCircleIcon,
  CalendarDaysIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  ClipboardDocumentListIcon,
  CodeBracketIcon,
  ArrowDownTrayIcon,
  UserGroupIcon,
  XMarkIcon,
  ShieldCheckIcon,
  UsersIcon,
  ServerStackIcon,
  CpuChipIcon,
} from "@heroicons/react/24/outline";
import { useCurrentUser } from "@/hooks/useUser";

const navigation = [
  { name: "Dashboard", href: "/", icon: HomeIcon },
  { name: "Projekte", href: "/projekte", icon: FolderIcon },
  { name: "Aufgaben", href: "/todos", icon: CheckCircleIcon },
  { name: "Tagesplan", href: "/planung/tagesplan", icon: ClipboardDocumentListIcon },
  { name: "Wochenplan", href: "/planung/wochenplan", icon: CalendarDaysIcon },
  { name: "Confluence", href: "/confluence", icon: DocumentTextIcon },
  { name: "GitHub", href: "/github", icon: CodeBracketIcon },
  { name: "Agents", href: "/agents", icon: UserGroupIcon },
  { name: "Import", href: "/import", icon: ArrowDownTrayIcon },
  { name: "Kalender", href: "/kalender", icon: CalendarDaysIcon },
  { name: "Einstellungen", href: "/einstellungen", icon: Cog6ToothIcon },
];

const adminNavigation = [
  { name: "Admin Dashboard", href: "/admin", icon: ShieldCheckIcon },
  { name: "Benutzer", href: "/admin/benutzer", icon: UsersIcon },
  { name: "System", href: "/admin/system", icon: ServerStackIcon },
  { name: "AI & Agents", href: "/admin/ai-agents", icon: CpuChipIcon },
];

function NavContent() {
  const pathname = usePathname();
  const { setSidebarOpen } = useAppStore();
  const { data: user } = useCurrentUser();

  return (
    <>
      <div className="flex h-16 items-center gap-2.5 border-b border-[rgba(255,255,255,0.07)] px-5">
        <div className="flex flex-col gap-px">
          <span className="font-mono text-lg font-semibold tracking-widest leading-none text-brand">
            PM<span className="text-white">-TOOL</span>
          </span>
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-[rgba(255,255,255,0.28)]">
            Projektmanagement
          </span>
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-sm px-3 py-2 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-brand text-white"
                  : "text-[rgba(255,255,255,0.55)] hover:bg-[rgba(0,158,227,0.10)] hover:text-white"
              )}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {item.name}
            </Link>
          );
        })}

        {user?.is_staff && (
          <>
            <div className="my-3 border-t border-[rgba(255,255,255,0.07)]" />
            <div className="px-3 pb-1 font-mono text-[0.6rem] uppercase tracking-widest text-[rgba(255,255,255,0.28)]">
              Admin
            </div>
            {adminNavigation.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/admin" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-sm px-3 py-2 text-sm font-medium transition-all duration-150",
                    isActive
                      ? "bg-brand text-white"
                      : "text-[rgba(255,255,255,0.55)] hover:bg-[rgba(0,158,227,0.10)] hover:text-white"
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {item.name}
                </Link>
              );
            })}
          </>
        )}
      </nav>
    </>
  );
}

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useAppStore();

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 flex-shrink-0 border-r border-[rgba(255,255,255,0.07)] bg-dark-bg lg:flex lg:flex-col">
        <NavContent />
      </aside>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 w-64 bg-dark-bg shadow-xl flex flex-col">
            <div className="absolute right-2 top-4">
              <button
                onClick={() => setSidebarOpen(false)}
                className="rounded-sm p-1 text-[rgba(255,255,255,0.28)] hover:text-white"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            <NavContent />
          </aside>
        </div>
      )}
    </>
  );
}
