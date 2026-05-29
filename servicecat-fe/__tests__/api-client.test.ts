import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthStore } from "@/lib/store/auth";

const BASE = "http://127.0.0.1:8000";

function res(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response;
}

const REFRESH = "/api/v1/auth/refresh";
const isRefresh = (url: unknown): boolean => String(url).endsWith(REFRESH);

let fetchMock: ReturnType<typeof vi.fn>;

function headersOf(callIndex: number): Record<string, string> {
  const init = fetchMock.mock.calls[callIndex][1] as RequestInit;
  return init.headers as Record<string, string>;
}

beforeEach(() => {
  localStorage.clear();
  useAuthStore.setState({
    accessToken: "at",
    refreshToken: "rt",
    workspaceId: "ws1",
    workspaceName: "Acme",
    hydrated: true,
  });
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiFetch", () => {
  it("attaches the bearer token + workspace header and returns parsed JSON", async () => {
    fetchMock.mockResolvedValue(res(200, { data: { id: "1" } }));

    const result = await apiFetch<{ data: { id: string } }>("/api/v1/services");

    expect(result).toEqual({ data: { id: "1" } });
    expect(fetchMock.mock.calls[0][0]).toBe(`${BASE}/api/v1/services`);
    const headers = headersOf(0);
    expect(headers.Authorization).toBe("Bearer at");
    expect(headers["X-Workspace-Id"]).toBe("ws1");
  });

  it("unwraps the error envelope into a typed ApiError on non-401 failures", async () => {
    fetchMock.mockResolvedValue(
      res(403, { error: { code: "S3_RBAC_DENIED", message: "nope" } }),
    );

    const error = await apiFetch("/api/v1/services").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 403, code: "S3_RBAC_DENIED", message: "nope" });
  });

  it("refreshes the token on a 401 and retries the request once", async () => {
    let resourceCalls = 0;
    fetchMock.mockImplementation(async (url: unknown) => {
      if (isRefresh(url)) {
        return res(200, { access_token: "new-at", refresh_token: "new-rt", token_type: "bearer" });
      }
      resourceCalls += 1;
      return resourceCalls === 1 ? res(401, {}) : res(200, { data: { ok: true } });
    });

    const result = await apiFetch<{ data: { ok: boolean } }>("/api/v1/services");

    expect(result).toEqual({ data: { ok: true } });
    // Store rotated to the refreshed pair.
    expect(useAuthStore.getState().accessToken).toBe("new-at");
    expect(useAuthStore.getState().refreshToken).toBe("new-rt");
    // The retry carried the new bearer token.
    const lastInit = fetchMock.mock.calls.at(-1)?.[1] as RequestInit;
    expect((lastInit.headers as Record<string, string>).Authorization).toBe("Bearer new-at");
  });

  it("shares a single refresh across concurrent 401s (rotation-safe dedup)", async () => {
    let refreshCalls = 0;
    let resourceCalls = 0;
    fetchMock.mockImplementation(async (url: unknown) => {
      if (isRefresh(url)) {
        refreshCalls += 1;
        return res(200, { access_token: "new-at", refresh_token: "new-rt", token_type: "bearer" });
      }
      resourceCalls += 1;
      // The two initial concurrent requests both 401; their retries succeed.
      return resourceCalls <= 2 ? res(401, {}) : res(200, { data: { n: resourceCalls } });
    });

    await Promise.all([apiFetch("/api/v1/a"), apiFetch("/api/v1/b")]);

    expect(refreshCalls).toBe(1);
  });

  it("clears the session and throws when the refresh itself fails", async () => {
    fetchMock.mockImplementation(async (url: unknown) =>
      isRefresh(url) ? res(401, {}) : res(401, { error: { code: "S1_UNAUTHENTICATED" } }),
    );

    const error = await apiFetch("/api/v1/services").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().refreshToken).toBeNull();
  });

  it("does not attempt a refresh when there is no refresh token", async () => {
    useAuthStore.setState({ refreshToken: null });
    let refreshCalls = 0;
    fetchMock.mockImplementation(async (url: unknown) => {
      if (isRefresh(url)) refreshCalls += 1;
      return res(401, {});
    });

    await apiFetch("/api/v1/services").catch(() => undefined);

    expect(refreshCalls).toBe(0);
    expect(useAuthStore.getState().accessToken).toBeNull();
  });

  it("serializes the request body for writes", async () => {
    fetchMock.mockResolvedValue(res(201, { data: { id: "1" } }));

    await apiFetch("/api/v1/services", { method: "POST", body: { name: "x" } });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ name: "x" }));
  });

  it("returns undefined for a 204 No Content response", async () => {
    fetchMock.mockResolvedValue(res(204, null));

    const result = await apiFetch<undefined>("/api/v1/services/1", { method: "DELETE" });

    expect(result).toBeUndefined();
  });
});
