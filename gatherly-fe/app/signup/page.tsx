"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { PartyPopper } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { AuthShell } from "@/components/auth-shell";
import { GoogleSignInButton } from "@/components/google-signin-button";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCompleteAuth } from "@/hooks/use-complete-auth";
import { ApiError, apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type TokenPair = components["schemas"]["TokenPairResponse"];

const schema = z.object({
  display_name: z.string().min(1),
  email: z.string().email(),
  password: z.string().min(8),
});
type FormValues = z.infer<typeof schema>;

export default function SignupPage() {
  const t = useTranslations("signup");
  const tl = useTranslations("login");
  const complete = useCompleteAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    try {
      const tokens = await apiFetch<TokenPair>("/api/v1/auth/register", {
        method: "POST",
        body: values,
        auth: false,
      });
      await complete(tokens);
    } catch (error) {
      const message = error instanceof ApiError && error.status === 409 ? t("emailTaken") : t("failed");
      toast.error(message);
    }
  });

  return (
    <AuthShell>
      <Card className="animate-fade-up relative w-full border-border/60 shadow-lift">
        <CardHeader>
          <Link
            href="/"
            className="mb-2 flex h-11 w-11 items-center justify-center rounded-xl bg-primary"
          >
            <PartyPopper className="h-5 w-5 text-primary-foreground" aria-hidden="true" />
          </Link>
          <CardTitle className="text-2xl">{t("title")}</CardTitle>
          <CardDescription>{t("subtitle")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={onSubmit} method="post" className="space-y-4" noValidate>
            <div className="space-y-2">
              <Label htmlFor="display_name">{t("name")}</Label>
              <Input id="display_name" autoComplete="name" {...register("display_name")} />
              {errors.display_name ? (
                <p className="text-sm text-destructive">{errors.display_name.message}</p>
              ) : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">{t("email")}</Label>
              <Input id="email" type="email" autoComplete="email" {...register("email")} />
              {errors.email ? (
                <p className="text-sm text-destructive">{errors.email.message}</p>
              ) : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t("password")}</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                {...register("password")}
              />
              <p className="text-xs text-muted-foreground">{t("passwordHint")}</p>
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? t("submitting") : t("submit")}
            </Button>
          </form>

          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="h-px flex-1 bg-border" />
            {tl("or")}
            <span className="h-px flex-1 bg-border" />
          </div>
          <GoogleSignInButton />

          <p className="text-center text-sm text-muted-foreground">
            {t("haveAccount")}{" "}
            <Link href="/login" className="font-medium text-brand hover:underline">
              {t("signinLink")}
            </Link>
          </p>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
