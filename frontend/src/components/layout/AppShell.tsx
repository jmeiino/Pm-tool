"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { AuthGuard } from "@/components/layout/AuthGuard";

const CHROMELESS_PATHS = ["/login"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isChromeless = CHROMELESS_PATHS.some((p) => pathname.startsWith(p));

  return (
    <AuthGuard>
      {isChromeless ? (
        <>{children}</>
      ) : (
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex flex-1 flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto p-6">{children}</main>
          </div>
        </div>
      )}
    </AuthGuard>
  );
}
