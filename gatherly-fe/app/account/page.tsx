"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { BillingCard } from "@/components/billing-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/store/auth";

type User = components["schemas"]["UserResponse"];

interface ProfileValues {
  display_name: string;
  timezone: string;
  avatar_url: string;
}
interface PasswordValues {
  current_password: string;
  new_password: string;
}

function Avatar({ url, name }: { url: string | null; name: string }) {
  const initials = name.slice(0, 2).toUpperCase();
  if (url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- external avatar URL, optimization not worth a domain allowlist
      <img
        src={url}
        alt={name}
        referrerPolicy="no-referrer"
        className="h-16 w-16 rounded-full border object-cover"
      />
    );
  }
  return (
    <span className="flex h-16 w-16 items-center justify-center rounded-full bg-primary font-display text-lg font-semibold text-primary-foreground">
      {initials}
    </span>
  );
}

export default function AccountPage() {
  const { ready } = useRequireAuth();
  const t = useTranslations("account");
  const tc = useTranslations("common");
  const router = useRouter();
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);
  const clear = useAuthStore((state) => state.clear);

  const me = useQuery({
    queryKey: ["me"],
    queryFn: () => apiFetch<Data<User>>("/api/v1/auth/me").then((r) => r.data),
    enabled: ready,
  });

  const profileForm = useForm<ProfileValues>();
  const passwordForm = useForm<PasswordValues>();

  useEffect(() => {
    if (me.data) {
      profileForm.reset({
        display_name: me.data.display_name,
        timezone: me.data.timezone,
        avatar_url: me.data.avatar_url ?? "",
      });
    }
  }, [me.data, profileForm]);

  const save = useMutation({
    mutationFn: (values: ProfileValues) =>
      apiFetch<Data<User>>("/api/v1/auth/me", {
        method: "PATCH",
        body: {
          display_name: values.display_name,
          timezone: values.timezone,
          avatar_url: values.avatar_url.trim() || null,
        },
      }).then((r) => r.data),
    onSuccess: (user) => {
      queryClient.setQueryData(["me"], user);
      setUser({ id: user.id, name: user.display_name });
      toast.success(t("saved"));
    },
    onError: () => toast.error(t("saveFailed")),
  });

  const changePassword = useMutation({
    mutationFn: (values: PasswordValues) =>
      apiFetch("/api/v1/auth/change-password", { method: "POST", body: values }),
    onSuccess: () => {
      passwordForm.reset();
      toast.success(t("password.changed"));
    },
    onError: () => toast.error(t("password.changeFailed")),
  });

  const deleteAccount = useMutation({
    mutationFn: () => apiFetch("/api/v1/auth/account", { method: "DELETE" }),
    onSuccess: () => {
      clear();
      router.push("/");
    },
    onError: () => toast.error(t("danger.failed")),
  });

  if (!ready) return null;
  const user = me.data;
  const isPasswordAccount = user?.auth_provider === "password";

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-2xl space-y-6 px-4 py-8 sm:px-6">
        <div className="animate-fade-up">
          <h1 className="font-display text-3xl font-semibold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>

        {me.isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}

        {user ? (
          <>
            <Card className="animate-fade-up [animation-delay:60ms]">
              <CardHeader>
                <CardTitle className="text-base">{t("profile")}</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  onSubmit={profileForm.handleSubmit((values) => save.mutate(values))}
                  className="space-y-5"
                >
                  <div className="flex items-center gap-4">
                    <Avatar url={user.avatar_url} name={user.display_name} />
                    <div className="text-sm">
                      <p className="font-medium">{user.email}</p>
                      <p className="text-muted-foreground">
                        {t("signedInWith")}{" "}
                        <Badge variant="secondary" className="ml-1 capitalize">
                          {user.auth_provider}
                        </Badge>
                      </p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="display_name">{t("displayName")}</Label>
                    <Input id="display_name" {...profileForm.register("display_name")} />
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="timezone">{t("timezone")}</Label>
                      <Input
                        id="timezone"
                        placeholder="America/Toronto"
                        {...profileForm.register("timezone")}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="avatar_url">{t("avatarUrl")}</Label>
                      <Input
                        id="avatar_url"
                        placeholder="https://…"
                        {...profileForm.register("avatar_url")}
                      />
                    </div>
                  </div>
                  <Button type="submit" disabled={save.isPending}>
                    {save.isPending ? t("saving") : t("save")}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <div className="animate-fade-up [animation-delay:120ms]">
              <BillingCard enabled={ready} />
            </div>

            <Card className="animate-fade-up [animation-delay:180ms]">
              <CardHeader>
                <CardTitle className="text-base">{t("password.title")}</CardTitle>
              </CardHeader>
              <CardContent>
                {isPasswordAccount ? (
                  <form
                    onSubmit={passwordForm.handleSubmit((values) => changePassword.mutate(values))}
                    className="space-y-4"
                  >
                    <div className="space-y-2">
                      <Label htmlFor="current_password">{t("password.current")}</Label>
                      <Input
                        id="current_password"
                        type="password"
                        autoComplete="current-password"
                        {...passwordForm.register("current_password", { required: true })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="new_password">{t("password.new")}</Label>
                      <Input
                        id="new_password"
                        type="password"
                        autoComplete="new-password"
                        {...passwordForm.register("new_password", { required: true, minLength: 8 })}
                      />
                    </div>
                    <Button type="submit" variant="outline" disabled={changePassword.isPending}>
                      {changePassword.isPending ? t("password.changing") : t("password.change")}
                    </Button>
                  </form>
                ) : (
                  <p className="text-sm text-muted-foreground">{t("password.googleNote")}</p>
                )}
              </CardContent>
            </Card>

            <Card className="animate-fade-up border-destructive/40 [animation-delay:240ms]">
              <CardHeader>
                <CardTitle className="text-base text-destructive">{t("danger.title")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">{t("danger.warning")}</p>
                <Button
                  variant="destructive"
                  disabled={deleteAccount.isPending}
                  onClick={() => {
                    if (window.confirm(t("danger.confirm"))) deleteAccount.mutate();
                  }}
                >
                  {deleteAccount.isPending ? t("danger.deleting") : t("danger.delete")}
                </Button>
              </CardContent>
            </Card>
          </>
        ) : null}
      </main>
    </div>
  );
}
