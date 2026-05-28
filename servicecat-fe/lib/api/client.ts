import { useAuthStore } from "@/lib/store/auth";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

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

/** Typed fetch wrapper that attaches auth + workspace headers and unwraps errors. */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, workspace = true } = options;
  const { accessToken, workspaceId } = useAuthStore.getState();

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (workspace && workspaceId) headers["X-Workspace-Id"] = workspaceId;

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorBody | null;
    throw new ApiError(response.status, payload?.error?.code, payload?.error?.message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
