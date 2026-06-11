"use client";

import { LogOut, PartyPopper } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/auth";

const NAV_LINKS = [{ href: "/events", key: "nav.events" }] as const;

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
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
            <PartyPopper className="h-[18px] w-[18px] text-primary-foreground" aria-hidden="true" />
          </span>
          <span className="font-display text-lg font-semibold tracking-tight">{t("app.title")}</span>
          {workspaceName ? (
            <span className="hidden truncate border-l border-border pl-2.5 text-sm text-muted-foreground sm:inline">
              {workspaceName}
            </span>
          ) : null}
          <nav className="ml-2 flex items-center gap-1 sm:ml-6">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-md px-2 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 sm:px-3",
                  pathname.startsWith(link.href)
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
                )}
                aria-current={pathname.startsWith(link.href) ? "page" : undefined}
              >
                {t(link.key)}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <ThemeToggle />
          <Link
            href="/account"
            aria-label={t("nav.account")}
            aria-current={pathname.startsWith("/account") ? "page" : undefined}
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full border bg-muted font-mono text-xs font-semibold uppercase transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              pathname.startsWith("/account")
                ? "border-brand/40 text-brand"
                : "text-muted-foreground hover:border-brand/40 hover:text-brand",
            )}
          >
            {(workspaceName ?? "·").slice(0, 2).toUpperCase()}
          </Link>
          <Button variant="ghost" size="sm" onClick={onLogout}>
            <LogOut className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">{t("nav.logout")}</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
