"use client";

import { Boxes, LogOut } from "lucide-react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/store/auth";

export function AppHeader() {
  const router = useRouter();
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
