"use client";

import { useRouter } from "next/navigation";

import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/store/auth";

type TokenPair = components["schemas"]["TokenPairResponse"];
type User = components["schemas"]["UserResponse"];

/**
 * Shared post-authentication step for every sign-in path (password login,
 * signup, Google): store the token pair, load the host identity, and redirect.
 */
export function useCompleteAuth(): (tokens: TokenPair, redirectTo?: string) => Promise<void> {
  const router = useRouter();
  const setSession = useAuthStore((state) => state.setSession);
  const setWorkspace = useAuthStore((state) => state.setWorkspace);

  return async (tokens, redirectTo = "/events") => {
    setSession({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    const me = await apiFetch<Data<User>>("/api/v1/auth/me", { workspace: false });
    setWorkspace({ id: me.data.id, name: me.data.display_name });
    router.push(redirectTo);
  };
}
