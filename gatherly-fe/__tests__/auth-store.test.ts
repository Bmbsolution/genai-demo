import { beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "@/lib/store/auth";

const EMPTY = {
  accessToken: null,
  refreshToken: null,
  userId: null,
  displayName: null,
  hydrated: false,
} as const;

beforeEach(() => {
  localStorage.clear();
  useAuthStore.setState({ ...EMPTY });
});

describe("useAuthStore", () => {
  it("setSession stores the token pair", () => {
    useAuthStore.getState().setSession({ accessToken: "a", refreshToken: "r" });
    expect(useAuthStore.getState().accessToken).toBe("a");
    expect(useAuthStore.getState().refreshToken).toBe("r");
  });

  it("setUser stores the signed-in user", () => {
    useAuthStore.getState().setUser({ id: "u1", name: "Alice" });
    expect(useAuthStore.getState().userId).toBe("u1");
    expect(useAuthStore.getState().displayName).toBe("Alice");
  });

  it("clear resets the session but leaves hydrated intact", () => {
    useAuthStore.setState({
      accessToken: "a",
      refreshToken: "r",
      userId: "u1",
      displayName: "Alice",
      hydrated: true,
    });
    useAuthStore.getState().clear();
    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.userId).toBeNull();
    expect(state.displayName).toBeNull();
    // hydrated is per-load runtime state, not reset by clear().
    expect(state.hydrated).toBe(true);
  });

  it("setHydrated flips the hydrated flag", () => {
    expect(useAuthStore.getState().hydrated).toBe(false);
    useAuthStore.getState().setHydrated();
    expect(useAuthStore.getState().hydrated).toBe(true);
  });

  it("persists only the session fields, not hydrated (partialize)", () => {
    useAuthStore.getState().setSession({ accessToken: "a", refreshToken: "r" });
    useAuthStore.getState().setUser({ id: "u1", name: "Alice" });
    useAuthStore.getState().setHydrated();

    const raw = localStorage.getItem("gatherly-auth");
    expect(raw).not.toBeNull();
    const persisted = JSON.parse(raw ?? "{}") as { state: Record<string, unknown> };
    expect(persisted.state).toMatchObject({
      accessToken: "a",
      refreshToken: "r",
      userId: "u1",
      displayName: "Alice",
    });
    expect(persisted.state).not.toHaveProperty("hydrated");
  });
});
