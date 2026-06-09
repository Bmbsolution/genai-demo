"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Boxes } from "lucide-react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

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
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/store/auth";

type TokenPair = components["schemas"]["TokenPairResponse"];
type Workspace = components["schemas"]["WorkspaceResponse"];

const schema = z.object({ email: z.string().email(), password: z.string().min(1) });
type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const t = useTranslations("login");
  const setSession = useAuthStore((state) => state.setSession);
  const setWorkspace = useAuthStore((state) => state.setWorkspace);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    try {
      const tokens = await apiFetch<TokenPair>("/api/v1/auth/login", {
        method: "POST",
        body: values,
        auth: false,
        workspace: false,
      });
      setSession({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      const workspaces = await apiFetch<Data<Workspace[]>>("/api/v1/workspaces", {
        workspace: false,
      });
      const first = workspaces.data.at(0);
      if (first) setWorkspace({ id: first.id, name: first.name });
      router.push("/services");
    } catch {
      toast.error(t("failed"));
    }
  });

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-grid p-6">
      <Card className="animate-fade-up relative w-full max-w-sm border-border/70 shadow-xl">
        <CardHeader>
          <div className="mb-2 flex h-11 w-11 items-center justify-center rounded-xl bg-primary">
            <Boxes className="h-5 w-5 text-primary-foreground" aria-hidden="true" />
          </div>
          <CardTitle className="text-2xl">{t("title")}</CardTitle>
          <CardDescription>{t("subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          {/* method="post": if the form is submitted before React hydrates,
              the browser's native fallback must not leak credentials into the
              URL as GET query params (history, logs). */}
          <form onSubmit={onSubmit} method="post" className="space-y-4" noValidate>
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
                autoComplete="current-password"
                {...register("password")}
              />
              {errors.password ? (
                <p className="text-sm text-destructive">{errors.password.message}</p>
              ) : null}
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? t("submitting") : t("submit")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
