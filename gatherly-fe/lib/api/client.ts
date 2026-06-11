import { useAuthStore } from "@/lib/store/auth";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8002";

/** Single-resource / simple-list success envelope returned by the API. */
export interface Data<T> {
  data: T;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(status: number, code?: string, message?: string) {
    super(message ?? `Request failed (${status})`);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  /** Attach the Bearer access token (default true). */
  auth?: boolean;
  /** Attach the X-Workspace-Id header (default true). */
  workspace?: boolean;
}

interface ApiErrorBody {
  error?: { code?: string; message?: string };
}

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

/**
 * Single in-flight refresh shared by all callers. The backend rotates the
 * refresh token on use, so concurrent 401s must not each call /refresh — the
 * second would present an already-consumed token and fail. They await this.
 */
let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, setSession, clear } = useAuthStore.getState();
  if (!refreshToken) {
    clear();
    return null;
  }
  const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    // Refresh token expired or revoked — drop the session; the guard redirects.
    clear();
    return null;
  }
  const pair = (await response.json()) as TokenPair;
  setSession({ accessToken: pair.access_token, refreshToken: pair.refresh_token });
  return pair.access_token;
}

function ensureFreshToken(): Promise<string | null> {
  refreshInFlight ??= refreshAccessToken().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

/** Typed fetch wrapper: attaches auth + workspace headers, refreshes on 401, unwraps errors. */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, workspace = true } = options;

  const send = (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (auth && token) headers.Authorization = `Bearer ${token}`;
    const { workspaceId } = useAuthStore.getState();
    if (workspace && workspaceId) headers["X-Workspace-Id"] = workspaceId;
    return fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  };

  let response = await send(useAuthStore.getState().accessToken);

  // Access token likely expired (15min TTL) — refresh once and retry.
  if (response.status === 401 && auth) {
    const refreshed = await ensureFreshToken();
    if (refreshed) response = await send(refreshed);
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorBody | null;
    throw new ApiError(response.status, payload?.error?.code, payload?.error?.message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
