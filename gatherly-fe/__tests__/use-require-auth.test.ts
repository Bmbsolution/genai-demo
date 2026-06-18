import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useRequireAuth } from "@/hooks/use-require-auth";
import { useAuthStore } from "@/lib/store/auth";

const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));

beforeEach(() => {
  replace.mockClear();
  useAuthStore.setState({
    accessToken: null,
    refreshToken: null,
    userId: null,
    displayName: null,
    hydrated: false,
  });
});

describe("useRequireAuth", () => {
  it("redirects to /login once hydrated and unauthenticated", () => {
    useAuthStore.setState({ hydrated: true, accessToken: null });
    const { result } = renderHook(() => useRequireAuth());
    expect(replace).toHaveBeenCalledWith("/login");
    expect(result.current.ready).toBe(false);
  });

  it("is ready and does not redirect when authenticated", () => {
    useAuthStore.setState({ hydrated: true, accessToken: "at" });
    const { result } = renderHook(() => useRequireAuth());
    expect(replace).not.toHaveBeenCalled();
    expect(result.current.ready).toBe(true);
  });

  it("waits without redirecting until the persisted store hydrates", () => {
    useAuthStore.setState({ hydrated: false, accessToken: null });
    const { result } = renderHook(() => useRequireAuth());
    // The whole point of the hydration guard: don't bounce before we know.
    expect(replace).not.toHaveBeenCalled();
    expect(result.current.ready).toBe(false);
  });
});
