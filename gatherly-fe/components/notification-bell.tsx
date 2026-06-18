"use client";

import { Bell } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useUnreadCount } from "@/hooks/use-notifications";
import { cn } from "@/lib/utils";

/** Header bell linking to /notifications, with a live unread-count badge. */
export function NotificationBell() {
  const t = useTranslations("notifications");
  const pathname = usePathname();
  const { data: unread } = useUnreadCount();

  const active = pathname.startsWith("/notifications");
  const count = unread ?? 0;
  const badge = count > 99 ? "99+" : String(count);
  const label = count > 0 ? t("bellWithCount", { count }) : t("bell");

  return (
    <Link
      href="/notifications"
      aria-label={label}
      aria-current={active ? "page" : undefined}
      className={cn(
        "relative flex h-8 w-8 items-center justify-center rounded-full border bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        active
          ? "border-brand/40 text-brand"
          : "text-muted-foreground hover:border-brand/40 hover:text-brand",
      )}
    >
      <Bell className="h-4 w-4" aria-hidden="true" />
      {count > 0 ? (
        <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand px-1 font-mono text-[10px] font-semibold leading-none text-primary-foreground">
          {badge}
        </span>
      ) : null}
    </Link>
  );
}
