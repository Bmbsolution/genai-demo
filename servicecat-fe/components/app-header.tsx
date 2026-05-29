"use client";

import { Boxes, LogOut } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/auth";

const NAV_LINKS = [
  { href: "/services", key: "nav.services" },
  { href: "/findings", key: "nav.findings" },
] as const;

export function AppHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations();
  const workspaceName = useAuthStore((state) => state.workspaceName);
  const clear = useAuthStore((state) => state.clear);

  const onLogout = () => {
    clear();
    router.push("/login");
  };

  return (
    <header className="border-b">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <div className="flex min-w-0 items-center gap-2">
          <Boxes className="h-6 w-6 shrink-0 text-primary" />
          <span className="text-lg font-semibold">{t("app.title")}</span>
          {workspaceName ? (
            <span className="hidden truncate text-sm text-muted-foreground sm:inline">
              / {workspaceName}
            </span>
          ) : null}
          <nav className="ml-2 flex items-center gap-1 sm:ml-6">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-md px-2 py-1.5 text-sm font-medium transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 sm:px-3",
                  pathname.startsWith(link.href) ? "text-foreground" : "text-muted-foreground",
                )}
              >
                {t(link.key)}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={onLogout}>
            <LogOut className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">{t("nav.logout")}</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
