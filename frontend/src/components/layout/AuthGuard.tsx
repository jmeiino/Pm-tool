"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";

const PUBLIC_PATHS = ["/login"];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

    if (!isAuthenticated && !isPublic) {
      router.replace("/login");
    } else if (isAuthenticated && pathname === "/login") {
      router.replace("/");
    } else {
      setChecked(true);
    }
  }, [isAuthenticated, pathname, router]);

  // Oeffentliche Seiten immer rendern
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return <>{children}</>;
  }

  if (!checked) {
    return null;
  }

  return <>{children}</>;
}
