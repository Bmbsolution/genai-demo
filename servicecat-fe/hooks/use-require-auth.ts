"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/lib/store/auth";

/**
 * Guards a protected page. Waits for the persisted auth store to rehydrate
 * before deciding, so a hard refresh or deep link does not bounce an
 * authenticated user to /login. Returns `ready` once we know the user is
 * authenticated and it is safe to render and fire queries.
 */
export function useRequireAuth(): { ready: boolean } {
  const router = useRouter();
  const hydrated = useAuthStore((state) => state.hydrated);
  const accessToken = useAuthStore((state) => state.accessToken);

  useEffect(() => {
    if (hydrated && !accessToken) router.replace("/login");
  }, [hydrated, accessToken, router]);

  return { ready: hydrated && Boolean(accessToken) };
}
