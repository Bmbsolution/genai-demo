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
        <div className="flex items-center gap-2">
          <Boxes className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">{t("app.title")}</span>
          {workspaceName ? (
            <span className="text-sm text-muted-foreground">/ {workspaceName}</span>
          ) : null}
          <nav className="ml-6 flex items-center gap-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:text-foreground",
                  pathname.startsWith(link.href)
                    ? "text-foreground"
                    : "text-muted-foreground",
                )}
              >
                {t(link.key)}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={onLogout}>
            <LogOut className="mr-2 h-4 w-4" />
            {t("nav.logout")}
          </Button>
        </div>
      </div>
    </header>
  );
}
