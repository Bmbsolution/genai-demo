"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

export default function RouteError({ reset }: { reset: () => void }) {
  const t = useTranslations("common");
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <p className="text-muted-foreground">{t("error")}</p>
      <Button variant="outline" onClick={reset}>
        {t("retry")}
      </Button>
    </div>
  );
}
