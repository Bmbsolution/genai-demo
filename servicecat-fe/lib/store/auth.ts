import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  workspaceId: string | null;
  workspaceName: string | null;
  setSession: (tokens: { accessToken: string; refreshToken: string }) => void;
  setWorkspace: (workspace: { id: string; name: string }) => void;
  clear: () => void;
}

const EMPTY = {
  accessToken: null,
  refreshToken: null,
  workspaceId: null,
  workspaceName: null,
} as const;

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      ...EMPTY,
      setSession: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      setWorkspace: ({ id, name }) => set({ workspaceId: id, workspaceName: name }),
      clear: () => set({ ...EMPTY }),
    }),
    { name: "servicecat-auth" },
  ),
);
